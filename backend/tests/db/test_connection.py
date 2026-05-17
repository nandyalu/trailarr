import pytest

import db.repos.connection as connection_repo
from db.models.connection import (
    ArrType,
    ConnectionBase,
    ConnectionCreate,
    ConnectionUpdate,
    MonitorType,
)
from exceptions import InvalidResponseError, ItemNotFoundError
from integrations.arr.radarr import RadarrManager
from integrations.arr.sonarr import SonarrManager
from services.connection_service import validate_connection

# Copied from connection_service.py
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


class TestConnectionRepo:

    @pytest.fixture(autouse=True, scope="function")
    def session_fixture(self, monkeypatch):

        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )

    @pytest.mark.asyncio
    async def test_create_connection(self, monkeypatch):
        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )
        from services.connection_service import create
        result, id = await create(connection)
        assert result.name == connection.name
        assert id >= 1

    @pytest.mark.asyncio
    async def test_create_connection_fail(self, monkeypatch):
        async def mock_result_fail(connection: ConnectionBase):
            raise InvalidResponseError(VALIDATE_FAIL_MESSAGE)

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_fail,
        )
        from services.connection_service import create
        with pytest.raises(InvalidResponseError) as exc_info:
            await create(connection)

        assert str(exc_info.value) == VALIDATE_FAIL_MESSAGE

    @pytest.mark.asyncio
    async def test_read_connection(self, monkeypatch):
        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )
        from services.connection_service import create
        await create(connection)

        result = connection_repo.read(CONN_ID_1)
        assert result.id == CONN_ID_1
        assert result.name == connection.name
        assert result.arr_type == connection.arr_type
        assert result.url == connection.url
        assert result.api_key == connection.api_key
        assert result.monitor == connection.monitor

    def test_read_connection_fail(self):
        with pytest.raises(ItemNotFoundError) as exc_info:
            connection_repo.read(1_000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)

    def test_read_connection_not_exists(self):
        result = connection_repo.exists(1_000)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_connection(self, monkeypatch):
        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )
        from services.connection_service import create, update
        await create(connection)
        update_result = await update(CONN_ID_1, connection_update)

        assert update_result.id == CONN_ID_1
        assert update_result.name == connection.name
        assert update_result.monitor == connection_update.monitor

    @pytest.mark.asyncio
    async def test_update_connection_fail(self, monkeypatch):
        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )
        from services.connection_service import create, update
        await create(connection)

        with pytest.raises(ItemNotFoundError) as exc_info:
            await update(1_000, connection_update)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)

    @pytest.mark.asyncio
    async def test_read_connection_exists(self, monkeypatch):
        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )
        from services.connection_service import create
        await create(connection)

        result = connection_repo.exists(CONN_ID_1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_connection(self, monkeypatch):
        async def mock_result_success(connection: ConnectionBase):
            return VALIDATE_SUCCESS_MSG

        monkeypatch.setattr(
            "services.connection_service.validate_connection",
            mock_result_success,
        )
        from services.connection_service import create
        await create(connection)
        await create(connection)
        await create(connection)

        delete_result = connection_repo.delete(CONN_ID_2)
        assert delete_result is True

        with pytest.raises(ItemNotFoundError) as exc_info:
            connection_repo.read(CONN_ID_2)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(CONN_ID_2)

    def test_delete_connection_fail(self):
        with pytest.raises(ItemNotFoundError) as exc_info:
            connection_repo.delete(1000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1000)


class TestConnectionValidation:

    @pytest.mark.asyncio
    async def test_validate_connection_no_connection(self):
        with pytest.raises(Exception):
            await validate_connection(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_validate_connection_valid_connection(self, monkeypatch):
        connection = ConnectionBase(
            name="Connection Name",
            arr_type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        async def mock_result_success(self):
            return "Success message"

        monkeypatch.setattr(
            RadarrManager, "get_system_status", mock_result_success
        )
        result = await validate_connection(connection)
        assert result == "Success message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_radarr(
        self, monkeypatch
    ):
        connection = ConnectionBase(
            name="Connection Name",
            arr_type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        async def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(
            RadarrManager, "get_system_status", mock_result_invalid
        )

        with pytest.raises(InvalidResponseError) as exceptions:
            await validate_connection(connection)

        assert str(exceptions.value) == "Error message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_sonarr(
        self, monkeypatch
    ):
        connection = ConnectionBase(
            name="Connection Name",
            arr_type=ArrType.SONARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        async def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(
            SonarrManager, "get_system_status", mock_result_invalid
        )

        with pytest.raises(InvalidResponseError) as exceptions:
            await validate_connection(connection)

        assert str(exceptions.value) == "Error message"
