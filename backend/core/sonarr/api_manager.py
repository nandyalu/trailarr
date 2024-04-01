from typing import Any
from backend.exceptions import InvalidResponseError
from backend.core.base.arr_manager.base import AsyncBaseArrManager


class SonarrManager(AsyncBaseArrManager):
    APPNAME = "Sonarr"

    def __init__(self, url: str, api_key: str):
        """
        Constructor for connection to Sonarr API

        Args:
            url (str): Host URL to Sonarr API
            api_key (str): API Key for Sonarr API

        Returns:
            None
        """
        self.version = "v3"
        super().__init__(url, api_key, self.version)

    async def get_system_status(self) -> str:
        """Get the system status of the Sonarr API

        Args:
            None

        Returns:
            str: The status of the Sonarr API with version.

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If API response is invalid
        """
        return await self._get_system_status(self.APPNAME)

    # Define Sonarr specific API methods here

    async def get_all_series(self) -> list[dict[str, Any]]:
        """Get all series from the Sonarr API

        Args:
            None

        Returns:
            list[dict[str, Any]: List of series from the Sonarr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        series = await self._request("GET", f"/api/{self.version}/series")
        if isinstance(series, list):
            return series
        raise InvalidResponseError("Invalid response from Sonarr API")

    async def get_series(self, sonarr_id: int) -> dict[str, Any]:
        """Get a series from the Sonarr API

        Args:
            sonarr_id (int): The ID of the series to get

        Returns:
            dict[str, Any]: Series from the Sonarr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        series = await self._request("GET", f"/api/{self.version}/series/{sonarr_id}")
        if isinstance(series, dict):
            return series
        raise InvalidResponseError("Invalid response from Sonarr API")

    # Define Alias methods here!
    get_all_media = get_all_series
    get_media = get_series
