"""Event repository — pure CRUD only.

Event-tracking helpers (track_media_added, track_monitor_changed, etc.) live in
services/event_service.py because they contain business rules about when and how
events are created.
"""
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, col, desc, or_, select

from db.engine import read_session, write_session
from db.models.event import Event, EventCreate, EventRead, EventSource, EventType
from exceptions import ItemNotFoundError


def _get_or_404(event_id: int, session: Session) -> Event:
    ev = session.get(Event, event_id)
    if ev is None:
        raise ItemNotFoundError("Event", event_id)
    return ev


@write_session
def create(event_create: EventCreate, *, _session: Session = None) -> EventRead:  # type: ignore
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
    existing = _session.exec(
        select(Event).where(
            Event.media_id == event_create.media_id,
            Event.event_type == event_create.event_type,
        )
    ).first()
    if existing:
        return EventRead.model_validate(existing), False
    db_event = Event.model_validate(event_create)
    _session.add(db_event)
    _session.commit()
    _session.refresh(db_event)
    return EventRead.model_validate(db_event), True


@write_session
def create_skip_if_not_exists(
    media_id: int,
    skip_reason: str,
    source_detail: str = "",
    *,
    _session: Session = None,  # type: ignore
) -> tuple[EventRead | None, bool]:
    """Only create a DOWNLOAD_SKIPPED event if no identical recent skip or subsequent download exists."""
    stmt = (
        select(Event)
        .where(Event.media_id == media_id)
        .where(
            or_(
                Event.event_type == EventType.DOWNLOAD_SKIPPED,
                Event.event_type == EventType.TRAILER_DOWNLOADED,
            )
        )
        .order_by(desc(Event.created_at))
    )
    existing = _session.exec(stmt).first()
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


@read_session
def read(event_id: int, *, _session: Session = None) -> EventRead:  # type: ignore
    return EventRead.model_validate(_get_or_404(event_id, _session))


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
    stmt = select(Event).order_by(desc(col(Event.created_at)))
    if event_type is not None:
        stmt = stmt.where(Event.event_type == event_type)
    if event_source is not None:
        stmt = stmt.where(Event.source == event_source)
    if media_id is not None:
        stmt = stmt.where(Event.media_id == media_id)
    stmt = stmt.offset(offset).limit(limit)
    return [EventRead.model_validate(e) for e in _session.exec(stmt).all()]


@read_session
def read_by_media_id(
    media_id: int,
    limit: int = 100,
    offset: int = 0,
    *,
    _session: Session = None,  # type: ignore
) -> list[EventRead]:
    stmt = (
        select(Event)
        .where(Event.media_id == media_id)
        .order_by(desc(col(Event.created_at)))
        .offset(offset)
        .limit(limit)
    )
    return [EventRead.model_validate(e) for e in _session.exec(stmt).all()]


@read_session
def has_skip_event(media_id: int, *, _session: Session = None) -> bool:  # type: ignore
    result = _session.exec(
        select(Event.id).where(
            Event.media_id == media_id,
            Event.event_type == EventType.DOWNLOAD_SKIPPED,
        )
    ).first()
    return result is not None


@write_session
def delete_old(days: int = 90, *, _session: Session = None) -> int:  # type: ignore
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    events = _session.exec(select(Event).where(col(Event.created_at) < cutoff)).all()
    count = len(events)
    for ev in events:
        _session.delete(ev)
    _session.commit()
    return count


@write_session
def delete_by_media_id(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    events = _session.exec(select(Event).where(Event.media_id == media_id)).all()
    count = len(events)
    for ev in events:
        _session.delete(ev)
    _session.commit()
    return count
