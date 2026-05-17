"""Comprehensive tests for services/tmdb_service.py."""

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from db.models.mediatrailerstatus import TrailerStatusEnum
from db.models.trailerprofile import VideoType
from services.tmdb_service import _fetch_tmdb_videos, _find_youtube_key, refresh_tmdb_videos


def _make_pending_row(
    row_id: int = 1,
    media_id: int = 1,
    profile_id: int = 1,
    season: int = 0,
    video_type: str = VideoType.TRAILER,
    status: TrailerStatusEnum = TrailerStatusEnum.PENDING,
):
    from db.repos.trailer_status import TmdbPendingRow
    return TmdbPendingRow(
        row_id=row_id,
        media_id=media_id,
        profile_id=profile_id,
        season=season,
        video_type=video_type,
        status=status,
    )


def _make_media(media_id: int = 1, txdb_id: str = "12345", is_movie: bool = True):
    return SimpleNamespace(id=media_id, txdb_id=txdb_id, is_movie=is_movie, title="Test")


# ─── _find_youtube_key ────────────────────────────────────────────────────────

class TestFindYoutubeKey:

    def test_finds_matching_trailer(self):
        results = [{"site": "YouTube", "type": "Trailer", "key": "abc123"}]
        assert _find_youtube_key(results, "Trailer") == "abc123"

    def test_case_insensitive_site_and_type(self):
        results = [{"site": "youtube", "type": "trailer", "key": "xyz"}]
        assert _find_youtube_key(results, "Trailer") == "xyz"

    def test_ignores_wrong_type(self):
        results = [{"site": "YouTube", "type": "Teaser", "key": "k1"}]
        assert _find_youtube_key(results, "Trailer") is None

    def test_ignores_non_youtube_site(self):
        results = [{"site": "Vimeo", "type": "Trailer", "key": "k2"}]
        assert _find_youtube_key(results, "Trailer") is None

    def test_returns_first_match(self):
        results = [
            {"site": "YouTube", "type": "Trailer", "key": "first"},
            {"site": "YouTube", "type": "Trailer", "key": "second"},
        ]
        assert _find_youtube_key(results, "Trailer") == "first"

    def test_empty_results_returns_none(self):
        assert _find_youtube_key([], "Trailer") is None

    def test_missing_fields_returns_none(self):
        results = [{"site": "YouTube"}]
        assert _find_youtube_key(results, "Trailer") is None

    def test_finds_teaser_type(self):
        results = [
            {"site": "YouTube", "type": "Trailer", "key": "t"},
            {"site": "YouTube", "type": "Teaser", "key": "ts"},
        ]
        assert _find_youtube_key(results, "Teaser") == "ts"


# ─── _fetch_tmdb_videos ──────────────────────────────────────────────────────

class TestFetchTmdbVideos:

    @pytest.mark.asyncio
    async def test_movie_uses_movie_url(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"results": [{"site": "YouTube", "type": "Trailer", "key": "k"}]})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        results = await _fetch_tmdb_videos(mock_session, "99", is_movie=True, season=0, api_key="key")

        url_used = mock_session.get.call_args[0][0]
        assert "/movie/99/videos" in url_used
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_tv_show_uses_tv_url(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"results": []})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        await _fetch_tmdb_videos(mock_session, "55", is_movie=False, season=0, api_key="k")

        url_used = mock_session.get.call_args[0][0]
        assert "/tv/55/videos" in url_used

    @pytest.mark.asyncio
    async def test_tv_season_uses_season_url(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"results": []})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        await _fetch_tmdb_videos(mock_session, "55", is_movie=False, season=2, api_key="k")

        url_used = mock_session.get.call_args[0][0]
        assert "/tv/55/season/2/videos" in url_used

    @pytest.mark.asyncio
    async def test_404_returns_empty_list(self):
        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        result = await _fetch_tmdb_videos(mock_session, "99", is_movie=True, season=0, api_key="k")
        assert result == []

    @pytest.mark.asyncio
    async def test_non_200_returns_empty_list(self):
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        result = await _fetch_tmdb_videos(mock_session, "99", is_movie=True, season=0, api_key="k")
        assert result == []

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_list(self):
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=asyncio.TimeoutError())

        result = await _fetch_tmdb_videos(mock_session, "99", is_movie=True, season=0, api_key="k")
        assert result == []

    @pytest.mark.asyncio
    async def test_client_error_returns_empty_list(self):
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("connection refused"))

        result = await _fetch_tmdb_videos(mock_session, "99", is_movie=True, season=0, api_key="k")
        assert result == []


# ─── refresh_tmdb_videos ─────────────────────────────────────────────────────

