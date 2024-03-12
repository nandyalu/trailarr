from backend.services.arr_manager.base import AsyncBaseArrManager


class SonarrManager(AsyncBaseArrManager):
    APPNAME = "Sonarr"

    def __init__(self, url: str, api_key: str):
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

    # Define Radarr specific API methods here
