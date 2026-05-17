"""Comprehensive tests for services/image_service.py."""

import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.image_service import refresh_images, _refresh_for_type


def _make_media(
    media_id: int = 1,
    poster_url: str = "http://img/poster.jpg",
    poster_path: str = "/app/posters/1.jpg",
    fanart_url: str = "http://img/fanart.jpg",
    fanart_path: str = "/app/posters/1f.jpg",
    plex_connection_id: int | None = None,
):
    return SimpleNamespace(
        id=media_id,
        poster_url=poster_url,
        poster_path=poster_path,
        fanart_url=fanart_url,
        fanart_path=fanart_path,
        plex_connection_id=plex_connection_id,
    )


class TestRefreshImages:

    @pytest.mark.asyncio
    async def test_calls_refresh_for_both_movies_and_series(self):
        with patch("services.image_service._refresh_for_type", new_callable=AsyncMock) as mock_refresh:
            await refresh_images()

        assert mock_refresh.call_count == 2
        call_args = [c.kwargs["is_movie"] for c in mock_refresh.call_args_list]
        assert True in call_args
        assert False in call_args

    @pytest.mark.asyncio
    async def test_passes_recent_only_flag(self):
        with patch("services.image_service._refresh_for_type", new_callable=AsyncMock) as mock_refresh:
            await refresh_images(recent_only=True)

        for c in mock_refresh.call_args_list:
            assert c.kwargs["recent_only"] is True

    @pytest.mark.asyncio
    async def test_passes_stop_event(self):
        stop = threading.Event()
        with patch("services.image_service._refresh_for_type", new_callable=AsyncMock) as mock_refresh:
            await refresh_images(_stop_event=stop)

        for c in mock_refresh.call_args_list:
            assert c.kwargs["_stop_event"] is stop


class TestRefreshForType:

    @pytest.mark.asyncio
    async def test_recent_only_uses_read_recent(self):
        media = _make_media()
        with (
            patch("services.image_service.media_repo.read_recent", return_value=[media]) as mock_recent,
            patch("services.image_service.media_repo.read_all_generator") as mock_all,
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock),
        ):
            await _refresh_for_type(is_movie=True, recent_only=True)

        mock_recent.assert_called_once_with(movies_only=True)
        mock_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_recent_uses_read_all_generator(self):
        media = _make_media()
        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]) as mock_all,
            patch("services.image_service.media_repo.read_recent") as mock_recent,
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock),
        ):
            await _refresh_for_type(is_movie=False, recent_only=False)

        mock_all.assert_called_once_with(movies_only=False)
        mock_recent.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_event_exits_before_building_list(self):
        stop = threading.Event()
        stop.set()
        media = _make_media()

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]),
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock) as mock_refresh,
        ):
            await _refresh_for_type(is_movie=True, _stop_event=stop)

        # stop event is checked at the start of each media iteration — the function
        # returns early without ever calling refresh_media_images
        mock_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_plex_media_includes_auth_header(self):
        media = _make_media(plex_connection_id=5)
        mock_conn = SimpleNamespace(api_key="plex-token-xyz", id=5)

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]),
            patch("services.image_service.connection_repo.read", return_value=mock_conn),
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock) as mock_refresh,
        ):
            await _refresh_for_type(is_movie=True)

        media_image_list = mock_refresh.call_args[0][1]
        for img in media_image_list:
            assert img.headers == {"X-Plex-Token": "plex-token-xyz"}

    @pytest.mark.asyncio
    async def test_plex_token_cached_across_media_items(self):
        media1 = _make_media(media_id=1, plex_connection_id=5)
        media2 = _make_media(media_id=2, plex_connection_id=5)
        mock_conn = SimpleNamespace(api_key="token", id=5)

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media1, media2]),
            patch("services.image_service.connection_repo.read", return_value=mock_conn) as mock_read_conn,
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock),
        ):
            await _refresh_for_type(is_movie=True)

        # Token should be fetched only once (cached)
        mock_read_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_plex_connection_error_results_in_no_headers(self):
        media = _make_media(plex_connection_id=9)

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]),
            patch("services.image_service.connection_repo.read", side_effect=Exception("not found")),
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock) as mock_refresh,
        ):
            await _refresh_for_type(is_movie=True)

        media_image_list = mock_refresh.call_args[0][1]
        for img in media_image_list:
            assert img.headers is None

    @pytest.mark.asyncio
    async def test_non_plex_media_has_no_headers(self):
        media = _make_media(plex_connection_id=None)

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]),
            patch("services.image_service.connection_repo.read") as mock_read_conn,
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock) as mock_refresh,
        ):
            await _refresh_for_type(is_movie=True)

        mock_read_conn.assert_not_called()
        media_image_list = mock_refresh.call_args[0][1]
        for img in media_image_list:
            assert img.headers is None

    @pytest.mark.asyncio
    async def test_two_images_per_media_item(self):
        media = _make_media()

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]),
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock) as mock_refresh,
        ):
            await _refresh_for_type(is_movie=True)

        media_image_list = mock_refresh.call_args[0][1]
        assert len(media_image_list) == 2
        assert any(img.is_poster for img in media_image_list)
        assert any(not img.is_poster for img in media_image_list)

    @pytest.mark.asyncio
    async def test_passes_empty_token_when_plex_api_key_is_empty(self):
        media = _make_media(plex_connection_id=3)
        mock_conn = SimpleNamespace(api_key="", id=3)

        with (
            patch("services.image_service.media_repo.read_all_generator", return_value=[media]),
            patch("services.image_service.connection_repo.read", return_value=mock_conn),
            patch("services.image_service.refresh_media_images", new_callable=AsyncMock) as mock_refresh,
        ):
            await _refresh_for_type(is_movie=True)

        # Empty token → no headers (falsy token skips plex_headers assignment)
        media_image_list = mock_refresh.call_args[0][1]
        for img in media_image_list:
            assert img.headers is None