class TestRefreshTmdbVideos:

    @pytest.mark.asyncio
    async def test_no_api_key_returns_early(self):
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh") as mock_rows,
        ):
            mock_settings.tmdb_api_key = ""
            await refresh_tmdb_videos()

        mock_rows.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_rows_returns_early(self):
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[]),
            patch("services.tmdb_service.media_repo.read") as mock_read,
        ):
            mock_settings.tmdb_api_key = "key123"
            await refresh_tmdb_videos()

        mock_read.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_event_exits_loop(self):
        stop_event = threading.Event()
        stop_event.set()

        row = _make_pending_row(media_id=1)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row]),
            patch("services.tmdb_service.media_repo.read") as mock_read,
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos(stop_event)

        mock_read.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_not_found_increments_errors(self):
        row = _make_pending_row(media_id=99)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row]),
            patch("services.tmdb_service.media_repo.read", return_value=None),
            patch("services.tmdb_service._fetch_tmdb_videos") as mock_fetch,
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_without_txdb_id_skipped(self):
        row = _make_pending_row(media_id=1)
        media = _make_media(txdb_id=None)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row]),
            patch("services.tmdb_service.media_repo.read", return_value=media),
            patch("services.tmdb_service._fetch_tmdb_videos") as mock_fetch,
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_trailer_type_with_yt_key_updates_ytid(self):
        row = _make_pending_row(video_type=VideoType.TRAILER, status=TrailerStatusEnum.PENDING)
        media = _make_media()

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row]),
            patch("services.tmdb_service.media_repo.read", return_value=media),
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock,
                  return_value=[{"site": "YouTube", "type": "Trailer", "key": "yt_key_abc"}]),
            patch("services.tmdb_service.media_repo.update_ytid") as mock_ytid,
            patch("services.tmdb_service.trailer_status_repo.update_row_status") as mock_status,
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        mock_ytid.assert_called_once_with(1, "yt_key_abc")
        mock_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_trailer_not_available_becomes_pending_when_results_found(self):
        row = _make_pending_row(
            video_type=VideoType.TEASER,
            status=TrailerStatusEnum.NOT_AVAILABLE,
        )
        media = _make_media()

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row]),
            patch("services.tmdb_service.media_repo.read", return_value=media),
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock,
                  return_value=[{"site": "YouTube", "type": "Teaser", "key": "ts_key"}]),
            patch("services.tmdb_service.trailer_status_repo.update_row_status") as mock_status,
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        mock_status.assert_called_once_with(row.row_id, TrailerStatusEnum.PENDING)

    @pytest.mark.asyncio
    async def test_non_trailer_pending_becomes_not_available_when_no_results(self):
        row = _make_pending_row(
            video_type=VideoType.TEASER,
            status=TrailerStatusEnum.PENDING,
        )
        media = _make_media()

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row]),
            patch("services.tmdb_service.media_repo.read", return_value=media),
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock, return_value=[]),
            patch("services.tmdb_service.trailer_status_repo.update_row_status") as mock_status,
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        mock_status.assert_called_once_with(row.row_id, TrailerStatusEnum.NOT_AVAILABLE)

    @pytest.mark.asyncio
    async def test_fetch_error_does_not_abort_run(self):
        row1 = _make_pending_row(row_id=1, media_id=1)
        row2 = _make_pending_row(row_id=2, media_id=2)
        media1 = _make_media(media_id=1)
        media2 = _make_media(media_id=2)

        def fake_read(media_id):
            return {1: media1, 2: media2}[media_id]

        fetch_call_count = 0

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key):
            nonlocal fetch_call_count
            fetch_call_count += 1
            if tmdb_id == "12345" and fetch_call_count == 1:
                raise Exception("network error")
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row1, row2]),
            patch("services.tmdb_service.media_repo.read", side_effect=fake_read),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.trailer_status_repo.update_row_status"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        # Both media items were processed (even if first had an error)
        assert fetch_call_count == 2

    @pytest.mark.asyncio
    async def test_groups_rows_by_media_and_season(self):
        row1 = _make_pending_row(row_id=1, media_id=1, season=0, video_type=VideoType.TRAILER)
        row2 = _make_pending_row(row_id=2, media_id=1, season=0, video_type=VideoType.TEASER, status=TrailerStatusEnum.NOT_AVAILABLE)
        media = _make_media()
        fetch_calls = []

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key):
            fetch_calls.append((tmdb_id, season))
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_status_repo.get_pending_for_tmdb_refresh", return_value=[row1, row2]),
            patch("services.tmdb_service.media_repo.read", return_value=media),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.trailer_status_repo.update_row_status"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        # Only one fetch for media_id=1, season=0 (both rows share the same group)
        assert len(fetch_calls) == 1
