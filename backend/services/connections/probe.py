"""Network probes against the server behind a connection.

These functions read the url, api_key and arr_type of a connection and then
talk to Radarr, Sonarr or Plex over the network. They touch no database.

They lived in `database/manager/connection/` until Phase 7 Stage B. The
database layer must not do network I/O: a slow or unreachable server then
blocks a database call, and in the update path it held a write transaction
open for the length of an HTTP request.
"""

from database.models.connection import ArrType, ConnectionBase
from exceptions import ItemNotFoundError
from services.connections.arr.radarr.api_manager import RadarrManager
from services.connections.arr.sonarr.api_manager import SonarrManager
from services.connections.plex.api_manager import PlexAPI

# Identifier sent to Plex when the connection has no id of its own yet.
DEFAULT_PLEX_IDENTIFIER = "trailarr_1234"


async def validate_connection(connection: ConnectionBase) -> str:
    """Validate the connection details and test the connection to the server \n
    Args:
        connection (ConnectionBase): The connection to validate \n
    Returns:
        str: The status message of the connection with version if valid. \n
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If API response is invalid
        ItemNotFoundError: If a connection object is not provided as input
    """
    if not connection:
        raise ItemNotFoundError("Connection", 0)

    # Test connectivity to server
    status_message = ""
    if connection.arr_type == ArrType.RADARR:
        arr_connection = RadarrManager(connection.url, connection.api_key)
        status_message = await arr_connection.get_system_status()
    elif connection.arr_type == ArrType.SONARR:
        arr_connection = SonarrManager(connection.url, connection.api_key)
        status_message = await arr_connection.get_system_status()
    elif connection.arr_type == ArrType.PLEX:
        plex_connection = PlexAPI(
            connection.url,
            connection.api_key,
            identifier=DEFAULT_PLEX_IDENTIFIER,
        )
        status_message = await plex_connection.get_system_status()

    return status_message


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
    elif connection.arr_type == ArrType.SONARR:
        arr_connection = SonarrManager(connection.url, connection.api_key)
        root_folders = await arr_connection.get_rootfolders()
    elif connection.arr_type == ArrType.PLEX:
        plex_connection = PlexAPI(
            connection.url,
            connection.api_key,
            identifier=DEFAULT_PLEX_IDENTIFIER,
        )
        root_folders = await plex_connection.get_library_folders()

    return root_folders


async def get_machine_identifier(
    connection: ConnectionBase,
    identifier: str = DEFAULT_PLEX_IDENTIFIER,
) -> str:
    """Read the machine identifier of a Plex server.

    Trailarr stores this value to recognize the same server later.

    Args:
        connection (ConnectionBase): The Plex connection to ask.
        identifier (str): The client identifier to send to Plex.

    Returns:
        str: The machine identifier of the server.
    """
    plex_api = PlexAPI(
        connection.url, connection.api_key, identifier=identifier
    )
    return await plex_api.get_machine_identifier()
