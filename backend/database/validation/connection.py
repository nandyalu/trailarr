from backend.database.models.connection import ArrType, ConnectionBase
from backend.exceptions import ItemNotFoundError
from backend.services.arr_manager.radarr import RadarrManager
from backend.services.arr_manager.sonarr import SonarrManager


def validate_connection(connection: ConnectionBase) -> str:
    """Validate the connection details and test the connection to the server
    Args:
        connection (ConnectionBase): The connection to validate
    Returns:
        str: The status message of the connection with version if valid.
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If API response is invalid
    """
    if not connection:
        raise ItemNotFoundError("No connection provided!")

    # if not connection.name:
    #     # Default to the type if not specified
    #     # connection.name = connection.type.value
    #     raise ValueError("Connection not created. No name provided!")
    # if not connection.type:
    #     # Default to radarr if not specified
    #     # connection.type = ArrType.RADARR
    #     raise ValueError("Connection not created. No type provided!")
    # if not connection.monitor:
    #     # Default to false if not specified
    #     # connection.monitor = MonitorType.MONITOR_NEW
    #     raise ValueError("Connection not created. No monitor type provided!")
    # if not connection.url:
    #     raise ValueError("Connection not created. No URL provided!")
    # if not connection.api_key:
    #     raise ValueError("Connection not created. No API key provided!")

    # Test connectivity to server
    status_message = ""
    if connection.type == ArrType.RADARR:
        arr_connection = RadarrManager(connection.url, connection.api_key)
        status_message = arr_connection.get_system_status()
    if connection.type == ArrType.SONARR:
        arr_connection = SonarrManager(connection.url, connection.api_key)
        status_message = arr_connection.get_system_status()

    return status_message
