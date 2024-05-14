from typing import Any
from exceptions import InvalidResponseError
from core.base.arr_manager.request_manager import AsyncRequestManager


class AsyncBaseArrManager(AsyncRequestManager):
    """Base class for async requests to Arr API"""

    def __init__(self, url: str, api_key: str, version: str = ""):
        """
        Constructor for connection to Arr API

        Args:
            url (str): Host URL to Arr API
            api_key (str): API Key for Arr API
            version (str, optional): Version of the API. Defaults to "".

        Returns:
            None
        """
        self.version = version
        super().__init__(url, api_key)

    async def api_version(self) -> str:
        """Get the version of the Arr API

        Args:
            None

        Returns:
            str: The version of the Arr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        response = await self._request("GET", "/api")
        if isinstance(response, dict):
            version: str = ""
            version = str(response.get("current", ""))
            return version
        if isinstance(response, str):
            return response
        return ""

    async def _get_system_status(self, app_name: str) -> str:
        """Get the system status of the Arr API

        Args:
            app_name (str): The name of the application to check the status of.

        Returns:
            str: The status of the Arr API with version if successful.

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If API response is invalid
        """
        status: str | dict[str, Any] | list[dict[str, Any]] = await self._request(
            "GET", f"/api/{self.version}/system/status"
        )
        if isinstance(status, str):
            raise InvalidResponseError(status)
        if not isinstance(status, dict):
            raise InvalidResponseError("Unknown Error")

        # Now status is a dict, check if the app_name and version is in the response
        result_app_name = status.get("appName")
        version = status.get("version")
        if result_app_name and version:
            result_app_name = str.lower(result_app_name)
            version = str(version)
            if result_app_name == app_name.lower():
                return f"{app_name} Connection Successful! Version: {status.get('version')}"
        raise InvalidResponseError(
            f"Invalid Host ({self.host_url}) or API Key ({self.api_key}), "
            f"not a {app_name} instance."
        )

    async def ping(self) -> str | dict[str, str] | list[dict[str, Any]]:
        """Ping the Arr API

        Args:
            None

        Returns:
            str | dict[str, str] | list[dict[str, Any]]: The response from the Arr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        return await self._request("GET", "/ping")
