from typing import Any
from backend.exceptions import InvalidResponseError
from backend.services.arr_manager.request_manager import RequestManager


class BaseArrManager(RequestManager):
    """Base class for requests to Arr API

    Args:
        url (str): Host URL to Arr API
        api_key (str): API Key for Arr API
        version (str, optional): Version of the API. Defaults to "".

    Returns:
        None
    """

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

    def api_version(self) -> str:
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
        response = self._request("GET", "/api")
        if isinstance(response, dict):
            version: str = ""
            version = str(response.get("current", ""))
            return version
        if isinstance(response, str):
            return response
        return ""

    def _get_system_status(self, app_name: str) -> str:
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
        status: str | dict[str, Any] = self._request(
            "GET", f"/api/{self.version}/system/status"
        )
        if isinstance(status, dict):
            result_appName = status.get("appName")
            version = status.get("version")
            if result_appName and version:
                result_appName = str.lower(result_appName)
                version = str(version)
                if result_appName == app_name.lower():
                    return f"{app_name} Connection Successful! Version: {status.get('version')}"
            raise InvalidResponseError(
                f"Invalid Host ({self.host_url}) or API Key ({self.api_key}), "
                f"not a {app_name} instance."
            )
        if isinstance(status, str):
            raise InvalidResponseError(status)
        raise InvalidResponseError("Unknown Error")

    def ping(self) -> str | dict[str, str]:
        """Ping the Arr API

        Args:
            None

        Returns:
            str | dict[str, str]: The response from the Arr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        return self._request("GET", "/ping")
