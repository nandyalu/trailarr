from typing import Any
from urllib.parse import urlparse, urlunparse
import requests

from backend.exceptions import ConnectionTimeoutError, InvalidResponseError


class RequestManager:
    """Base class for requests to Arr API"""

    def __init__(self, host_url: str, api_key: str):
        """Constructor for connection to Arr API

        Args:
            host_url (str): Host URL to Arr API
            api_key (str): API Key for Arr API
        """
        self.host_url = host_url.rstrip("/")
        self.api_key = api_key
        self.session: requests.Session = requests.Session()

    def _request(
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
        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url, headers=headers, params=params, json=data
                )
            if method.upper() == "POST":
                response = self.session.post(
                    url, headers=headers, params=params, json=data
                )
            if method.upper() == "PUT":
                response = self.session.put(
                    url, headers=headers, params=params, json=data
                )
            if method.upper() == "DELETE":
                response = self.session.delete(
                    url, headers=headers, params=params, json=data
                )
        except requests.ConnectionError:
            raise ConnectionError("Connection Refused while connecting to API.")
        except requests.Timeout:
            raise ConnectionTimeoutError("Timeout occurred while connecting to API.")

        return self._process_response(response)

    def _process_response(self, response: requests.Response) -> str | dict[str, Any]:
        """Process the response from the API

        Args:
            response (requests.Response): Response from the API

        Returns:
            str: Processed response from the API

        Raises:
            ConnectionError: If the response is not 200
            InvalidResponseError: If the API response is invalid
        """
        if response.status_code == 200:
            try:
                return response.json()
            except Exception:
                # Check if response is html
                response_content_type = response.headers.get("content-type")
                if response_content_type and "text/html" in response_content_type:
                    raise InvalidResponseError(
                        f"Invalid Response from server! Check if {self.host_url}"
                        f" is a valid API endpoint."
                    )
                return response.text
        if response.status_code == 400:
            raise ConnectionError(
                f"Bad Request, possibly a bug. {str(response.content)}"
            )
        if response.status_code == 401:
            raise ConnectionError(
                f"Unauthorized. Please ensure valid API Key is used: {self.api_key}"
            )
        if response.status_code == 403:
            raise ConnectionError(
                f"Access restricted. Please ensure API Key '{self.api_key}'"
                f" has correct permissions"
            )
        if response.status_code == 404:
            raise ConnectionError(f"Resource not found: {response.url}")
        if response.status_code == 405:
            raise ConnectionError(f"The endpoint {response.url} is not allowed")
        if response.status_code == 500:
            try:
                message = response.json().get("message", "")
                error_message = f"Internal Server Error: {message}"
            except Exception:
                if response.text:
                    error_message = f"Internal Server Error: {response.text}"
                else:
                    error_message = "Internal Server Error: Unknown Error Occurred."
            raise ConnectionError(error_message)
        if response.status_code == 502:
            raise ConnectionError(
                f"Bad Gateway. Check if your server at {response.url} is accessible."
            )
        raise ConnectionError(
            f"Invalid Host ({self.host_url}) or API Key ({self.api_key}), "
            f"not a Radarr or Sonarr instance."
        )
