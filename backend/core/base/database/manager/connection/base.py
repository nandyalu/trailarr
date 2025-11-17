from sqlmodel import Session
from core.radarr.api_manager import RadarrManager
from core.sonarr.api_manager import SonarrManager
from core.base.database.models.connection import (
    ArrType,
    Connection,
    ConnectionBase,
    ConnectionCreate,
    ConnectionUpdate,
    PathMapping,
)
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError


@manage_session
def exists(
    connection_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Check if a connection exists in the database \n
    Args:
        connection_id (int): The id of the connection to check
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        bool: True if the connection exists, False if not
    """
    connection = _session.get(Connection, connection_id)
    return bool(connection)


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
    if connection.arr_type == ArrType.SONARR:
        arr_connection = SonarrManager(connection.url, connection.api_key)
        status_message = await arr_connection.get_system_status()

    return status_message


def end_path_with_slash(path: str) -> str:
    """End a path with a slash if it does not already have one \n
    Args:
        path (str): The path to end with a slash \n
    Returns:
        str: The path with a slash at the end
    """
    # Check if path has a slash '/' (Linux/MacOS)
    if path.count("/") > 1:
        # End path with a slash if it does not have one
        if not path.endswith("/"):
            path += "/"
        return path
    # Check if path has a backslash '\' (Windows)
    # Python uses double backslashes for escape characters, so we need to check for '\\'
    # to escape the backslash itself which will be a single backslash in the path
    if path.count("\\") > 1:
        # End path with a slash if it does not have one
        if not path.endswith("\\"):
            path += "\\"
        return path
    return path


def _convert_path_mappings(
    connection: ConnectionCreate | ConnectionUpdate,
) -> list[PathMapping]:
    """Convert the path mappings of a connection to database objects \n
    Args:
        connection (ConnectionCreate | ConnectionUpdate): The connection to convert \n
    Returns:
        list[PathMapping]: The list of path mappings as database objects
    """
    db_path_mappings: list[PathMapping] = []
    for path_mapping in connection.path_mappings:
        db_path_mapping = PathMapping.model_validate(path_mapping)
        # Make sure that path_from/path_to ends with a slash
        db_path_mapping.path_from = end_path_with_slash(
            db_path_mapping.path_from
        )
        db_path_mapping.path_to = end_path_with_slash(db_path_mapping.path_to)
        db_path_mappings.append(db_path_mapping)
    return db_path_mappings


def _update_path_mappings(
    db_connection: Connection,
    connection_update: ConnectionUpdate,
    *,
    _session: Session,
) -> None:
    """Compare new and existing path mappings of a connection. \n
    Does the following: \n
    1. Update existing mappings \n
    2. Add new mappings \n
    3. Delete removed mappings \n
    All mappings are added to session, but not committed \n
    Args:
        connection (Connection): The connection to update
        connection_update (ConnectionUpdate): The connection update object
        _session (Session): The database session to use \n
    Returns:
        None: No return value, updates are made in place to \
            the connection object, and added to the session.
    """
    # Get new path mappings
    new_mappings = _convert_path_mappings(connection_update)
    # Make a dictionary of new mappings by id
    new_mappings_ids = [mapping.id for mapping in new_mappings if mapping.id]
    # Get existing path mappings
    existing_mappings = db_connection.path_mappings
    existing_mappings_dict = {
        mapping.id: mapping for mapping in existing_mappings
    }

    # Delete removed mappings
    for db_mapping in existing_mappings[:]:  # Copy the list to avoid modifying
        if db_mapping.id not in new_mappings_ids:
            db_connection.path_mappings.remove(db_mapping)
            _session.delete(db_mapping)

    for new_mapping in new_mappings:
        if new_mapping.id:
            # Update existing mappings
            if new_mapping.id in existing_mappings_dict:
                existing_mapping = existing_mappings_dict[new_mapping.id]
                existing_mapping.path_from = new_mapping.path_from
                existing_mapping.path_to = new_mapping.path_to
                _session.add(existing_mapping)
            # If new mapping has an id, but it does not exist in the database \
            # then clear it's id and add it as a new mapping
            else:
                new_mapping.id = None
                new_mapping.connection_id = db_connection.id
                db_connection.path_mappings.append(new_mapping)
        # Add new mappings
        else:
            db_connection.path_mappings.append(new_mapping)
    return None


@manage_session
def _get_db_item(
    connection_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    """Get a connection from the database. This is a private method. \n
    Args:
        connection_id (int): The id of the connection to read
        _session (optional): A session to use for the database connection. \
            Defaults to None, in which case a new session is created. \n
    Returns:
        Connection: The connection [database] object \n
    Raises:
        ItemNotFoundError: If a connection with provided id does not exist
    """
    connection = _session.get(Connection, connection_id)
    if not connection:
        raise ItemNotFoundError("Connection", connection_id)
    return connection
