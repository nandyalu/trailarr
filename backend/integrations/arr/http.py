from typing import Any
from urllib.parse import urlparse, urlunparse

import aiohttp

from exceptions import ConnectionTimeoutError, InvalidResponseError


class AsyncRequestManager:
    def __init__(self, host_url: str, api_key: str):
        self.host_url = host_url.rstrip("/")
        self.api_key = api_key

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: list[dict] | dict | None = None,
    ) -> str | dict[str, Any] | list[dict[str, Any]]:
        initial_url = f"{self.host_url}/{path}"
        parsed_url = urlparse(initial_url)
        fixed_path = parsed_url.path.replace("//", "/").rstrip("/")
        url = urlunparse(parsed_url._replace(path=fixed_path))
        headers = {"X-Api-Key": self.api_key}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, url, headers=headers, params=params, data=data, ssl=False
                ) as resp:
                    return await self._process_response(resp)
            except aiohttp.ServerTimeoutError:
                raise ConnectionTimeoutError("Timeout occurred while connecting to API.")
            except aiohttp.ClientConnectionError:
                raise ConnectionError("Connection Refused while connecting to API.")
            except Exception:
                raise ConnectionError("Unable to connect to API. Check your connection.")

    async def _process_response(
        self, response: aiohttp.ClientResponse
    ) -> str | dict[str, Any] | list[dict[str, Any]]:
        if response.status == 200:
            try:
                return await response.json()
            except Exception:
                ct = response.headers.get("content-type", "")
                if "text" in ct:
                    raise InvalidResponseError(
                        f"Invalid Response from server! Check if {self.host_url} is a valid API endpoint."
                    )
                return await response.text()
        if response.status == 400:
            raise ConnectionError(f"Bad Request, possibly a bug. {str(await response.text())}")
        if response.status == 401:
            raise ConnectionError(f"Unauthorized. Please ensure valid API Key is used: {self.api_key}")
        if response.status == 403:
            raise ConnectionError(f"Access restricted. Please ensure API Key '{self.api_key}' has correct permissions")
        if response.status == 404:
            raise ConnectionError(f"Resource not found: {response.url}")
        if response.status == 405:
            raise ConnectionError(f"The endpoint {response.url} is not allowed")
        if response.status == 500:
            try:
                message = (await response.json()).get("message", "")
                raise ConnectionError(f"Internal Server Error: {message}")
            except Exception:
                text = await response.text()
                raise ConnectionError(f"Internal Server Error: {text or 'Unknown Error Occurred.'}")
        if response.status == 502:
            raise ConnectionError(f"Bad Gateway. Check if your server at {response.url} is accessible.")
        raise ConnectionError(
            f"Invalid Host ({self.host_url}) or API Key ({self.api_key}), not a Radarr or Sonarr instance."
        )
