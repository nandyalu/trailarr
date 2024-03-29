from sqlmodel import Session
from backend.database.models.connection import (
    ArrType,
    Connection,
    ConnectionBase,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)

from backend.database.utils.engine import manage_session
from backend.exceptions import ItemNotFoundError
from backend.services.arr_manager.radarr import RadarrManager
from backend.services.arr_manager.sonarr import SonarrManager


class ConnectionDatabaseHandler:
    """CRUD operations for the Connection database table"""

    CREATE_SUCCESS_MESSAGE = "Connection createded successfully! {}"
    UPDATE_SUCCESS_MESSAGE = "Connection updated successfully!"
    DELETE_SUCCESS_MESSAGE = "Connection deleted successfully!"
    NO_CONN_MESSAGE = "Connection not found. Connection id: {} does not exist!"

    @manage_session
    async def create(
        self,
        connection: ConnectionCreate,
        *,
        _session: Session = None,  # type: ignore
    ) -> str:
        """Create a new connection in the database

        Args:
            connection (Connection): The connection to create
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            str: The status message of the connection with version if valid.

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

        return self.CREATE_SUCCESS_MESSAGE.format(status)

    @manage_session
    def check_if_exists(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> bool:
        """Check if a connection exists in the database

        Args:
            connection_id (int): The id of the connection to check
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if the connection exists, False if not
        """

        connection = _session.get(Connection, connection_id)
        return bool(connection)

    @manage_session
    def _get_db_item(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> Connection:
        """Get a connection from the database. This is a private method.

        Args:
            connection_id (int): The id of the connection to read
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            Connection: The connection object

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
        """Read a connection from the database

        Args:
            connection_id (int): The id of the connection to read
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            ConnectionRead: The read-only connection object

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
    ) -> str:
        """Update an existing connection in the database

        Args:
            connection_id (int): The id of the connection to update
            connection (Connection): The connection to update
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            str: The status message of the connection with version if valid.

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
        return self.UPDATE_SUCCESS_MESSAGE

    @manage_session
    def delete(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> str:
        """Delete a connection from the database

        Args:
            connection_id (int): The id of the connection to delete
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            str: The status message of the connection with version if valid.

        Raises:
            ItemNotFoundError: If a connection with provided id does not exist
        """

        connection = self._get_db_item(connection_id, _session=_session)
        _session.delete(connection)
        _session.commit()
        return self.DELETE_SUCCESS_MESSAGE


async def validate_connection(connection: ConnectionBase) -> str:
    """Validate the connection details and test the connection to the server
    Args:
        connection (ConnectionBase): The connection to validate
    Returns:
        str: The status message of the connection with version if valid.
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


# For SQLModel bulk operations
#   link: https://docs.sqlalchemy.org/en/13/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow # noqa
#   Use session.add_all(Model, [dict1, dict2, dict3, ...]) to insert multiple NEW rows.
#   bulk_insert_mappings is no longer needed as of SQLALchemy 2.0
#       as it is now built into the session.add_all() method
#   Use session.bulk_update_mappings(Model, [dict1, dict2, dict3, ...]) to update multiple EXISTING rows. # noqa
