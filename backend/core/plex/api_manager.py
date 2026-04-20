from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import urlencode

import aiohttp

from app_logger import ModuleLogger
from core.plex.models import (
    PlexEpisodeLeaf,
    PlexLibrarySection,
    PlexMediaExtra,
    PlexMediaItem,
)

logger = ModuleLogger("PlexAPI")

_PAGE_SIZE = 500

# Scalar fields not used by PlexMediaItem — excluded to trim response payload
_MEDIA_EXCLUDE_FIELDS = (
    "titleSort,rating,audienceRating,audienceRatingImage,"
    "contentRating,contentRatingAge,viewCount,lastViewedAt,"
    "leafCount,viewedLeafCount,childCount,primaryExtraKey,theme,index"
)

# For allLeaves we only need grandparentRatingKey + Media[0].Part[0].file
# (~51% payload reduction confirmed against live server)
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
    """Async HTTP client for the Plex Media Server API."""

    def __init__(
        self, server_url: str, token: str, identifier: str = "trailarr"
    ):
        if not server_url.startswith(("http://", "https://")):
            server_url = f"http://{server_url}"
        if server_url.endswith("/"):
            server_url = server_url[:-1]
        self.server_url = server_url
        self.identifier = identifier
        self.token = token
        self.headers = {
            "Accept": "application/json",
            "X-Plex-Token": token,
            "X-Plex-Client-Identifier": identifier,
        }

    async def get_query_json(
        self, url: str, method: str = "GET"
    ) -> dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=self.headers, ssl=False
                ) as response:
                    if response.status == 401:
                        raise ConnectionError(
                            "Plex authentication failed — invalid token"
                        )
                    if response.status != 200:
                        error_text = await response.text()
                        raise ConnectionError(
                            f"Plex returned {response.status}: {error_text}"
                        )
                    data: dict[str, Any] = await response.json()
                    return data.get("MediaContainer", {})
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Network error reaching Plex: {e}") from e
        except (ValueError, aiohttp.ContentTypeError) as e:
            raise ValueError(f"Failed to parse Plex JSON response: {e}") from e

    async def _get_total_size(self, url: str) -> int:
        """Return the total number of items at *url* via a size=0 preflight."""
        preflight_headers = {
            **self.headers,
            "X-Plex-Container-Start": "0",
            "X-Plex-Container-Size": "0",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    "GET", url, headers=preflight_headers, ssl=False
                ) as response:
                    if response.status != 200:
                        return 0
                    data: dict[str, Any] = await response.json()
                    return data.get("MediaContainer", {}).get("totalSize", 0)
        except Exception:
            return 0

    async def _iter_pages(
        self, url: str, page_size: int = _PAGE_SIZE
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yield raw metadata dicts from *url*, fetching one page at a time."""
        total = await self._get_total_size(url)
        if total == 0:
            return

        offset = 0
        while offset < total:
            page_headers = {
                **self.headers,
                "X-Plex-Container-Start": str(offset),
                "X-Plex-Container-Size": str(page_size),
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        "GET", url, headers=page_headers, ssl=False
                    ) as response:
                        if response.status == 401:
                            raise ConnectionError(
                                "Plex authentication failed — invalid token"
                            )
                        if response.status != 200:
                            error_text = await response.text()
                            raise ConnectionError(
                                f"Plex returned {response.status}: {error_text}"
                            )
                        data: dict[str, Any] = await response.json()
                        items: list[dict[str, Any]] = (
                            data.get("MediaContainer", {}).get("Metadata", [])
                        )
            except aiohttp.ClientError as e:
                raise ConnectionError(
                    f"Network error reaching Plex: {e}"
                ) from e
            except (ValueError, aiohttp.ContentTypeError) as e:
                raise ValueError(
                    f"Failed to parse Plex JSON response: {e}"
                ) from e

            if not items:
                break
            for item in items:
                yield item
            offset += page_size

    async def get_system_status(self) -> str:
        """Validate token and return a status string with the Plex version."""
        url = f"{self.server_url}/"
        data = await self.get_query_json(url)
        version = data.get("version", "unknown")
        return f"Connected to Plex Media Server v{version}"

    async def get_machine_identifier(self) -> str:
        """Return the Plex server's unique machine identifier."""
        url = f"{self.server_url}/"
        data = await self.get_query_json(url)
        return data.get("machineIdentifier", "")

    async def validate_token(self) -> bool:
        """Return True if the token is valid, False otherwise."""
        try:
            await self.get_system_status()
            return True
        except Exception as e:
            logger.debug(f"Failed to validate Plex token: {e}")
            return False

    async def get_libraries(self) -> list[PlexLibrarySection]:
        """Return all library sections from the Plex server."""
        url = f"{self.server_url}/library/sections"
        data = await self.get_query_json(url)
        libraries_raw = data.get("Directory", [])
        libraries = [PlexLibrarySection(**lib) for lib in libraries_raw]
        logger.debug(f"Retrieved {len(libraries)} library sections")
        return libraries

    async def get_library_folders(self) -> list[str]:
        """Return all root folder paths across all library sections."""
        libraries = await self.get_libraries()
        folders: list[str] = []
        for lib in libraries:
            folders.extend(lib.folders)
        logger.debug(f"Retrieved {len(folders)} library folders")
        return folders

    async def get_library_media(
        self, section_key: str | int
    ) -> AsyncGenerator[PlexMediaItem, None]:
        """Yield all media items from a library section, one page at a time.

        Uses excludeFields to strip unused scalar attributes and paginates
        in chunks of _PAGE_SIZE to avoid loading the entire library at once.
        """
        url = (
            f"{self.server_url}/library/sections/{section_key}/all"
            f"?includeGuids=1&excludeFields={_MEDIA_EXCLUDE_FIELDS}"
        )
        count = 0
        async for raw in self._iter_pages(url):
            count += 1
            yield PlexMediaItem(**raw)
        logger.debug(
            f"Yielded {count} items from section {section_key}"
        )

    async def get_library_leaves(
        self, section_key: str | int
    ) -> AsyncGenerator[PlexEpisodeLeaf, None]:
        """Yield all episode leaves from a show section, one page at a time.

        Uses excludeFields to strip all unused scalars (~51% payload reduction)
        since only grandparentRatingKey and Media[0].Part[0].file are needed.
        """
        url = (
            f"{self.server_url}/library/sections/{section_key}/allLeaves"
            f"?excludeFields={_LEAF_EXCLUDE_FIELDS}"
        )
        count = 0
        async for raw in self._iter_pages(url):
            count += 1
            yield PlexEpisodeLeaf(**raw)
        logger.debug(
            f"Yielded {count} leaf items from section {section_key}"
        )

    async def get_library_item_details(
        self, rating_key: str | int
    ) -> PlexMediaItem:
        """Return detailed metadata for a single media item."""
        url = (
            f"{self.server_url}/library/metadata/{rating_key}?includeExtras=1"
        )
        data = await self.get_query_json(url)
        items_raw = data.get("Metadata", [])
        return PlexMediaItem(**items_raw[0])

    async def get_library_item_extras(
        self, rating_key: str | int
    ) -> list[PlexMediaExtra]:
        """Return all extras (trailers, featurettes, etc.) for a media item."""
        url = f"{self.server_url}/library/metadata/{rating_key}/extras"
        data = await self.get_query_json(url)
        extras_raw = data.get("Metadata", [])
        return [PlexMediaExtra(**item) for item in extras_raw]

    async def add_library_item_extra(
        self, rating_key: str | int, url: str, title: str
    ) -> bool:
        """Add a trailer/extra URL to a Plex media item. Returns True on success."""
        params = urlencode({"extraType": 1, "url": url, "title": title})
        api_url = (
            f"{self.server_url}/library/metadata/{rating_key}/extras?{params}"
        )
        try:
            await self.get_query_json(api_url, method="POST")
            logger.debug(f"Added extra '{title}' to item {rating_key}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to add extra '{title}' to item {rating_key}: {e}"
            )
            return False

    async def refresh_item(self, rating_key: str | int) -> bool:
        """Trigger a targeted metadata refresh for a single item."""
        url = f"{self.server_url}/library/metadata/{rating_key}/refresh"
        try:
            await self.get_query_json(url, method="PUT")
            logger.debug(f"Triggered refresh for item {rating_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh item {rating_key}: {e}")
            return False

    async def refresh_section(self, section_key: str | int) -> bool:
        """Trigger a library section scan."""
        url = f"{self.server_url}/library/sections/{section_key}/refresh"
        try:
            await self.get_query_json(url, method="GET")
            logger.debug(f"Triggered refresh for section {section_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh section {section_key}: {e}")
            return False

    async def scan_section_path(
        self, section_key: str | int, path: str
    ) -> bool:
        """Trigger a targeted file-system scan for a specific folder path.

        Tells Plex to scan only the given directory within the library section,
        picking up newly added, changed, or removed files without scanning the
        entire library.

        Args:
            section_key: The Plex library section id.
            path: The Plex-side folder path to scan (after reversing path mappings).
        """
        params = urlencode({"path": path})
        url = f"{self.server_url}/library/sections/{section_key}/refresh?{params}"
        try:
            await self.get_query_json(url, method="GET")
            logger.debug(
                f"Triggered path scan for section {section_key}, path '{path}'"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to scan path '{path}' in section {section_key}: {e}"
            )
            return False
