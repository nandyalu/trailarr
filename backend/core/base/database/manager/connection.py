from sqlmodel import Session, select
from core.base.database.models.connection import (
    ArrType,
    Connection,
    ConnectionBase,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
    PathMapping,
)

from core.base.database.models.media import Media
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError
from core.radarr.api_manager import RadarrManager
from core.sonarr.api_manager import SonarrManager


class ConnectionDatabaseManager:
    """CRUD operations for the Connection database table"""

    @manage_session
    async def create(
        self,
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
        status = await validate_connection(connection)
        # Convert path mappings to database objects
        # Calling Connection.model_validate(connection) will raise an error \
        # with the current implementation of PathMappingCRU
        # https://github.com/nandyalu/trailarr/issues/53
        _path_mappings = self._convert_path_mappings(connection)
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

    @manage_session
    def check_if_exists(
        self,
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

    @manage_session
    def read_all(
        self,
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
        return [ConnectionRead.model_validate(connection) for connection in connections]

    def _end_path_with_slash(self, path: str) -> str:
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
        self, connection: ConnectionCreate | ConnectionUpdate
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
            db_path_mapping.path_from = self._end_path_with_slash(
                db_path_mapping.path_from
            )
            db_path_mapping.path_to = self._end_path_with_slash(db_path_mapping.path_to)
            db_path_mappings.append(db_path_mapping)
        return db_path_mappings

    def _update_path_mappings(
        self,
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
        new_mappings = self._convert_path_mappings(connection_update)
        # Make a dictionary of new mappings by id
        new_mappings_ids = [mapping.id for mapping in new_mappings if mapping.id]
        # Get existing path mappings
        existing_mappings = db_connection.path_mappings
        existing_mappings_dict = {mapping.id: mapping for mapping in existing_mappings}

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
        self,
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

    @manage_session
    def read(
        self,
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
        connection = self._get_db_item(connection_id, _session=_session)
        # Convert the connection to a ConnectionRead object
        connection_read = ConnectionRead.model_validate(connection)
        return connection_read

    @manage_session
    async def update(
        self,
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
        db_connection = self._get_db_item(connection_id, _session=_session)
        # Update the connection details from input
        connection_update_data = connection_update.model_dump(exclude_unset=True)
        db_connection.sqlmodel_update(connection_update_data)
        # Update the path mappings
        self._update_path_mappings(db_connection, connection_update, _session=_session)
        # Validate the connection details
        await validate_connection(db_connection)
        # Commit the changes to the database
        _session.add(db_connection)
        _session.commit()
        return ConnectionRead.model_validate(db_connection)

    @manage_session
    def delete(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> bool:
        """Delete a connection from the database \n
        Args:
            connection_id (int): The id of the connection to delete
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created. \n
        Returns:
            bool: True if the connection was deleted successfully. \n
        Raises:
            ItemNotFoundError: If a connection with provided id does not exist
        """
        connection = self._get_db_item(connection_id, _session=_session)
        _session.delete(connection)
        # Delete all path mappings associated with the connection
        for path_mapping in connection.path_mappings:
            _session.delete(path_mapping)
        # Delete all media associated with the connection
        _statement = select(Media).where(Media.connection_id == connection_id)
        media_list = _session.exec(_statement).all()
        for media in media_list:
            _session.delete(media)
        _session.commit()
        return True


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


async def get_connection_rootfolders(connection: ConnectionBase) -> list[str]:
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
