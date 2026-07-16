"""Apprise notification dispatcher.

Fire-and-forget by design: event creation enqueues a note (thread-safe,
never raises into the caller) and a background loop drains the queue every
BATCH_WINDOW seconds, sending ONE message per channel per window. Batching
is the flood control — bulk operations (Arr syncs, attribution passes,
library scans) can create thousands of events in seconds; a subscribed
Discord channel receives a single summarized message instead
(track-apprise-notifications.md decision D4).

Apprise URLs contain credentials: they must never appear in logs or error
messages here.
"""

import asyncio
from collections import deque
from dataclasses import dataclass

from app_logger import ModuleLogger
import core.base.database.manager.media as media_manager
import core.base.database.manager.notificationchannel as channel_manager

logger = ModuleLogger("Notifications")

BATCH_WINDOW_SECONDS = 30.0
MAX_LINES_PER_MESSAGE = 10

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


def _media_title(media_id: int | None, cache: dict[int, str]) -> str:
    if media_id is None:
        return ""
    if media_id not in cache:
        try:
            cache[media_id] = media_manager.read(media_id).title
        except Exception:
            cache[media_id] = f"media [{media_id}]"
    return cache[media_id]


def _format_batch(notes: list[EventNote]) -> str:
    """One message body for a channel's batch: up to MAX_LINES lines,
    then a summary of the rest."""
    title_cache: dict[int, str] = {}
    lines: list[str] = []
    for note in notes[:MAX_LINES_PER_MESSAGE]:
        title = _media_title(note.media_id, title_cache)
        line = f"{_event_label(note.event_type)}"
        if title:
            line += f": {title}"
        if note.detail:
            line += f" — {note.detail}"
        lines.append(line)
    overflow = len(notes) - MAX_LINES_PER_MESSAGE
    if overflow > 0:
        lines.append(f"…and {overflow} more")
    return "\n".join(lines)


def _send_sync(url: str, title: str, body: str) -> bool:
    """Blocking Apprise send — run via asyncio.to_thread."""
    import apprise

    notifier = apprise.Apprise()
    if not notifier.add(url):
        return False
    return bool(notifier.notify(title=title, body=body))


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

    for channel_id, (url, channel_notes) in per_channel.items():
        body = _format_batch(channel_notes)
        try:
            ok = await asyncio.to_thread(_send_sync, url, "Trailarr", body)
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
