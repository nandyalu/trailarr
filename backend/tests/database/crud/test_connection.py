import pytest

# from backend.database.crud.connection import connectionCRUD.ConnectionDatabaseHandler
import backend.core.base.database.manager.connection as connectionCRUD
from backend.core.base.database.manager.connection import validate_connection
from backend.core.base.database.models import (
    ArrType,
    ConnectionBase,
    ConnectionCreate,
    ConnectionUpdate,
    MonitorType,
)
from backend.exceptions import InvalidResponseError, ItemNotFoundError
from backend.core.radarr.api_manager import RadarrManager
from backend.core.sonarr.api_manager import SonarrManager


# Copied from backend/database/crud/connection.py
CREATE_SUCCESS_MSG = "Connection createded successfully! {}"
UPDATE_SUCCESS_MESSAGE = "Connection updated successfully!"
DELETE_SUCCESS_MESSAGE = "Connection deleted successfully!"
NO_CONN_MESSAGE = "Connection not found. Connection id: {} does not exist!"

VALIDATE_SUCCESS_MSG = "Success message"
VALIDATE_FAIL_MESSAGE = "Some Value is invalid!"

# Default connection object to use in tests
connection = ConnectionCreate(
    name="Connection Name",
    arr_type=ArrType.RADARR,
    url="http://example.com",
    api_key="API_KEY",
    monitor=MonitorType.MONITOR_NEW,
)

# Default connection update object to use in tests
connection_update = ConnectionUpdate(monitor=MonitorType.MONITOR_SYNC)

# Default Connection id for create
CONN_ID_1 = 1

# Default Connection id for failed read/update/delete
CONN_ID_2 = 2


class TestConnectionDatabaseHandler:
    db_handler = connectionCRUD.ConnectionDatabaseHandler()

    @pytest.fixture(autouse=True, scope="function")
    def session_fixture(self, monkeypatch):

        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        # Mock the validate_connection function to return a success message
        monkeypatch.setattr(
            "backend.database.crud.connection.validate_connection",
            mock_result_success,
        )

    @pytest.mark.asyncio
    async def test_create_connection(self):

        # Call the create_connection method and assert the return value
        result = await self.db_handler.create(connection)
        assert result == CREATE_SUCCESS_MSG.format(VALIDATE_SUCCESS_MSG)

    @pytest.mark.asyncio
    async def test_create_connection_fail(self, monkeypatch):
        def mock_result_fail(connection: ConnectionBase):
            raise InvalidResponseError(VALIDATE_FAIL_MESSAGE)

        # Mock the validate_connection function to raise an InvalidResponseError
        # This overrides the previous mock that was set in the autouse fixture
        monkeypatch.setattr(
            "backend.database.crud.connection.validate_connection",
            mock_result_fail,
        )
        # Call the create_connection method and assert the return value
        with pytest.raises(Exception) as exc_info:
            await self.db_handler.create(connection)

        assert str(exc_info.value) == VALIDATE_FAIL_MESSAGE
        assert exc_info.type.__name__ == "InvalidResponseError"

    @pytest.mark.asyncio
    async def test_read_connection(self):
        # Call the create_connection method and assert the return value
        await self.db_handler.create(connection)
        # self.test_create_connection()

        # Call the read_connection method and assert the return values match
        result = self.db_handler.read(CONN_ID_1)
        assert result.id == CONN_ID_1
        assert result.name == connection.name
        assert result.arr_type == connection.arr_type
        assert result.url == connection.url
        assert result.api_key == connection.api_key
        assert result.monitor == connection.monitor

    def test_read_connection_fail(self):
        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.db_handler.read(1_000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    @pytest.mark.asyncio
    async def test_read_connection_exists(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()

        # Call the check_if_exists method and assert the return value
        result = self.db_handler.check_if_exists(CONN_ID_1)
        assert result is True

    def test_read_connection_not_exists(self):
        # Call the check_if_exists method and assert the return value
        result = self.db_handler.check_if_exists(1_000)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_connection(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()

        # Call the update_connection method and assert the return value
        update_result = await self.db_handler.update(CONN_ID_1, connection_update)
        assert update_result == UPDATE_SUCCESS_MESSAGE

        # Call the read_connection method and assert the return values match
        read_result = self.db_handler.read(CONN_ID_1)
        assert read_result.id == CONN_ID_1
        assert read_result.name == connection.name
        assert read_result.arr_type == connection.arr_type
        assert read_result.url == connection.url
        assert read_result.api_key == connection.api_key
        assert read_result.monitor == connection_update.monitor

    @pytest.mark.asyncio
    async def test_update_connection_fail(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()

        # Call the update_connection method and assert the return value
        with pytest.raises(Exception) as exc_info:
            await self.db_handler.update(1_000, connection_update)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    @pytest.mark.asyncio
    async def test_delete_connection(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()
        await self.test_create_connection()
        await self.test_create_connection()
        # Note: We are creating multiple connections and deleting the second one
        # to test the delete method so that it does not affect the other tests
        # that rely on the first connection being present (movie / series CRUD tests)

        # Call the delete_connection method and assert the return value
        delete_result = self.db_handler.delete(CONN_ID_2)
        assert delete_result == DELETE_SUCCESS_MESSAGE

        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.db_handler.read(CONN_ID_2)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(CONN_ID_2)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_delete_connection_fail(self):
        # Call the delete_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.db_handler.delete(1000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1000)
        assert exc_info.type.__name__ == "ItemNotFoundError"


class TestConnectionValidation:

    @pytest.mark.asyncio
    async def test_validate_connection_no_connection(self):
        # Call the validate_connection function with no connection
        with pytest.raises(ItemNotFoundError) as exceptions:
            await validate_connection(None)  # type: ignore

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "No connection provided!"

    @pytest.mark.asyncio
    async def test_validate_connection_valid_connection(self, monkeypatch):
        # Create a connection object
        connection = ConnectionBase(
            name="Connection Name",
            arr_type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        # Mock the get_system_status function to return a success message
        async def mock_result_success(self):
            return "Success message"

        monkeypatch.setattr(RadarrManager, "get_system_status", mock_result_success)
        # Call validate_connection function with the mock connection and assert return value
        result = await validate_connection(connection)
        assert result == "Success message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_radarr(self, monkeypatch):
        # Create a connection object
        connection = ConnectionBase(
            name="Connection Name",
            arr_type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        # Mock the get_system_status function to raise an Exception
        async def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(RadarrManager, "get_system_status", mock_result_invalid)

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            await validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_sonarr(self, monkeypatch):
        # Create a connection object
        connection = ConnectionBase(
            name="Connection Name",
            arr_type=ArrType.SONARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        # Mock the get_system_status function to raise an Exception
        async def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(SonarrManager, "get_system_status", mock_result_invalid)

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            await validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"
