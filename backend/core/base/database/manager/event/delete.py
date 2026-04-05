from datetime import datetime, timedelta, timezone

from sqlmodel import Session, col, select

from core.base.database.models.event import Event
from core.base.database.utils.engine import write_session


@write_session
def delete_old_events(
    days: int = 90,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete events older than specified number of days. \n
    Useful for cleanup/maintenance tasks. \n
    Args:
        days (int, Optional=90): Delete events older than this many days.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        int: Number of events deleted.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(Event).where(col(Event.created_at) < cutoff_date)
    db_events = _session.exec(statement).all()
    count = len(db_events)
    for event in db_events:
        _session.delete(event)
    _session.commit()
    return count


@write_session
def delete_by_media_id(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete all events for a specific media item. \n
    Args:
        media_id (int): The media ID whose events to delete.
        _session (Session, Optional): A session to use for the database connection.
            Default is None, in which case a new session will be created. \n
    Returns:
        int: Number of events deleted.
    """
    statement = select(Event).where(Event.media_id == media_id)
    db_events = _session.exec(statement).all()
    count = len(db_events)
    for event in db_events:
        _session.delete(event)
    _session.commit()
    return count
