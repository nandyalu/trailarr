"""Event helper functions for creating events at appropriate places in the app.

This module provides simple functions to create events for various actions.
Use these functions instead of directly calling the event manager to ensure
consistent event creation across the application.
"""

from typing import TYPE_CHECKING

from sqlmodel import Session

from app_logger import ModuleLogger
from .create import (
    create as create_event,
    create_skip_event_if_not_exists,
)
from core.base.database.models.event import (
    EventCreate,
    EventSource,
    EventType,
)

if TYPE_CHECKING:
    from core.base.database.models.media import MediaRead

logger = ModuleLogger("EventsHelper")


def track_media_added(
    media: "MediaRead",
    connection_name: str,
    source: EventSource = EventSource.SYSTEM,
    source_detail: str = "",
) -> None:
    """Track events when a new media item is added to Trailarr.

    Creates the following events in order:
    1. MEDIA_ADDED - Records the media addition
    2. YOUTUBE_ID_CHANGED - Records initial YouTube ID (if present)
    3. MONITOR_CHANGED - Records initial monitor status

    Args:
        media (MediaRead): The newly created media object.
        connection_name (str): The name of the connection/source.
        source (EventSource): The source of the event (USER or SYSTEM).
        source_detail (str): Additional details about the source.
    """
    media_id = media.id
    # 1. Create media_added event
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.MEDIA_ADDED,
            source=source,
            source_detail=source_detail,
            new_value=connection_name,
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track media_added event for [{media_id}]: {e}"
        )

    # 2. Create youtube_id_changed event if youtube_id exists
    if media.youtube_trailer_id:
        try:
            event_create = EventCreate(
                media_id=media_id,
                event_type=EventType.YOUTUBE_ID_CHANGED,
                source=source,
                source_detail=source_detail,
                old_value="",
                new_value=media.youtube_trailer_id,
            )
            create_event(event_create)
        except Exception as e:
            logger.warning(
                "Failed to track youtube_id_changed event for"
                f" [{media_id}]: {e}"
            )

    # 3. Create monitor_changed event to track initial monitor status
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.MONITOR_CHANGED,
            source=source,
            source_detail=source_detail,
            old_value="",
            new_value=str(media.monitor).lower(),
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track monitor_changed event for [{media_id}]: {e}"
        )


def track_monitor_changed(
    media_id: int,
    old_monitor: bool,
    new_monitor: bool,
    source: EventSource = EventSource.USER,
    source_detail: str = "",
) -> None:
    """Track when monitor status changes for a media item. \n
    Args:
        media_id (int): The ID of the media item.
        old_monitor (bool): The previous monitor status.
        new_monitor (bool): The new monitor status.
        source (EventSource): The source of the event (USER or SYSTEM).
        source_detail (str): Additional details about the source (e.g., task name).
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.MONITOR_CHANGED,
            source=source,
            source_detail=source_detail,
            old_value=str(old_monitor).lower(),
            new_value=str(new_monitor).lower(),
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track monitor_changed event for [{media_id}]: {e}"
        )


def track_youtube_id_changed(
    media_id: int,
    old_yt_id: str | None,
    new_yt_id: str | None,
    source: EventSource = EventSource.USER,
    source_detail: str = "",
    *,
    session: Session | None = None,
) -> None:
    """Track when YouTube trailer ID changes for a media item. \n
    Args:
        media_id (int): The ID of the media item.
        old_yt_id (str | None): The previous YouTube ID.
        new_yt_id (str | None): The new YouTube ID.
        source (EventSource): The source of the event (USER or SYSTEM).
        source_detail (str): Additional details about the source.
        session (Session | None): Optional database session to use directly.
    """
    if old_yt_id == new_yt_id:
        return
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.YOUTUBE_ID_CHANGED,
            source=source,
            source_detail=source_detail,
            old_value=old_yt_id or "",
            new_value=new_yt_id or "",
        )
        create_event(event_create, _session=session)  # type: ignore
    except Exception as e:
        logger.warning(
            f"Failed to track youtube_id_changed event for [{media_id}]: {e}"
        )


def track_trailer_downloaded(
    media_id: int,
    yt_id: str,
    source: EventSource = EventSource.USER,
    source_detail: str = "",
) -> None:
    """Track when a trailer is downloaded for a media item. \n
    Args:
        media_id (int): The ID of the media item.
        yt_id (str): The YouTube ID of the downloaded trailer.
        source (EventSource): The source of the event (USER or SYSTEM).
        source_detail (str): Additional details about the source (e.g., task name).
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.TRAILER_DOWNLOADED,
            source=source,
            source_detail=source_detail,
            new_value=yt_id,
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track trailer_downloaded event for [{media_id}]: {e}"
        )


