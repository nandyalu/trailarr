"""Actions the user takes on a media item.

Each function does the work and reports what happened. None of them
broadcast: the websocket belongs to the api layer, so the handler reads the
result and sends the message.

Phase 7 Stage B moved this out of api/v1/media.py, where the work, the
websocket messages and the HTTP status mapping were interleaved.
"""

from dataclasses import dataclass

from app_logger import ModuleLogger
import database.manager.download as download_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.event import EventSource
from services.files.files_handler import FilesHandler

logger = ModuleLogger("MediaService")


@dataclass
class ActionResult:
    """What happened, and how the user should be told.

    Attributes:
        message: The line to show the user.
        ok: True when the action did what was asked.
        reload: The part of the UI to refresh, or None to refresh nothing.
    """

    message: str
    ok: bool
    reload: str | None = None


async def delete_trailers(media_id: int) -> ActionResult:
    """Delete every trailer file of one media item.

    The download rows are the record of which files are trailers, so they
    decide what gets deleted, and each one is marked deleted afterwards.
    One event is tracked for the media item, not one per file.

    Args:
        media_id (int): The media item to clear.

    Returns:
        ActionResult: What was deleted, or why nothing was.
    """
    media = media_manager.read(media_id)
    if not media.folder_path:
        return ActionResult(
            f"Media '{media.title}' [{media.id}] has no folder path",
            ok=False,
        )
    # Use download records as the authoritative source for trailer files
    downloads = download_manager.read_by_media_id(media_id)
    live = [d for d in downloads if d.file_exists]
    if not live:
        return ActionResult(
            f"No trailer files found for media '{media.title}' [{media.id}]",
            ok=False,
        )

    for d in live:
        await FilesHandler.delete_file(d.path)
        download_manager.mark_as_deleted(d.id)

    # Track trailer_deleted event (once per media item, not per file)
    event_manager.track_trailer_deleted(
        media_id=media_id,
        reason="user_request",
        source=EventSource.USER,
    )

    msg = f"Trailer for media '{media.title}' [{media.id}] has been deleted."
    logger.info(msg)
    return ActionResult(msg, ok=True, reload="media")


def set_youtube_id(media_id: int, yt_id: str) -> str:
    """Store the YouTube id a user picked for a media item.

    The caller checks the id first. An event is tracked only when the value
    really changes.

    Args:
        media_id (int): The media item to change.
        yt_id (str): The YouTube id to store. An empty string clears it.

    Returns:
        str: A line that says what changed.
    """
    # Get old YouTube ID for event tracking
    media = media_manager.read(media_id)
    old_yt_id = media.youtube_trailer_id

    media_manager.update_ytid(media_id, yt_id)

    # Track youtube_id_changed event if ID actually changed
    if old_yt_id != yt_id:
        event_manager.track_youtube_id_changed(
            media_id=media_id,
            old_yt_id=old_yt_id,
            new_yt_id=yt_id,
            source=EventSource.USER,
            source_detail="UserInput",
        )

    msg = f"YouTube ID for media with ID: {media_id} has been updated."
    logger.info(msg)
    return msg


def set_monitoring_bulk(media_ids: list[int], monitor: bool) -> str:
    """Turn monitoring on or off for several media items at once.

    No event is tracked here. The single-item path tracks one because it
    knows the value before the change; a bulk update does not read each row
    first, and doing so would cost one query per item.

    Args:
        media_ids (list[int]): The media items to change.
        monitor (bool): True to monitor them, False to stop.

    Returns:
        str: A line that says how many changed.
    """
    media_manager.update_monitoring_bulk(media_ids, monitor)
    state = "monitored" if monitor else "unmonitored"
    return f"{len(media_ids)} Media are now {state}"


def set_monitoring(media_id: int, monitor: bool) -> ActionResult:
    """Turn monitoring on or off for one media item.

    An event is tracked only when the flag really changes.

    Args:
        media_id (int): The media item to change.
        monitor (bool): True to monitor it, False to stop.

    Returns:
        ActionResult: The message from the manager, and whether it worked.
    """
    # Get old monitor status for event tracking
    media = media_manager.read(media_id)
    old_monitor = media.monitor

    msg, is_success = media_manager.update_monitoring(media_id, monitor)
    logger.info(msg)

    # Track monitor_changed event if status actually changed
    if is_success:
        event_manager.track_monitor_changed(
            media_id=media_id,
            old_monitor=old_monitor,
            new_monitor=monitor,
            source=EventSource.USER,
        )

    return ActionResult(msg, ok=is_success, reload="media")
