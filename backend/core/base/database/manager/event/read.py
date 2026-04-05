from sqlmodel import Session, col, desc, select

from . import base
from core.base.database.models.event import (
    Event,
    EventRead,
    EventSource,
    EventType,
)
from core.base.database.utils.engine import read_session


@read_session
def read(
    id: int,
    *,
    _session: Session = None,  # type: ignore
) -> EventRead:
    """Get an event from the database by id. \n
    Args:
        id (int): The id of the event to get.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        EventRead: The event data.
    Raises:
        ItemNotFoundError: If the event with provided id doesn't exist.
    """
    db_event = base._get_db_item(id, _session)
    return EventRead.model_validate(db_event)


@read_session
def read_all(
    limit: int = 100,
    offset: int = 0,
    event_type: EventType | None = None,
    event_source: EventSource | None = None,
    media_id: int | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> list[EventRead]:
    """Get all events from the database with optional filtering. \n
    Args:
        limit (int, Optional=100): Maximum number of events to return.
        offset (int, Optional=0): Number of events to skip.
        event_type (EventType | None, Optional=None): Filter by event type.
        event_source (EventSource | None, Optional=None): Filter by event source.
        media_id (int | None, Optional=None): Filter by media ID.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        list[EventRead]: List of event data.
    """
    statement = select(Event).order_by(desc(col(Event.created_at)))

    if event_type is not None:
        statement = statement.where(Event.event_type == event_type)
    if event_source is not None:
        statement = statement.where(Event.source == event_source)
    if media_id is not None:
        statement = statement.where(Event.media_id == media_id)

    statement = statement.offset(offset).limit(limit)
    db_events = _session.exec(statement).all()
    return [EventRead.model_validate(e) for e in db_events]


@read_session
def read_by_media_id(
    media_id: int,
    limit: int = 100,
    offset: int = 0,
    *,
    _session: Session = None,  # type: ignore
) -> list[EventRead]:
    """Get all events for a specific media item. \n
    Args:
        media_id (int): The media ID to filter by.
        limit (int, Optional=100): Maximum number of events to return.
        offset (int, Optional=0): Number of events to skip.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        list[EventRead]: List of event data for the media item.
    """
    statement = (
        select(Event)
        .where(Event.media_id == media_id)
        .order_by(desc(col(Event.created_at)))
        .offset(offset)
        .limit(limit)
    )
    db_events = _session.exec(statement).all()
    return [EventRead.model_validate(e) for e in db_events]


@read_session
def has_skip_event(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Check if a skip event already exists for a media item. \n
    Args:
        media_id (int): The media ID to check.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        bool: True if a skip event exists, False otherwise.
    """
    statement = select(Event.id).where(
        Event.media_id == media_id,
        Event.event_type == EventType.DOWNLOAD_SKIPPED,
    )
    result = _session.exec(statement).first()
    return result is not None
