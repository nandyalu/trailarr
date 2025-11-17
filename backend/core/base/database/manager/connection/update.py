from sqlmodel import Session

from . import base
from core.base.database.models.connection import (
    ConnectionRead,
    ConnectionUpdate,
)
from core.base.database.utils.engine import manage_session


@manage_session
async def update(
    connection_id: int,
    connection_update: ConnectionUpdate,
    *,
    _session: Session = None,  # type: ignore
) -> ConnectionRead:
    """Update an existing connection in the database\n
    Args:
        connection_id (int): The id of the connection to update
        connection (Connection): The connection to update
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        ConnectionRead: The updated read-only connection object. \n
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If API response is invalid
        ItemNotFoundError: If a connection with provided id does not exist
    """
    # Get the connection from the database
    db_connection = base._get_db_item(connection_id, _session=_session)
    # Update the connection details from input
    connection_update_data = connection_update.model_dump(exclude_unset=True)
    db_connection.sqlmodel_update(connection_update_data)
    # Update the path mappings
    base._update_path_mappings(
        db_connection, connection_update, _session=_session
    )
    # Validate the connection details
    await base.validate_connection(db_connection)
    # Commit the changes to the database
    _session.add(db_connection)
    _session.commit()
    return ConnectionRead.model_validate(db_connection)
