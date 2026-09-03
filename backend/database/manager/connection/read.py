"""Read a connection to a Radarr, Sonarr or Plex server from the database."""

from sqlmodel import Session, select

from . import base
from database.models.connection import (
    ConnectionRead,
    Connection,
)
from database.engine import read_session


@read_session
def read(
    connection_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> ConnectionRead:
    """Read a connection from the database \n
    Args:
        connection_id (int): The id of the connection to read
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        ConnectionRead: The read-only connection object \n
    Raises:
        ItemNotFoundError: If a connection with provided id does not exist
    """
    connection = base._get_db_item(connection_id, _session=_session)
    # Convert the connection to a ConnectionRead object
    connection_read = ConnectionRead.model_validate(connection)
    return connection_read


@read_session
def read_all(
    *,
    _session: Session = None,  # type: ignore
) -> list[ConnectionRead]:
    """Read all connections from the database \n
    Args:
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        list[ConnectionRead]: A list of read-only connection objects
    """
    statement = select(Connection)
    connections = _session.exec(statement).all()
    return [
        ConnectionRead.model_validate(connection) for connection in connections
    ]


