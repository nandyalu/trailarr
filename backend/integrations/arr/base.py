from typing import Any

from exceptions import InvalidResponseError
from integrations.arr.http import AsyncRequestManager


class AsyncBaseArrManager(AsyncRequestManager):
    def __init__(self, url: str, api_key: str, version: str = ""):
        self.version = version
        super().__init__(url, api_key)

    async def api_version(self) -> str:
        response = await self._request("GET", "/api")
        if isinstance(response, dict):
            return str(response.get("current", ""))
        if isinstance(response, str):
            return response
        return ""

    async def _get_system_status(self, app_name: str) -> str:
        status = await self._request("GET", f"/api/{self.version}/system/status")
        if isinstance(status, str):
            raise InvalidResponseError(status)
        if not isinstance(status, dict):
            raise InvalidResponseError("Unknown Error")
        result_app_name = status.get("appName")
        version = status.get("version")
        if result_app_name and version:
            if str.lower(result_app_name) == app_name.lower():
                return f"{app_name} Connection Successful! Version: {version}"
        raise InvalidResponseError(
            f"Invalid Host ({self.host_url}) or API Key ({self.api_key}), not a {app_name} instance."
        )

    async def ping(self) -> str | dict[str, str] | list[dict[str, Any]]:
        return await self._request("GET", "/ping")

    async def get_rootfolders(self) -> list[str]:
        response = await self._request("GET", f"/api/{self.version}/rootfolder")
        if isinstance(response, str):
            raise InvalidResponseError(response)
        if not isinstance(response, list):
            raise InvalidResponseError(f"Unable to parse response! Response: ({response})")
        rootfolders: list[str] = []
        for rootfolder in response:
            if not isinstance(rootfolder, dict):
                raise InvalidResponseError("Response is not a dict")
            if "path" not in rootfolder:
                raise InvalidResponseError("Path not found in response")
            rootfolders.append(f"{rootfolder['path']}")
        return rootfolders
