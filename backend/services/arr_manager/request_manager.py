from typing import Any
from urllib.parse import urlparse, urlunparse
import aiohttp

from backend.exceptions import ConnectionTimeoutError, InvalidResponseError


class AsyncRequestManager:
    """Base class for asynchronous requests to Arr API"""

    def __init__(self, host_url: str, api_key: str):
        """Constructor for connection to Arr API

        Args:
            host_url (str): Host URL to Arr API
            api_key (str): API Key for Arr API
        """
        self.host_url = host_url.rstrip("/")
        self.api_key = api_key

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: list[dict] | dict | None = None,
    ) -> str | dict[str, Any]:
        """Send a request of HTTP method type to the Arr API

        Args:
            method (str): HTTP method type
            path (str): Destination for specific call
            params (dict | None): Parameters to send with the request
            data (list[dict] | dict | None): Data to send with the request

        Returns:
            str | dict[str, Any]: Response from the API in string or dictionary format

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        initial_url = f"{self.host_url}/{path}"
        parsed_url = urlparse(initial_url)
        fixed_path = parsed_url.path.replace("//", "/").rstrip("/")
        url = urlunparse(parsed_url._replace(path=fixed_path))
        headers = {"X-Api-Key": self.api_key}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, url, headers=headers, params=params, data=data
                ) as client_response:
                    # client_response.raise_for_status()
                    response = await self._process_response(client_response)
                    return response
            except aiohttp.ServerTimeoutError:
                raise ConnectionTimeoutError(
                    "Timeout occurred while connecting to API."
                )
            except aiohttp.ClientConnectionError:
                raise ConnectionError("Connection Refused while connecting to API.")
            except Exception:
                raise ConnectionError(
                    "Unable to connect to API. Check your connection."
                )

    async def _process_response(
        self, response: aiohttp.ClientResponse
    ) -> str | dict[str, Any]:
        """Process the response from the API

        Args:
            response (aiohttp.ClientResponse): Response from the API

        Returns:
            str | dict[str, Any]: Processed response from the API

        Raises:
            ConnectionError: If the response is not 200
            InvalidResponseError: If the API response is invalid
        """
        if response.status == 200:
            try:
                return await response.json()
            except Exception:
                # Check if response is html
                response_content_type = response.headers.get("content-type")
                if response_content_type and "text" in response_content_type:
                    raise InvalidResponseError(
                        f"Invalid Response from server! Check if {self.host_url}"
                        f" is a valid API endpoint."
                    )
                return await response.text()
        if response.status == 400:
            raise ConnectionError(
                f"Bad Request, possibly a bug. {str(await response.text())}"
            )
        if response.status == 401:
            raise ConnectionError(
                f"Unauthorized. Please ensure valid API Key is used: {self.api_key}"
            )
        if response.status == 403:
            raise ConnectionError(
                f"Access restricted. Please ensure API Key '{self.api_key}'"
                f" has correct permissions"
            )
        if response.status == 404:
            raise ConnectionError(f"Resource not found: {response.url}")
        if response.status == 405:
            raise ConnectionError(f"The endpoint {response.url} is not allowed")
        if response.status == 500:
            try:
                message = (await response.json()).get("message", "")
                error_message = f"Internal Server Error: {message}"
            except Exception:
                text = await response.text()
                if text:
                    error_message = f"Internal Server Error: {text}"
                else:
                    error_message = "Internal Server Error: Unknown Error Occurred."
            raise ConnectionError(error_message)
        if response.status == 502:
            raise ConnectionError(
                f"Bad Gateway. Check if your server at {response.url} is accessible."
            )
        raise ConnectionError(
            f"Invalid Host ({self.host_url}) or API Key ({self.api_key}), "
            f"not a Radarr or Sonarr instance."
        )
