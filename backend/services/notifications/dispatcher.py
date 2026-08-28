"""Notification dispatcher (Apprise + native Discord embeds).

Fire-and-forget by design: event creation enqueues a note (thread-safe,
never raises into the caller) and a background loop drains the queue every
BATCH_WINDOW seconds, sending ONE message per channel per window. Batching
is the flood control — bulk operations (Arr syncs, attribution passes,
library scans) can create thousands of events in seconds; a subscribed
Discord channel receives a single summarized message instead
(track-apprise-notifications.md decision D4). On top of the window, sends
are capped at MAX_SENDS_PER_MINUTE: a rate-limited cycle leaves the queue
untouched, so held notes simply merge into the next allowed batch.

Discord channels bypass Apprise's generic send: its plugin cannot place
the poster inside the embed, set fields, or a timestamped footer, so we
POST the webhook payload ourselves (decision D10). Every other service
goes through Apprise.

Channel URLs contain credentials: they must never appear in logs or error
messages here.
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app_logger import ModuleLogger
import database.manager.media as media_manager
import database.manager.notificationchannel as channel_manager

logger = ModuleLogger("Notifications")

BATCH_WINDOW_SECONDS = 10.0
MAX_LINES_PER_MESSAGE = 10
MAX_SENDS_PER_MINUTE = 5

# Public HTTPS URL — services like Discord fetch the bot avatar themselves,
# so a local file path won't work here.
_LOGO_URL = (
    "https://raw.githubusercontent.com/nandyalu/trailarr/main/"
    "frontend/src/assets/logos/trailarr-192.png"
)

_queue: deque["EventNote"] = deque()
_send_times: deque[float] = deque()  # monotonic stamps of recent sends
_dispatch_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


@dataclass
class EventNote:
    event_type: str  # EventType NAME, e.g. "TRAILER_DOWNLOADED"
    source: str  # EventSource name, e.g. "SYSTEM"
    media_id: int | None
    detail: str  # short human line, e.g. "Downloaded trailer: abc123"


def enqueue(
    event_type: str, source: str, media_id: int | None, detail: str = ""
) -> None:
    """Queue a note for dispatch. Called from event creation (sync, any
    thread). MUST never raise — notifications never break event tracking."""
    try:
        _queue.append(EventNote(event_type, source, media_id, detail))
    except Exception:  # pragma: no cover — deque.append shouldn't fail
        pass


def _event_label(event_type: str) -> str:
    return event_type.replace("_", " ").title()


def _media_info(media_id: int | None, cache: dict[int, object]):
    """Read the media row for a note (cached per dispatch cycle).
    Returns None for system notes and for lookups that fail."""
    if media_id is None:
        return None
    if media_id not in cache:
        try:
            cache[media_id] = media_manager.read(media_id)
        except Exception:
            cache[media_id] = None
    return cache[media_id]


def _format_batch(notes: list[EventNote], media_cache: dict[int, object]) -> str:
    """One message body for a channel's batch: up to MAX_LINES lines,
    then a summary of the rest."""
    lines: list[str] = []
    for note in notes[:MAX_LINES_PER_MESSAGE]:
        line = f"{_event_label(note.event_type)}"
        media = _media_info(note.media_id, media_cache)
        if media is not None:
            line += f": {media.title} ({media.year}) [#{media.id}]"
        elif note.media_id is not None:
            line += f": media [{note.media_id}]"
        if note.detail:
            line += f" — {note.detail}"
        if media is not None and media.youtube_trailer_id:
            line += (
                " — [YouTube](https://www.youtube.com/watch?v="
                f"{media.youtube_trailer_id})"
            )
        lines.append(line)
    overflow = len(notes) - MAX_LINES_PER_MESSAGE
    if overflow > 0:
        lines.append(f"…and {overflow} more")
    return "\n".join(lines)


def _poster_attachment(
    notes: list[EventNote], media_cache: dict[int, object]
) -> str | None:
    """Poster file to attach, only when the whole batch is about exactly
    one media item — batched summaries stay compact, no image pile-up."""
    media_ids = {n.media_id for n in notes if n.media_id is not None}
    if len(media_ids) != 1:
        return None
    media = _media_info(next(iter(media_ids)), media_cache)
    if media is None or not media.poster_path:
        return None
    from core.download.image import _url_to_fs_path

    poster = _url_to_fs_path(media.poster_path)
    return str(poster) if poster.is_file() else None


_EVENT_EMOJI = (
    ("DOWNLOAD", "⬇️"),
    ("ADDED", "➕"),
    ("DELETE", "🗑️"),
    ("CHANGE", "🔄"),
    ("RENAM", "✏️"),
    ("LINK", "🔗"),
)
_COLOR_GREEN = 0x57F287
_COLOR_RED = 0xED4245
_COLOR_BLURPLE = 0x5865F2


def _event_emoji(event_type: str) -> str:
    for key, emoji in _EVENT_EMOJI:
        if key in event_type:
            return emoji
    return "📌"


def _event_color(event_type: str) -> int:
    if "DOWNLOAD" in event_type:
        return _COLOR_GREEN
    if "DELETE" in event_type or "FAIL" in event_type:
        return _COLOR_RED
    return _COLOR_BLURPLE


def _public_poster_url(media) -> str | None:
    """Poster URL Discord can fetch itself. Arr-synced media stores the
    public remoteUrl (TMDB/TVDB) in poster_url; Plex-only media (arr_id=0)
    stores a LAN server URL Discord can't reach, so it falls back to the
    attachment-upload path."""
    url = (getattr(media, "poster_url", None) or "").strip()
    if url.startswith("http") and getattr(media, "arr_id", 0):
        return url
    return None


def _push_summary(
    notes: list[EventNote], media_cache: dict[int, object]
) -> str:
    """One-line text for the payload's top-level `content`. Mobile push
    previews only read this field — an embed-only message with an uploaded
    poster notifies as just "image received" — so every Discord payload
    carries a compact summary here too."""
    media_ids = {n.media_id for n in notes if n.media_id is not None}
    single = (
        _media_info(next(iter(media_ids)), media_cache)
        if len(media_ids) == 1
        else None
    )
    if single is not None:
        if len(notes) == 1:
            note = notes[0]
            return (
                f"{_event_emoji(note.event_type)} "
                f"{_event_label(note.event_type)}: "
                f"{single.title} ({single.year})"
            )
        # Same media, several events: title once, then the event types
        labels: list[str] = []
        for note in notes:
            label = _event_label(note.event_type)
            if label not in labels:
                labels.append(label)
        shown = labels[:3]
        if len(labels) > 3:
            shown.append(f"+{len(labels) - 3} more")
        return f"{single.title} ({single.year}): {', '.join(shown)}"
    # Mixed media: short "Title — Event" notes for the first couple
    entries: list[str] = []
    for note in notes[:2]:
        media = _media_info(note.media_id, media_cache)
        label = _event_label(note.event_type)
        entries.append(f"{media.title} — {label}" if media else label)
    remaining = len(notes) - 2
    if remaining > 0:
        entries.append(f"…and {remaining} more")
    return "; ".join(entries)


def _discord_webhook_url(url: str) -> str | None:
    """The raw webhook endpoint if this channel is a Discord webhook
    (discord:// scheme or a pasted discord.com/api/webhooks URL), else
    None. Parsed via Apprise so every URL form it accepts works here."""
    try:
        import apprise
        from apprise.plugins.discord import NotifyDiscord

        notifier = apprise.Apprise()
        if not notifier.add(url):
            return None
        server = notifier[0]
        if isinstance(server, NotifyDiscord):
            return (
                "https://discord.com/api/webhooks/"
                f"{server.webhook_id}/{server.webhook_token}"
            )
    except Exception:
        return None
    return None


def _discord_payload(
    notes: list[EventNote], media_cache: dict[int, object]
) -> tuple[dict, str | None]:
    """Native Discord embed for a batch. Single-media batches lead with
    the media title, Media/Trailer fields, and the poster inside the
    embed (uploaded, referenced as attachment://); multi-media batches
    stay a compact text summary."""
    media_ids = {n.media_id for n in notes if n.media_id is not None}
    single = (
        _media_info(next(iter(media_ids)), media_cache)
        if len(media_ids) == 1
        else None
    )
    embed: dict = {
        "color": _event_color(notes[0].event_type),
        "footer": {"text": "Trailarr", "icon_url": _LOGO_URL},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    poster: str | None = None
    if single is not None:
        embed["title"] = f"{single.title} ({single.year})"
        lines = [
            f"{_event_emoji(n.event_type)} {_event_label(n.event_type)}"
            + (f" — {n.detail}" if n.detail else "")
            for n in notes[:MAX_LINES_PER_MESSAGE]
        ]
        overflow = len(notes) - MAX_LINES_PER_MESSAGE
        if overflow > 0:
            lines.append(f"…and {overflow} more")
        embed["description"] = "\n".join(lines)
        fields = [{"name": "Media", "value": f"#{single.id}", "inline": True}]
        if single.youtube_trailer_id:
            fields.append(
                {
                    "name": "Trailer",
                    "value": (
                        "[▶ YouTube](https://www.youtube.com/watch?v="
                        f"{single.youtube_trailer_id})"
                    ),
                    "inline": True,
                }
            )
        embed["fields"] = fields
        public_poster = _public_poster_url(single)
        if public_poster:
            embed["image"] = {"url": public_poster}
        else:
            poster = _poster_attachment(notes, media_cache)
            if poster:
                embed["image"] = {
                    "url": f"attachment://poster{Path(poster).suffix}"
                }
    else:
        count = len(notes)
        embed["title"] = f"Trailarr — {count} update{'s' if count != 1 else ''}"
        embed["description"] = _format_batch(notes, media_cache)
    payload = {
        "username": "Trailarr",
        "avatar_url": _LOGO_URL,
        "embeds": [embed],
    }
    # Push previews read `content` first and fall back to the embed's
    # title/description — unless the message carries an attachment, which
    # previews as "image received". So a content line is added only where
    # the embed fallback isn't enough: attachment uploads, and multi-media
    # batches whose embed title alone ("Trailarr — N updates") says little.
    if poster or single is None:
        payload["content"] = _push_summary(notes, media_cache)
    return payload, poster


def _post_discord_sync(
    webhook_url: str, payload: dict, poster_path: str | None = None
) -> bool:
    """Blocking Discord webhook POST — run via asyncio.to_thread. The
    poster is uploaded multipart so the embed's attachment:// reference
    resolves regardless of whether the poster's source URL is public."""
    import requests

    if poster_path:
        with open(poster_path, "rb") as fh:
            name = f"poster{Path(poster_path).suffix}"
            response = requests.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files={"files[0]": (name, fh)},
                timeout=30,
            )
    else:
        response = requests.post(webhook_url, json=payload, timeout=30)
    return response.status_code < 300


def _send_sync(
    url: str, title: str, body: str, attach: str | None = None
) -> bool:
    """Blocking Apprise send — run via asyncio.to_thread. Services without
    attachment support simply send the text message."""
    import apprise

    # Brand outgoing messages as Trailarr (bot avatar/icon on Discord,
    # Slack, Telegram, …) instead of Apprise's default logo.
    asset = apprise.AppriseAsset(
        app_id="Trailarr",
        app_desc="Trailarr",
        app_url="https://nandyalu.github.io/trailarr/",
        image_url_mask=_LOGO_URL,
        image_url_logo=_LOGO_URL,
    )
    notifier = apprise.Apprise(asset=asset)
    if not notifier.add(url):
        return False
    # Discord only renders rich embeds (clickable [YouTube](…) links,
    # colored strip) in markdown mode, which otherwise needs an explicit
    # ?format=markdown on the URL — default it so users don't have to.
    from apprise.plugins.discord import NotifyDiscord

    for server in notifier:
        if isinstance(server, NotifyDiscord):
            server.notify_format = apprise.NotifyFormat.MARKDOWN
    return bool(
        notifier.notify(
            title=title, body=body, body_format="markdown", attach=attach
        )
    )


async def send_test(channel_id: int) -> bool:
    """Send an immediate test message to one channel (user-triggered)."""
    url = channel_manager.get_url(channel_id)
    return await asyncio.to_thread(
        _send_sync,
        url,
        "Trailarr",
        "Test notification — this channel is set up correctly! 🎬",
    )


def _rate_limited() -> bool:
    """True when MAX_SENDS_PER_MINUTE cycles already sent in the last
    minute. Expired stamps are pruned here."""
    now = time.monotonic()
    while _send_times and now - _send_times[0] >= 60.0:
        _send_times.popleft()
    return len(_send_times) >= MAX_SENDS_PER_MINUTE


async def _dispatch_pending(force: bool = False) -> None:
    """Drain the queue and send one batched message per subscribed channel.

    A rate-limited cycle returns with the queue untouched — those notes
    merge into the next allowed batch. `force` (shutdown flush) bypasses
    the cap so pending notes are never dropped."""
    if not _queue:
        return
    if not force and _rate_limited():
        return
    notes: list[EventNote] = []
    while _queue:
        notes.append(_queue.popleft())

    # Group notes per channel via subscriptions
    per_channel: dict[int, tuple[str, list[EventNote]]] = {}
    for note in notes:
        try:
            subscribed = channel_manager.subscribed_channels(
                note.event_type, is_user_event=(note.source == "USER")
            )
        except Exception as e:
            logger.warning(f"Failed to resolve channel subscriptions: {e}")
            return
        for channel_id, url in subscribed:
            per_channel.setdefault(channel_id, (url, []))[1].append(note)

    if per_channel:
        _send_times.append(time.monotonic())
    media_cache: dict[int, object] = {}
    for channel_id, (url, channel_notes) in per_channel.items():
        webhook = _discord_webhook_url(url)
        try:
            if webhook:
                payload, poster = _discord_payload(channel_notes, media_cache)
                ok = await asyncio.to_thread(
                    _post_discord_sync, webhook, payload, poster
                )
            else:
                body = _format_batch(channel_notes, media_cache)
                attach = _poster_attachment(channel_notes, media_cache)
                ok = await asyncio.to_thread(
                    _send_sync, url, "Trailarr", body, attach
                )
            if not ok:
                logger.warning(
                    f"Notification send failed for channel [{channel_id}]"
                    " — check its Apprise URL (Test button in Settings)."
                )
        except Exception as e:
            logger.warning(
                f"Notification send error for channel [{channel_id}]:"
                f" {type(e).__name__}"
            )


async def _dispatch_loop() -> None:
    assert _stop_event is not None
    while not _stop_event.is_set():
        try:
            await asyncio.wait_for(
                _stop_event.wait(), timeout=BATCH_WINDOW_SECONDS
            )
        except asyncio.TimeoutError:
            pass
        try:
            await _dispatch_pending()
        except Exception as e:  # never let the loop die
            logger.warning(f"Notification dispatch cycle failed: {e}")


def start() -> None:
    """Start the dispatcher loop (called from the app lifespan, which is
    already running inside the event loop at this point)."""
    global _dispatch_task, _stop_event
    if _dispatch_task is not None:
        return
    _stop_event = asyncio.Event()
    _dispatch_task = asyncio.get_running_loop().create_task(_dispatch_loop())
    logger.debug("Notification dispatcher started")


async def stop() -> None:
    """Stop the loop and flush pending notes (app shutdown).

    The loop itself dispatches once more before exiting in the common case
    (woken by the stop event mid-wait), but that's a timing detail, not a
    guarantee — e.g. if stop() races ahead of the task's very first
    iteration, the loop's `while` condition is already false and it never
    dispatches at all. Explicitly flushing here after the task has stopped
    makes the "pending notes are flushed on shutdown" contract hold
    regardless of that timing.
    """
    global _dispatch_task, _stop_event
    if _dispatch_task is None or _stop_event is None:
        return
    _stop_event.set()
    try:
        await asyncio.wait_for(_dispatch_task, timeout=10)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        _dispatch_task.cancel()
    _dispatch_task = None
    _stop_event = None
    try:
        await _dispatch_pending(force=True)
    except Exception as e:  # best-effort — never block shutdown
        logger.warning(f"Final notification flush failed: {type(e).__name__}")
    logger.debug("Notification dispatcher stopped")
