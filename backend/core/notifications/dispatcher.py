"""Notification dispatcher (Apprise + native Discord embeds).

Fire-and-forget by design: event creation enqueues a note (thread-safe,
never raises into the caller) and a background loop drains the queue every
BATCH_WINDOW seconds, sending ONE message per channel per window. Batching
is the flood control — bulk operations (Arr syncs, attribution passes,
library scans) can create thousands of events in seconds; a subscribed
Discord channel receives a single summarized message instead
(track-apprise-notifications.md decision D4).

Discord channels bypass Apprise's generic send: its plugin cannot place
the poster inside the embed, set fields, or a timestamped footer, so we
POST the webhook payload ourselves (decision D10). Every other service
goes through Apprise.

Channel URLs contain credentials: they must never appear in logs or error
messages here.
"""

import asyncio
import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app_logger import ModuleLogger
import core.base.database.manager.media as media_manager
import core.base.database.manager.notificationchannel as channel_manager

logger = ModuleLogger("Notifications")

BATCH_WINDOW_SECONDS = 30.0
MAX_LINES_PER_MESSAGE = 10

# Public HTTPS URL — services like Discord fetch the bot avatar themselves,
# so a local file path won't work here.
_LOGO_URL = (
    "https://raw.githubusercontent.com/nandyalu/trailarr/main/"
    "frontend/src/assets/logos/trailarr-192.png"
)

_queue: deque["EventNote"] = deque()
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


async def _dispatch_pending() -> None:
    """Drain the queue and send one batched message per subscribed channel."""
    if not _queue:
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
        await _dispatch_pending()
    except Exception as e:  # best-effort — never block shutdown
        logger.warning(f"Final notification flush failed: {type(e).__name__}")
    logger.debug("Notification dispatcher stopped")
