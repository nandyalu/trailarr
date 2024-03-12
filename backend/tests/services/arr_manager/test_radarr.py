import pytest
from backend.exceptions import InvalidResponseError
from backend.services.arr_manager.radarr import RadarrManager
from backend.tests import conftest


class TestRadarrManager:
    URL = conftest.TEST_AIOHTTP_URL
    API_KEY = conftest.TEST_AIOHTTP_APIKEY
    radarr_manager = RadarrManager(URL, API_KEY)

    @pytest.mark.asyncio
    async def test_get_system_status_success(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload={"appName": "Radarr", "version": "3.0.0"},
        )

        # Act
        result = await self.radarr_manager.get_system_status()

        # Assert
        assert result == "Radarr Connection Successful! Version: 3.0.0"

    @pytest.mark.asyncio
    async def test_get_system_status_exception(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload={"appName": "WrongApp", "version": "3.0.0"},
        )

        # Act
        with pytest.raises(InvalidResponseError) as e:
            await self.radarr_manager.get_system_status()

        # Assert
        _error = f"Invalid Host ({self.URL}) or API Key ({self.API_KEY}), not a Radarr instance."
        assert str(e.value) == _error
        assert e.type == InvalidResponseError
