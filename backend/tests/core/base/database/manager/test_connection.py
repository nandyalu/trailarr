import pytest

# from database.crud.connection import connectionCRUD.ConnectionDatabaseHandler
import core.base.database.manager.connection as db_manager
import core.base.database.manager.connection.base as db_manager_base
from core.base.database.models.connection import (
    ArrType,
    ConnectionBase,
    ConnectionCreate,
    ConnectionUpdate,
    MonitorType,
)
from exceptions import InvalidResponseError, ItemNotFoundError
from core.radarr.api_manager import RadarrManager
from core.sonarr.api_manager import SonarrManager

# Copied from backend/database/crud/connection.py
CREATE_SUCCESS_MSG = "Connection createded successfully! {}"
UPDATE_SUCCESS_MESSAGE = "Connection updated successfully!"
DELETE_SUCCESS_MESSAGE = "Connection deleted successfully!"
NO_CONN_MESSAGE = "Connection with id {} not found"

VALIDATE_SUCCESS_MSG = "Success message"
VALIDATE_FAIL_MESSAGE = "Some Value is invalid!"

# Default connection object to use in tests
connection = ConnectionCreate(
    name="Connection Name",
    arr_type=ArrType.RADARR,
    url="http://example.com",
    api_key="API_KEY",
    monitor=MonitorType.MONITOR_NEW,
    path_mappings=[],
)

# Default connection update object to use in tests
connection_update = ConnectionUpdate(
    monitor=MonitorType.MONITOR_SYNC, path_mappings=[]
)

# Default Connection id for create
CONN_ID_1 = 1

# Default Connection id for failed read/update/delete
CONN_ID_2 = 2


class TestConnectionDatabaseHandler:

    @pytest.fixture(autouse=True, scope="function")
    def session_fixture(self, monkeypatch):

        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        # Mock the validate_connection function to return a success message
        # Note: We have to match the actual module path where
        # validate_connection is defined for monkeypatching to work
        monkeypatch.setattr(
            db_manager_base,
            "validate_connection",
            mock_result_success,
        )
        # db_manager.validate_connection = mock_result_success

    @pytest.mark.asyncio
    async def test_create_connection(self):

        # Call the create_connection method and assert the return value
        result, id = await db_manager.create(connection)
        assert result == VALIDATE_SUCCESS_MSG
        assert id >= 1

    @pytest.mark.asyncio
    async def test_create_connection_fail(self, monkeypatch):
        def mock_result_fail(connection: ConnectionBase):
            raise InvalidResponseError(VALIDATE_FAIL_MESSAGE)

        # Mock the validate_connection function to raise an InvalidResponseError
        # This overrides the previous mock that was set in the autouse fixture
        monkeypatch.setattr(
            db_manager_base,
            "validate_connection",
            mock_result_fail,
        )
        # Call the create_connection method and assert the return value
        with pytest.raises(InvalidResponseError) as exc_info:
            await db_manager.create(connection)

        assert str(exc_info.value) == VALIDATE_FAIL_MESSAGE

    @pytest.mark.asyncio
    async def test_read_connection(self):
        # Call the create_connection method and assert the return value
        await db_manager.create(connection)
        # self.test_create_connection()

        # Call the read_connection method and assert the return values match
        result = db_manager.read(CONN_ID_1)
        assert result.id == CONN_ID_1
        assert result.name == connection.name
        assert result.arr_type == connection.arr_type
        assert result.url == connection.url
        assert result.api_key == connection.api_key
        assert result.monitor == connection.monitor

    def test_read_connection_fail(self):
        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.read(1_000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)

    @pytest.mark.asyncio
    async def test_read_connection_exists(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()

        # Call the `exists` method and assert the return value
        result = db_manager.exists(CONN_ID_1)
        assert result is True

    def test_read_connection_not_exists(self):
        # Call the `exists` method and assert the return value
        result = db_manager.exists(1_000)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_connection(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()

        # Call the update_connection method and assert the return value
        update_result = await db_manager.update(CONN_ID_1, connection_update)
        # assert update_result == UPDATE_SUCCESS_MESSAGE

        # Call the read_connection method and assert the return values match
        # update_result = db_manager.read(CONN_ID_1)
        assert update_result.id == CONN_ID_1
        assert update_result.name == connection.name
        assert update_result.arr_type == connection.arr_type
        assert update_result.url == connection.url
        assert update_result.api_key == connection.api_key
        assert update_result.monitor == connection_update.monitor

    @pytest.mark.asyncio
    async def test_update_connection_fail(self):
        # Call the create_connection method and assert the return value
        await self.test_create_connection()

        # Call the update_connection method and assert the return value
        with pytest.raises(ItemNotFoundError) as exc_info:
            await db_manager.update(1_000, connection_update)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)

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
        delete_result = db_manager.delete(CONN_ID_2)
        assert delete_result is True

        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.read(CONN_ID_2)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(CONN_ID_2)

    def test_delete_connection_fail(self):
        # Call the delete_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.delete(1000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1000)


class TestConnectionValidation:

    @pytest.mark.asyncio
    async def test_validate_connection_no_connection(self):
        # Call the validate_connection function with no connection
        with pytest.raises(ItemNotFoundError) as exceptions:
            await db_manager.validate_connection(None)  # type: ignore

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Connection with id 0 not found"

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

        monkeypatch.setattr(
            RadarrManager, "get_system_status", mock_result_success
        )
        # Call validate_connection function with the mock connection and assert return value
        result = await db_manager.validate_connection(connection)
        assert result == "Success message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_radarr(
        self, monkeypatch
    ):
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

        monkeypatch.setattr(
            RadarrManager, "get_system_status", mock_result_invalid
        )

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            await db_manager.validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_sonarr(
        self, monkeypatch
    ):
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

        monkeypatch.setattr(
            SonarrManager, "get_system_status", mock_result_invalid
        )

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            await db_manager.validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"
