"""Add a connection to a Radarr, Sonarr or Plex server to the database."""

from sqlmodel import Session

from . import base
from database.models.connection import ConnectionCreate, Connection
from database.engine import write_session


@write_session
def _save_validated_connection(
    connection: Connection,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Save a connection to the database \n
    Args:
        connection (Connection): The validated connection to save
        _session (Session, optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        int: The id of the saved connection
    """
    # Use the session to add the connection to the database
    _session.add(connection)
    _session.commit()
    assert connection.id is not None
    return connection.id


def create(
    connection: ConnectionCreate,
    *,
    machine_identifier: str | None = None,
) -> int:
    """Save a new connection to the database.

    The caller validates the connection against the server first. This
    function only writes the row. See `services/connections/service.py`.

    Args:
        connection (ConnectionCreate): The connection to save.
        machine_identifier (str | None): The Plex server identifier, when
            the caller read one.

    Returns:
        int: The id of the created connection.
    """
    # Convert path mappings to database objects
    # Calling Connection.model_validate(connection) will raise an error \
    # with the current implementation of PathMappingCRU
    # https://github.com/nandyalu/trailarr/issues/53
    _path_mappings = base._convert_path_mappings(connection)
    connection.path_mappings = []  # Clear path mappings from input connection
    # Create db connection object from input
    db_connection = Connection.model_validate(connection)
    # Add path mappings to database connection
    db_connection.path_mappings = _path_mappings
    db_connection.machine_identifier = machine_identifier
    # Pass the validated connection to the save function
    # to add to the database and return the id of the new connection
    return _save_validated_connection(db_connection)
