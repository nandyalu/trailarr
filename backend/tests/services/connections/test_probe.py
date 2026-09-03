"""Tests for the network probes against a connection's server.

These moved out of tests/database/manager/test_connection.py in Phase 7
Stage B, with the functions they cover.
"""

import pytest

from database.models.connection import ArrType, ConnectionBase
from exceptions import InvalidResponseError
from services.connections import probe
from services.connections.arr.radarr.api_manager import RadarrManager
from services.connections.arr.sonarr.api_manager import SonarrManager


def _connection(arr_type: ArrType = ArrType.RADARR) -> ConnectionBase:
    return ConnectionBase(
        name="Connection Name",
        arr_type=arr_type,
        url="http://example.com",
        api_key="API_KEY",
        monitor_new_media=True,
    )


class TestValidateConnection:

    @pytest.mark.asyncio
    async def test_validate_connection_no_connection(self):
        # Call the validate_connection function with no connection
        with pytest.raises(Exception) as exceptions:
            await probe.validate_connection(None)  # type: ignore

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Connection with id 0 not found"

    @pytest.mark.asyncio
    async def test_validate_connection_valid_connection(self, monkeypatch):
        connection = _connection(ArrType.RADARR)

        # Mock the get_system_status function to return a success message
        async def mock_result_success(self):
            return "Success message"

        monkeypatch.setattr(
            RadarrManager, "get_system_status", mock_result_success
        )
        # Call validate_connection function with the mock connection and assert return value
        result = await probe.validate_connection(connection)
        assert result == "Success message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_radarr(
        self, monkeypatch
    ):
        connection = _connection(ArrType.RADARR)

        # Mock the get_system_status function to raise an Exception
        async def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(
            RadarrManager, "get_system_status", mock_result_invalid
        )

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            await probe.validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_connection_sonarr(
        self, monkeypatch
    ):
        connection = _connection(ArrType.SONARR)

        # Mock the get_system_status function to raise an Exception
        async def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(
            SonarrManager, "get_system_status", mock_result_invalid
        )

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            await probe.validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"


class TestGetRootFolders:

    @pytest.mark.asyncio
    async def test_no_connection_raises(self):
        with pytest.raises(Exception) as exceptions:
            await probe.get_rootfolders(None)  # type: ignore

        assert str(exceptions.value) == "Connection with id 0 not found"

    @pytest.mark.asyncio
    async def test_radarr_rootfolders(self, monkeypatch):
        async def mock_roots(self):
            return ["/movies"]

        monkeypatch.setattr(RadarrManager, "get_rootfolders", mock_roots)
        assert await probe.get_rootfolders(_connection()) == ["/movies"]
