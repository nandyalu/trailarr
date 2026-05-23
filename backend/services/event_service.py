"""Event tracking helpers — thin wrappers that call db.repos.event.

Business rules (when to fire which event, with what values) live here.
db.repos.event contains only pure DB CRUD.
"""
from app_logger import ModuleLogger
from db.models.event import EventCreate, EventSource, EventType
import db.repos.event as event_repo

logger = ModuleLogger("EventService")


def _fire(event_create: EventCreate) -> None:
    try:
        event_repo.create(event_create)
    except Exception as e:
        logger.warning(f"Failed to fire event {event_create.event_type} for [{event_create.media_id}]: {e}")


def track_media_added(
    media,  # MediaRead
    connection_name: str,
    source: EventSource = EventSource.SYSTEM,
    source_detail: str = "",
) -> None:
    media_id = media.id
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.MEDIA_ADDED,
        source=source, source_detail=source_detail, new_value=connection_name,
    ))
    if media.youtube_trailer_id:
        _fire(EventCreate(
            media_id=media_id, event_type=EventType.YOUTUBE_ID_CHANGED,
            source=source, source_detail=source_detail,
            old_value="", new_value=media.youtube_trailer_id,
        ))
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.MONITOR_CHANGED,
        source=source, source_detail=source_detail,
        old_value="", new_value=str(media.monitor).lower(),
    ))


def track_monitor_changed(
    media_id: int,
    old_monitor: bool,
    new_monitor: bool,
    source: EventSource = EventSource.USER,
    source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.MONITOR_CHANGED,
        source=source, source_detail=source_detail,
        old_value=str(old_monitor).lower(), new_value=str(new_monitor).lower(),
    ))


def track_youtube_id_changed(
    media_id: int,
    old_yt_id: str | None,
    new_yt_id: str | None,
    source: EventSource = EventSource.USER,
    source_detail: str = "",
) -> None:
    if old_yt_id == new_yt_id:
        return
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.YOUTUBE_ID_CHANGED,
        source=source, source_detail=source_detail,
        old_value=old_yt_id or "", new_value=new_yt_id or "",
    ))


def track_trailer_downloaded(
    media_id: int, yt_id: str,
    source: EventSource = EventSource.USER, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.TRAILER_DOWNLOADED,
        source=source, source_detail=source_detail, new_value=yt_id,
    ))


def track_trailer_deleted(
    media_id: int, reason: str = "",
    source: EventSource = EventSource.USER, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.TRAILER_DELETED,
        source=source, source_detail=source_detail, new_value=reason,
    ))


def track_trailer_detected(
    media_id: int,
    source: EventSource = EventSource.SYSTEM, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.TRAILER_DETECTED,
        source=source, source_detail=source_detail,
    ))


def track_plex_linked(
    media_id: int, connection_name: str, plex_rating_key: str,
    source: EventSource = EventSource.SYSTEM, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.PLEX_LINKED,
        source=source, source_detail=source_detail,
        new_value=connection_name, old_value=plex_rating_key,
    ))


def track_plex_unlinked(
    media_id: int, connection_name: str,
    source: EventSource = EventSource.SYSTEM, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.PLEX_UNLINKED,
        source=source, source_detail=source_detail, old_value=connection_name,
    ))


def track_plex_scan_triggered(
    media_id: int, scan_path: str,
    source: EventSource = EventSource.SYSTEM, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.PLEX_SCAN_TRIGGERED,
        source=source, source_detail=source_detail, new_value=scan_path,
    ))


def track_arr_linked(
    media_id: int, connection_name: str,
    source: EventSource = EventSource.SYSTEM, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.ARR_LINKED,
        source=source, source_detail=source_detail, new_value=connection_name,
    ))


def track_arr_unlinked(
    media_id: int, connection_name: str,
    source: EventSource = EventSource.SYSTEM, source_detail: str = "",
) -> None:
    _fire(EventCreate(
        media_id=media_id, event_type=EventType.ARR_UNLINKED,
        source=source, source_detail=source_detail, old_value=connection_name,
    ))


def track_download_skipped(
    media_id: int, skip_reason: str, source_detail: str = ""
) -> bool:
    try:
        _, created = event_repo.create_skip_if_not_exists(
            media_id=media_id, skip_reason=skip_reason, source_detail=source_detail
        )
        return created
    except Exception as e:
        logger.warning(f"Failed to track download_skipped for [{media_id}]: {e}")
        return False
