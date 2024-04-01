import pytest
from backend.exceptions import InvalidResponseError
from backend.core.sonarr.api_manager import SonarrManager
from backend.tests import conftest


class TestSonarrManager:

    URL = conftest.TEST_AIOHTTP_URL
    API_KEY = conftest.TEST_AIOHTTP_APIKEY
    sonarr_manager = SonarrManager(URL, API_KEY)

    @pytest.mark.asyncio
    async def test_get_system_status_success(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload={"appName": "Sonarr", "version": "3.0.0"},
        )

        # Act
        result = await self.sonarr_manager.get_system_status()

        # Assert
        assert result == "Sonarr Connection Successful! Version: 3.0.0"

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
            await self.sonarr_manager.get_system_status()

        # Assert
        _error = f"Invalid Host ({self.URL}) or API Key ({self.API_KEY}), not a Sonarr instance."
        assert str(e.value) == _error
        assert e.type == InvalidResponseError
