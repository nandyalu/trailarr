from sqlmodel import Session, select

from . import base
from core.radarr.api_manager import RadarrManager
from core.sonarr.api_manager import SonarrManager
from exceptions import ItemNotFoundError
from core.base.database.models.connection import (
    ArrType,
    ConnectionBase,
    ConnectionRead,
    Connection,
)
from core.base.database.utils.engine import manage_session


@manage_session
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


@manage_session
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


async def get_rootfolders(connection: ConnectionBase) -> list[str]:
    """Get the root folders of a connection \n
    Args:
        connection (ConnectionBase): The connection to get root folders from \n
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If the API response is invalid \n
    Returns:
        list[str]: The list of root folders
    """
    if not connection:
        raise ItemNotFoundError("Connection", 0)

    root_folders: list[str] = []
    if connection.arr_type == ArrType.RADARR:
        arr_connection = RadarrManager(connection.url, connection.api_key)
        root_folders = await arr_connection.get_rootfolders()
    if connection.arr_type == ArrType.SONARR:
        arr_connection = SonarrManager(connection.url, connection.api_key)
        root_folders = await arr_connection.get_rootfolders()

    return root_folders
