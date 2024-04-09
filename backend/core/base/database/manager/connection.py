from sqlmodel import Session, select
from backend.core.base.database.models.connection import (
    ArrType,
    Connection,
    ConnectionBase,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)

from backend.core.base.database.utils.engine import manage_session
from backend.exceptions import ItemNotFoundError
from backend.core.radarr.api_manager import RadarrManager
from backend.core.sonarr.api_manager import SonarrManager


class ConnectionDatabaseHandler:
    """CRUD operations for the Connection database table"""

    @manage_session
    async def create(
        self,
        connection: ConnectionCreate,
        *,
        _session: Session = None,  # type: ignore
    ) -> str:
        """Create a new connection in the database \n
        Args:
            connection (Connection): The connection to create
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created. \n
        Returns:
            str: The status message of the connection with version if created. \n
        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If API response is invalid
            ValidationError: If the connection is invalid
        """
        # Validate the connection details, will raise an error if invalid
        status = await validate_connection(connection)
        # Use the session to add the connection to the database
        db_connection = Connection.model_validate(connection)
        _session.add(db_connection)
        _session.commit()
        return status

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
