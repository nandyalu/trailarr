from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import urlencode

import aiohttp

from app_logger import ModuleLogger
from integrations.plex.models import PlexEpisodeLeaf, PlexLibrarySection, PlexMediaExtra, PlexMediaItem

logger = ModuleLogger("PlexAPI")

_PAGE_SIZE = 500
_MEDIA_EXCLUDE_FIELDS = (
    "titleSort,rating,audienceRating,audienceRatingImage,"
    "contentRating,contentRatingAge,viewCount,lastViewedAt,"
    "leafCount,viewedLeafCount,childCount,primaryExtraKey,theme,index"
)
_LEAF_EXCLUDE_FIELDS = (
    "guid,parentGuid,grandparentGuid,grandparentSlug,type,title,"
    "grandparentKey,parentKey,grandparentTitle,parentTitle,"
    "contentRating,summary,index,parentIndex,audienceRating,"
    "viewCount,lastViewedAt,year,thumb,art,parentThumb,"
    "grandparentThumb,grandparentArt,grandparentTheme,"
    "duration,originallyAvailableAt,addedAt,audienceRatingImage,"
    "key,ratingKey,parentRatingKey"
)


class PlexAPI:
    def __init__(self, server_url: str, token: str, identifier: str = "trailarr"):
        if not server_url.startswith(("http://", "https://")):
            server_url = f"http://{server_url}"
        self.server_url = server_url.rstrip("/")
        self.identifier = identifier
        self.token = token
        self.headers = {
            "Accept": "application/json",
            "X-Plex-Token": token,
            "X-Plex-Client-Identifier": identifier,
        }

    async def get_query_json(self, url: str, method: str = "GET") -> dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=self.headers, ssl=False) as response:
                    if response.status == 401:
                        raise ConnectionError("Plex authentication failed — invalid token")
                    if response.status != 200:
                        raise ConnectionError(f"Plex returned {response.status}: {await response.text()}")
                    data: dict[str, Any] = await response.json()
                    return data.get("MediaContainer", {})
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Network error reaching Plex: {e}") from e
        except (ValueError, aiohttp.ContentTypeError) as e:
            raise ValueError(f"Failed to parse Plex JSON response: {e}") from e

    async def _get_total_size(self, url: str) -> int:
        preflight_headers = {**self.headers, "X-Plex-Container-Start": "0", "X-Plex-Container-Size": "0"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request("GET", url, headers=preflight_headers, ssl=False) as response:
                    if response.status != 200:
                        return 0
                    data: dict[str, Any] = await response.json()
                    return data.get("MediaContainer", {}).get("totalSize", 0)
        except Exception:
            return 0

    async def _iter_pages(self, url: str, page_size: int = _PAGE_SIZE) -> AsyncGenerator[dict[str, Any], None]:
        total = await self._get_total_size(url)
        if total == 0:
            return
        offset = 0
        while offset < total:
            page_headers = {**self.headers, "X-Plex-Container-Start": str(offset), "X-Plex-Container-Size": str(page_size)}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request("GET", url, headers=page_headers, ssl=False) as response:
                        if response.status == 401:
                            raise ConnectionError("Plex authentication failed — invalid token")
                        if response.status != 200:
                            raise ConnectionError(f"Plex returned {response.status}: {await response.text()}")
                        data: dict[str, Any] = await response.json()
                        items: list[dict[str, Any]] = data.get("MediaContainer", {}).get("Metadata", [])
            except aiohttp.ClientError as e:
                raise ConnectionError(f"Network error reaching Plex: {e}") from e
            if not items:
                break
            for item in items:
                yield item
            offset += page_size

    async def get_system_status(self) -> str:
        data = await self.get_query_json(f"{self.server_url}/")
        version = data.get("version", "unknown")
        return f"Connected to Plex Media Server v{version}"

    async def get_machine_identifier(self) -> str:
        data = await self.get_query_json(f"{self.server_url}/")
        return data.get("machineIdentifier", "")

    async def validate_token(self) -> bool:
        try:
            await self.get_system_status()
            return True
        except Exception:
            return False

    async def get_libraries(self) -> list[PlexLibrarySection]:
        data = await self.get_query_json(f"{self.server_url}/library/sections")
        return [PlexLibrarySection(**lib) for lib in data.get("Directory", [])]

    async def get_library_folders(self) -> list[str]:
        libraries = await self.get_libraries()
        folders: list[str] = []
        for lib in libraries:
            folders.extend(lib.folders)
        return folders

    async def get_library_media(self, section_key: str | int) -> AsyncGenerator[PlexMediaItem, None]:
        url = (
            f"{self.server_url}/library/sections/{section_key}/all"
            f"?includeGuids=1&excludeFields={_MEDIA_EXCLUDE_FIELDS}"
        )
        async for raw in self._iter_pages(url):
            yield PlexMediaItem(**raw)

    async def get_library_leaves(self, section_key: str | int) -> AsyncGenerator[PlexEpisodeLeaf, None]:
        url = (
            f"{self.server_url}/library/sections/{section_key}/allLeaves"
            f"?excludeFields={_LEAF_EXCLUDE_FIELDS}"
        )
        async for raw in self._iter_pages(url):
            yield PlexEpisodeLeaf(**raw)

    async def get_library_item_details(self, rating_key: str | int) -> PlexMediaItem:
        data = await self.get_query_json(f"{self.server_url}/library/metadata/{rating_key}?includeExtras=1")
        return PlexMediaItem(**data.get("Metadata", [])[0])

    async def get_library_item_extras(self, rating_key: str | int) -> list[PlexMediaExtra]:
        data = await self.get_query_json(f"{self.server_url}/library/metadata/{rating_key}/extras")
        return [PlexMediaExtra(**item) for item in data.get("Metadata", [])]

    async def add_library_item_extra(self, rating_key: str | int, url: str, title: str) -> bool:
        params = urlencode({"extraType": 1, "url": url, "title": title})
        api_url = f"{self.server_url}/library/metadata/{rating_key}/extras?{params}"
        try:
            await self.get_query_json(api_url, method="POST")
            return True
        except Exception as e:
            logger.error(f"Failed to add extra '{title}' to item {rating_key}: {e}")
            return False

    async def refresh_item(self, rating_key: str | int) -> bool:
        try:
            await self.get_query_json(f"{self.server_url}/library/metadata/{rating_key}/refresh", method="PUT")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh item {rating_key}: {e}")
            return False

    async def refresh_section(self, section_key: str | int) -> bool:
        try:
            await self.get_query_json(f"{self.server_url}/library/sections/{section_key}/refresh", method="GET")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh section {section_key}: {e}")
            return False

    async def scan_section_path(self, section_key: str | int, path: str) -> bool:
        params = urlencode({"path": path})
        url = f"{self.server_url}/library/sections/{section_key}/refresh?{params}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, ssl=False) as resp:
                    if resp.status == 401:
                        raise ConnectionError("Plex authentication failed — invalid token")
                    if resp.status not in (200, 204):
                        raise ConnectionError(f"Plex returned {resp.status}: {await resp.text()}")
            return True
        except Exception as e:
            logger.error(f"Failed to scan path '{path}' in section {section_key}: {e}")
            return False
