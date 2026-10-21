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
import database.manager.mediavideo as video_manager
from database.models.mediavideo import MediaVideoRead
from database.models.event import EventSource
from database.models.video_type import (
    DEFAULT_VIDEO_TYPE,
    is_trailer_type,
    normalize_video_type,
)
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
            f"'{media.title}' has no folder path.",
            ok=False,
        )
    # Use download records as the authoritative source for trailer files.
    # Only the trailers: a featurette or a clip is deleted from its own
    # row on the media details page (Phase 9). The action keeps its name.
    downloads = download_manager.read_by_media_id(media_id)
    live = [
        d
        for d in downloads
        if d.file_exists and is_trailer_type(d.video_type)
    ]
    if not live:
        return ActionResult(
            f"Trailarr found no trailer files for '{media.title}'.",
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

    msg = f"Trailarr deleted the trailer for '{media.title}'."
    logger.info(msg)
    return ActionResult(msg, ok=True, reload="media")


def list_videos(media_id: int) -> list[MediaVideoRead]:
    """Every video Trailarr knows for a media item, in resolution order.

    Args:
        media_id (int): The media item.

    Returns:
        list[MediaVideoRead]: The videos, the first one being the one a
            download would use.
    """
    return video_manager.read_for_media(media_id)


def first_video_id(
    media_id: int, video_type: str = DEFAULT_VIDEO_TYPE
) -> str | None:
    """The video that a download of the type would take now, if any.

    Args:
        media_id (int): The media item.
        video_type (str): The type of video to look at.

    Returns:
        str | None: The YouTube id of the first known video of that type,
            or None when there is none.
    """
    try:
        candidates = video_manager.read_candidates(
            media_id, video_type=video_type
        )
    except Exception as e:
        logger.warning(
            f"Trailarr could not read the known videos: {e}",
            **logger.media(media_id),
        )
        return None
    return candidates[0].video_id if candidates else None


def add_video(
    media_id: int,
    video_id: str,
    language: str | None = None,
    video_type: str = DEFAULT_VIDEO_TYPE,
) -> MediaVideoRead:
    """Add a video that the user chose.

    The row goes into the known videos as a USER row, which the resolver
    puts before every other source and no task ever removes. The change is
    recorded as a YOUTUBE_ID_CHANGED event when the video that a download
    of this type would take changes. Phase 9 dropped the legacy
    `media.youtube_trailer_id` column (H9), so this is the only path.

    Args:
        media_id (int): The media item.
        video_id (str): The YouTube id. The caller reads it out of a URL.
        language (str | None): The language the video is in, so that a
            profile asking for that language can use it. None means the
            video suits a profile that takes any language.
        video_type (str): What the video is: a trailer by default, or
            another type, so that a profile of that type can use it.

    Returns:
        MediaVideoRead: The row that was created, or the row that another
            source made for the same video and that now belongs to the user.
    """
    video_type = normalize_video_type(video_type)
    # The video that a download of this type took before the change, so
    # the event says what the user's choice replaced.
    old_yt_id = first_video_id(media_id, video_type)

    row = video_manager.add_user_video(
        media_id, video_id, language=language, video_type=video_type
    )
    event_manager.track_youtube_id_changed(
        media_id=media_id,
        old_yt_id=old_yt_id,
        new_yt_id=video_id,
        source=EventSource.USER,
        source_detail="UserInput",
    )

    logger.info(
        f"Trailarr added the video '{video_id}' that you chose.",
        **logger.media(media_id),
    )
    return row


def remove_video(media_id: int, video_id: str) -> bool:
    """Remove one known video from a media item.

    Args:
        media_id (int): The media item.
        video_id (str): The YouTube id to remove.

    Returns:
        bool: False when the media item did not have that video.
    """
    removed = video_manager.delete_video(media_id, video_id)
    if removed:
        logger.info(
            f"Trailarr removed the video '{video_id}'.",
            **logger.media(media_id),
        )
    return removed


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
    return f"Trailarr set {len(media_ids)} media items to {state}."


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
    logger.info(msg, **logger.media(media_id))

    # Track monitor_changed event if status actually changed
    if is_success:
        event_manager.track_monitor_changed(
            media_id=media_id,
            old_monitor=old_monitor,
            new_monitor=monitor,
            source=EventSource.USER,
        )

    return ActionResult(msg, ok=is_success, reload="media")
