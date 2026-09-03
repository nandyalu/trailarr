"""Shared helpers for reading and writing an event in the history."""

from sqlmodel import Session, select

from database.models.event import Event
from exceptions import ItemNotFoundError


def _get_db_item(
    id: int,
    session: Session,
) -> Event:
    """🚨This is a private method🚨 \n
    Get a event object from the database by id. \n
    Args:
        id (int): The id of the event object to get.
        session (Session): A session to use for the database connection. \n
    Returns:
        Event: The Event object if it exists.
    Raises:
        ItemNotFoundError: If the event with provided id doesn't exist.
    """
    statement = select(Event).where(Event.id == id)
    db_event = session.exec(statement).first()
    if not db_event:
        raise ItemNotFoundError("Event", id)
    return db_event
