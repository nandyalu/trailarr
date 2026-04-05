from sqlmodel import Session, desc, select, or_

from core.base.database.models.event import (
    Event,
    EventCreate,
    EventRead,
    EventSource,
    EventType,
)
from core.base.database.utils.engine import write_session


@write_session
def create(
    event_create: EventCreate,
    *,
    _session: Session = None,  # type: ignore
) -> EventRead:
    """Create a new event in the database. \n
    Args:
        event_create (EventCreate): The event data to create.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        EventRead: The created event data.
    """
    db_event = Event.model_validate(event_create)
    _session.add(db_event)
    _session.commit()
    _session.refresh(db_event)
    return EventRead.model_validate(db_event)


@write_session
def create_if_not_exists(
    event_create: EventCreate,
    *,
    _session: Session = None,  # type: ignore
) -> tuple[EventRead, bool]:
    """Create a new event in the database only if one doesn't already exist \
        for the same media_id and event_type. \n
    Useful for skip events where we only want to record once per media item. \n
    Args:
        event_create (EventCreate): The event data to create.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        tuple[EventRead, bool]: Tuple of the event and a boolean indicating \
            if it was newly created (True) or already existed (False).
    """
    statement = select(Event).where(
        Event.media_id == event_create.media_id,
        Event.event_type == event_create.event_type,
    )
    db_event = _session.exec(statement).first()
    if db_event:
        return EventRead.model_validate(db_event), False

    db_event = Event.model_validate(event_create)
    _session.add(db_event)
    _session.commit()
    _session.refresh(db_event)
    return EventRead.model_validate(db_event), True


@write_session
def create_skip_event_if_not_exists(
    media_id: int,
    skip_reason: str,
    source_detail: str = "",
    *,
    _session: Session = None,  # type: ignore
) -> tuple[EventRead | None, bool]:
    """Track when a trailer download is skipped for a media item. \n
    This event is only recorded if there isn't already a recent skip event (same reason) \
        or has a download event after it for the media item to avoid spamming events. \n
    Subsequent calls for the same media_id will be ignored. \n
    Args:
        media_id (int): The media ID to create the skip event for.
        skip_reason (str): The reason the download was skipped.
        source_detail (str, Optional): The source detail (e.g., task name).
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        tuple[EventRead | None, bool]: Tuple of the event (None if already exists) \
            and a boolean indicating if it was created.
    """
    statement = select(Event).where(Event.media_id == media_id)
    statement = statement.where(
        or_(
            Event.event_type == EventType.DOWNLOAD_SKIPPED,
            Event.event_type == EventType.TRAILER_DOWNLOADED,
        )
    )
    statement = statement.order_by(desc(Event.created_at))

    existing = _session.exec(statement).first()
    if existing and existing.event_type == EventType.DOWNLOAD_SKIPPED:
        if existing.new_value == skip_reason:
            return None, False

    event_create = EventCreate(
        media_id=media_id,
        event_type=EventType.DOWNLOAD_SKIPPED,
        source=EventSource.SYSTEM,
        source_detail=source_detail,
        new_value=skip_reason,
    )
    db_event = Event.model_validate(event_create)
    _session.add(db_event)
    _session.commit()
    _session.refresh(db_event)
    return EventRead.model_validate(db_event), True
