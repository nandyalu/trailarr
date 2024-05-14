import pytest
from exceptions import InvalidResponseError
from core.base.arr_manager.base import AsyncBaseArrManager
from tests import conftest


class TestAsyncBaseArrManager:
    URL = conftest.TEST_AIOHTTP_URL
    API_KEY = conftest.TEST_AIOHTTP_APIKEY
    arr_manager = AsyncBaseArrManager(URL, API_KEY, "v3")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload, expected_result",
        [
            ({"current": "v3"}, "v3"),
            ("v3", "v3"),
            ({}, ""),
            (None, ""),
            ({"abc": "abc"}, ""),
        ],
    )
    async def test_api_version_success(self, debug_aiohttp, payload, expected_result):
        # Arrange
        debug_aiohttp.get(f"{self.URL}/api", status=200, payload=payload)

        # Act
        actual_result = await self.arr_manager.api_version()

        # Assert
        assert actual_result == expected_result

    @pytest.mark.asyncio
    async def test_get_system_status_success(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload={"appName": "Radarr", "version": "3.0.0"},
        )

        # Act
        result = await self.arr_manager._get_system_status("Radarr")

        # Assert
        assert result == "Radarr Connection Successful! Version: 3.0.0"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload",
        [
            {"appName": "WrongApp", "version": "3.0.0"},
            {"appName": "", "version": "1.0.0"},
            {"appName": "Radarr", "version": ""},
            {"appName": "testApp", "version": ""},
        ],
    )
    async def test_get_system_status_invalid_appname(self, debug_aiohttp, payload):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload=payload,
        )

        # Act
        with pytest.raises(Exception) as e:
            await self.arr_manager._get_system_status("Radarr")

        # Assert
        _error = f"Invalid Host ({self.URL}) or API Key ({self.API_KEY}), not a Radarr instance."
        assert str(e.value) == _error
        assert e.type == InvalidResponseError

    @pytest.mark.asyncio
    async def test_get_system_status_str_response(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload="Version: v3",
        )

        # Act
        with pytest.raises(Exception) as e:
            await self.arr_manager._get_system_status("Radarr")

        # Assert
        assert str(e.value) == "Version: v3"
        assert e.type == InvalidResponseError

    @pytest.mark.asyncio
    async def test_get_system_status_error_status(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            exception=ValueError("Error message"),
        )

        # Act
        with pytest.raises(Exception) as e:
            await self.arr_manager._get_system_status("Radarr")

        # Assert
        assert e.type == ConnectionError

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", [None, 123])
    async def test_get_system_status_unknown_error(self, debug_aiohttp, payload):
        # Arrange
        debug_aiohttp.get(
            f"{self.URL}/api/v3/system/status",
            status=200,
            payload=payload,
        )

        # Act
        with pytest.raises(Exception) as e:
            await self.arr_manager._get_system_status("Radarr")

        # Assert
        assert str(e.value) == "Unknown Error"
        assert e.type == InvalidResponseError

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", ["Pong", 123, {"ping": "Pong"}])
    async def test_ping_success(self, debug_aiohttp, payload):
        # Arrange
        debug_aiohttp.get(f"{self.URL}/ping", status=200, payload=payload)

        # Act
        result = await self.arr_manager.ping()

        # Assert
        assert result == payload

    @pytest.mark.asyncio
    async def test_ping_error(self, debug_aiohttp):
        # Arrange
        debug_aiohttp.get(f"{self.URL}/ping", exception=Exception("Error message"))

        # Act
        with pytest.raises(Exception) as e:
            await self.arr_manager.ping()

        # Assert
        assert e.type == ConnectionError