def track_trailer_deleted(
    media_id: int,
    reason: str = "",
    source: EventSource = EventSource.USER,
    source_detail: str = "",
) -> None:
    """Track when a trailer is deleted for a media item. \n
    Args:
        media_id (int): The ID of the media item.
        reason (str): The reason for deletion (e.g., 'user_request',
            'file_not_found', 'corrupted').
        source (EventSource): The source of the event (USER or SYSTEM).
        source_detail (str): Additional details about the source (e.g., task name).
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.TRAILER_DELETED,
            source=source,
            source_detail=source_detail,
            new_value=reason,
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track trailer_deleted event for [{media_id}]: {e}"
        )


def track_trailer_detected(
    media_id: int,
    source: EventSource = EventSource.SYSTEM,
    source_detail: str = "",
) -> None:
    """Track when an existing trailer is detected on disk for a media item. \n
    This is used when scanning media folders and finding trailers that were
    added outside of Trailarr. \n
    Args:
        media_id (int): The ID of the media item.
        source (EventSource): The source of the event (USER or SYSTEM).
        source_detail (str): Additional details about the source.
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.TRAILER_DETECTED,
            source=source,
            source_detail=source_detail,
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track trailer_detected event for [{media_id}]: {e}"
        )


def track_plex_linked(
    media_id: int,
    connection_name: str,
    plex_rating_key: str,
    source: EventSource = EventSource.SYSTEM,
    source_detail: str = "",
) -> None:
    """Track when a media item is linked to a Plex connection for the first time.

    Only fires when a previously-unlinked (or differently-linked) Arr-sourced
    row is associated with a Plex item via folder-path matching.

    Args:
        media_id (int): The ID of the media item.
        connection_name (str): The name of the Plex connection.
        plex_rating_key (str): The Plex ratingKey assigned to this item.
        source (EventSource): The source of the event.
        source_detail (str): Additional details (e.g. "PlexRefresh").
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.PLEX_LINKED,
            source=source,
            source_detail=source_detail,
            new_value=connection_name,
            old_value=plex_rating_key,
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track plex_linked event for [{media_id}]: {e}"
        )


def track_plex_unlinked(
    media_id: int,
    connection_name: str,
    source: EventSource = EventSource.SYSTEM,
    source_detail: str = "",
    *,
    _session: Session | None = None,
) -> None:
    """Track when a media item loses its Plex link.

    Fires when a Plex connection is deleted (for Arr-sourced rows that had
    plex_connection_id pointing to the deleted connection) or when a media
    item is explicitly disassociated from Plex.

    Args:
        media_id (int): The ID of the media item.
        connection_name (str): The name of the Plex connection being removed.
        source (EventSource): The source of the event.
        source_detail (str): Additional details (e.g. "ConnectionDeleted").
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.PLEX_UNLINKED,
            source=source,
            source_detail=source_detail,
            old_value=connection_name,
        )
        create_event(event_create, _session=_session)  # type: ignore
    except Exception as e:
        logger.warning(
            f"Failed to track plex_unlinked event for [{media_id}]: {e}"
        )


def track_plex_scan_triggered(
    media_id: int,
    scan_path: str,
    source: EventSource = EventSource.SYSTEM,
    source_detail: str = "",
) -> None:
    """Track when a targeted Plex library scan is triggered for a media item.

    Args:
        media_id (int): The ID of the media item.
        scan_path (str): The Plex-side folder path sent to the scan endpoint.
        source (EventSource): The source of the event.
        source_detail (str): Additional details (e.g. "TrailerDownloaded").
    """
    try:
        event_create = EventCreate(
            media_id=media_id,
            event_type=EventType.PLEX_SCAN_TRIGGERED,
            source=source,
            source_detail=source_detail,
            new_value=scan_path,
        )
        create_event(event_create)
    except Exception as e:
        logger.warning(
            f"Failed to track plex_scan_triggered event for [{media_id}]: {e}"
        )


def track_download_skipped(
    media_id: int,
    skip_reason: str,
    source_detail: str = "",
) -> bool:
    """Track when a trailer download is skipped for a media item. \n
    This event is only recorded if there isn't already a recent skip event \
        or has a download event after it for the media item to avoid spamming events. \n
    Subsequent calls for the same media_id will be ignored. \n
    Args:
        media_id (int): The ID of the media item.
        skip_reason (str): The reason for skipping (e.g., 'no_folder_path',
            'folder_not_found', 'already_downloaded', 'unmonitored').
        source_detail (str): Additional details about the source (e.g., task name). \n
    Returns:
        bool: True if event was created, False if it already existed.
    """
    try:
        _, created = create_skip_event_if_not_exists(
            media_id=media_id,
            skip_reason=skip_reason,
            source_detail=source_detail,
        )
        return created
    except Exception as e:
        logger.warning(
            f"Failed to track download_skipped event for [{media_id}]: {e}"
        )
        return False
