import pytest

from backend.database.validation.connection import validate_connection
from backend.database.models.connection import ConnectionBase, ArrType, MonitorType
from backend.exceptions import InvalidResponseError, ItemNotFoundError
from backend.services.arr_manager.radarr import RadarrManager
from backend.services.arr_manager.sonarr import SonarrManager


class TestConnectionValidation:

    def test_validate_connection_no_connection(self):
        # Call the validate_connection function with no connection
        with pytest.raises(ItemNotFoundError) as exceptions:
            validate_connection(None)  # type: ignore

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "No connection provided!"

    def test_validate_connection_valid_connection(self, monkeypatch):
        # Create a connection object
        connection = ConnectionBase(
            name="Connection Name",
            type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        # Mock the get_system_status function to return a success message
        def mock_result_success(self):
            return "Success message"

        monkeypatch.setattr(RadarrManager, "get_system_status", mock_result_success)
        # Call validate_connection function with the mock connection and assert return value
        assert validate_connection(connection) == "Success message"

    def test_validate_connection_invalid_connection_radarr(self, monkeypatch):
        # Create a connection object
        connection = ConnectionBase(
            name="Connection Name",
            type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        # Mock the get_system_status function to raise an Exception
        def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(RadarrManager, "get_system_status", mock_result_invalid)

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"

    def test_validate_connection_invalid_connection_sonarr(self, monkeypatch):
        # Create a connection object
        connection = ConnectionBase(
            name="Connection Name",
            type=ArrType.SONARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )

        # Mock the get_system_status function to raise an Exception
        def mock_result_invalid(self):
            raise InvalidResponseError("Error message")

        monkeypatch.setattr(SonarrManager, "get_system_status", mock_result_invalid)

        # Call the validate_connection function with the mock connection
        with pytest.raises(InvalidResponseError) as exceptions:
            validate_connection(connection)

        # Assert that the correct error message is raised
        assert str(exceptions.value) == "Error message"
