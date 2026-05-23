"""Tests for PlexAPI pagination helpers and async generators."""

import re
import pytest
from aioresponses import aioresponses
from unittest.mock import patch

from integrations.plex.client import PlexAPI


PLEX_URL = "http://plex-test"
PLEX_TOKEN = "test-token"

_MOVIE_RAW = {"ratingKey": "1", "title": "Movie One", "type": "movie"}
_LEAF_RAW = {
    "grandparentRatingKey": "99",
    "Media": [{"Part": [{"file": "/media/tv/Show/S01/E01.mkv"}]}],
}


def _make_container(items: list, total: int | None = None) -> dict:
    container: dict = {"MediaContainer": {"size": len(items), "Metadata": items}}
    if total is not None:
        container["MediaContainer"]["totalSize"] = total
    return container


@pytest.fixture
def api() -> PlexAPI:
    return PlexAPI(PLEX_URL, PLEX_TOKEN)


class TestGetTotalSize:
    @pytest.mark.asyncio
    async def test_returns_total_from_response(self, api):
        with aioresponses() as m:
            m.get(
                f"{PLEX_URL}/library/sections/1/all",
                payload={"MediaContainer": {"totalSize": 42, "size": 0}},
            )
            total = await api._get_total_size(f"{PLEX_URL}/library/sections/1/all")
        assert total == 42

    @pytest.mark.asyncio
    async def test_returns_zero_on_http_error(self, api):
        with aioresponses() as m:
            m.get(f"{PLEX_URL}/library/sections/1/all", status=500)
            total = await api._get_total_size(f"{PLEX_URL}/library/sections/1/all")
        assert total == 0

    @pytest.mark.asyncio
    async def test_returns_zero_on_network_error(self, api):
        with aioresponses() as m:
            m.get(
                f"{PLEX_URL}/library/sections/1/all",
                exception=Exception("connection refused"),
            )
            total = await api._get_total_size(f"{PLEX_URL}/library/sections/1/all")
        assert total == 0


class TestIterPages:
    @pytest.mark.asyncio
    async def test_empty_library_yields_nothing(self, api):
        url = f"{PLEX_URL}/library/sections/1/all"
        with aioresponses() as m:
            m.get(url, payload={"MediaContainer": {"totalSize": 0, "size": 0}})
            results = [item async for item in api._iter_pages(url)]
        assert results == []

    @pytest.mark.asyncio
    async def test_single_page_yields_all_items(self, api):
        url = f"{PLEX_URL}/library/sections/1/all"
        items = [_MOVIE_RAW, _MOVIE_RAW, _MOVIE_RAW]
        with aioresponses() as m:
            m.get(url, payload={"MediaContainer": {"totalSize": 3, "size": 0}})
            m.get(url, payload=_make_container(items))
            results = [item async for item in api._iter_pages(url, page_size=500)]
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_multiple_pages_yields_all_items(self, api):
        url = f"{PLEX_URL}/library/sections/1/all"
        page1 = [{"ratingKey": str(i)} for i in range(3)]
        page2 = [{"ratingKey": str(i)} for i in range(3, 5)]
        with aioresponses() as m:
            m.get(url, payload={"MediaContainer": {"totalSize": 5, "size": 0}})
            m.get(url, payload=_make_container(page1))
            m.get(url, payload=_make_container(page2))
            results = [item async for item in api._iter_pages(url, page_size=3)]
        assert len(results) == 5
        assert results[0]["ratingKey"] == "0"
        assert results[4]["ratingKey"] == "4"

    @pytest.mark.asyncio
    async def test_stops_early_on_empty_page(self, api):
        url = f"{PLEX_URL}/library/sections/1/all"
        with aioresponses() as m:
            m.get(url, payload={"MediaContainer": {"totalSize": 10, "size": 0}})
            m.get(url, payload=_make_container([]))
            results = [item async for item in api._iter_pages(url, page_size=500)]
        assert results == []

    @pytest.mark.asyncio
    async def test_raises_connection_error_on_401(self, api):
        url = f"{PLEX_URL}/library/sections/1/all"
        with aioresponses() as m:
            m.get(url, payload={"MediaContainer": {"totalSize": 1, "size": 0}})
            m.get(url, status=401)
            with pytest.raises(ConnectionError, match="authentication failed"):
                async for _ in api._iter_pages(url):
                    pass

    @pytest.mark.asyncio
    async def test_raises_connection_error_on_http_error(self, api):
        url = f"{PLEX_URL}/library/sections/1/all"
        with aioresponses() as m:
            m.get(url, payload={"MediaContainer": {"totalSize": 1, "size": 0}})
            m.get(url, status=503, body="Service Unavailable")
            with pytest.raises(ConnectionError, match="503"):
                async for _ in api._iter_pages(url):
                    pass


