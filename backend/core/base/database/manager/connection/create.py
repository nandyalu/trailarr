from sqlmodel import Session

from . import base
from core.base.database.models.connection import ConnectionCreate, Connection
from core.base.database.utils.engine import manage_session


@manage_session
async def create(
    connection: ConnectionCreate,
    *,
    _session: Session = None,  # type: ignore
) -> tuple[str, int]:
    """Create a new connection in the database \n
    Args:
        connection (Connection): The connection to create
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        tuple(str, int): The status message of the connection with version if created. \
            and the id of the created connection. \n
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If API response is invalid
        ValidationError: If the connection is invalid
    """
    # Validate the connection details, will raise an error if invalid
    status = await base.validate_connection(connection)
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
    # Use the session to add the connection to the database
    _session.add(db_connection)
    _session.commit()
    assert db_connection.id is not None
    return status, db_connection.id