class TestGetLibraryMedia:
    @pytest.mark.asyncio
    async def test_yields_plex_media_items(self, api):
        from integrations.plex.models import PlexMediaItem

        pattern = re.compile(r".*/library/sections/1/all.*")
        with aioresponses() as m:
            m.get(pattern, payload={"MediaContainer": {"totalSize": 1, "size": 0}})
            m.get(pattern, payload=_make_container([_MOVIE_RAW]))
            results = [item async for item in api.get_library_media(1)]
        assert len(results) == 1
        assert isinstance(results[0], PlexMediaItem)
        assert results[0].title == "Movie One"

    @pytest.mark.asyncio
    @patch.object(PlexAPI, "_iter_pages")
    async def test_url_contains_include_guids(self, mock_iter, api):
        async def _empty():
            return
            yield

        mock_iter.return_value = _empty()
        async for _ in api.get_library_media(1):
            pass
        called_url: str = mock_iter.call_args[0][0]
        assert "includeGuids=1" in called_url

    @pytest.mark.asyncio
    @patch.object(PlexAPI, "_iter_pages")
    async def test_url_contains_exclude_fields(self, mock_iter, api):
        async def _empty():
            return
            yield

        mock_iter.return_value = _empty()
        async for _ in api.get_library_media(1):
            pass
        called_url: str = mock_iter.call_args[0][0]
        assert "excludeFields=" in called_url

    @pytest.mark.asyncio
    @patch.object(PlexAPI, "_iter_pages")
    async def test_url_does_not_include_include_details(self, mock_iter, api):
        async def _empty():
            return
            yield

        mock_iter.return_value = _empty()
        async for _ in api.get_library_media(1):
            pass
        called_url: str = mock_iter.call_args[0][0]
        assert "includeDetails" not in called_url


class TestGetLibraryLeaves:
    @pytest.mark.asyncio
    async def test_yields_plex_episode_leaves(self, api):
        from integrations.plex.models import PlexEpisodeLeaf

        pattern = re.compile(r".*/library/sections/3/allLeaves.*")
        with aioresponses() as m:
            m.get(pattern, payload={"MediaContainer": {"totalSize": 1, "size": 0}})
            m.get(pattern, payload=_make_container([_LEAF_RAW]))
            results = [item async for item in api.get_library_leaves(3)]
        assert len(results) == 1
        assert isinstance(results[0], PlexEpisodeLeaf)
        assert results[0].grandparentRatingKey == "99"
        assert results[0].media_folder == "/media/tv/Show/S01"

    @pytest.mark.asyncio
    @patch.object(PlexAPI, "_iter_pages")
    async def test_url_contains_exclude_fields(self, mock_iter, api):
        async def _empty():
            return
            yield

        mock_iter.return_value = _empty()
        async for _ in api.get_library_leaves(3):
            pass
        called_url: str = mock_iter.call_args[0][0]
        assert "excludeFields=" in called_url
        assert "allLeaves" in called_url

    @pytest.mark.asyncio
    async def test_yields_nothing_for_empty_section(self, api):
        url_prefix = f"{PLEX_URL}/library/sections/3/allLeaves"
        with aioresponses() as m:
            m.get(url_prefix, payload={"MediaContainer": {"totalSize": 0, "size": 0}})
            results = [item async for item in api.get_library_leaves(3)]
        assert results == []
