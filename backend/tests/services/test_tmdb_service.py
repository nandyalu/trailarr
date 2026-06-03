"""Tests for services/tmdb_service.py."""

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from services.tmdb_service import (
    _fetch_tmdb_videos,
    _find_youtube_key,
    _get_seasons_to_fetch,
    refresh_tmdb_videos,
)


def _make_media(
    media_id: int = 1,
    tmdb_id: str = "12345",
    is_movie: bool = True,
    season_count: int = 0,
):
    return SimpleNamespace(
        id=media_id, tmdb_id=tmdb_id, is_movie=is_movie,
        title="Test", season_count=season_count,
    )


def _make_cfg(
    movie_languages=None,
    series_languages=None,
    has_season_profile=False,
):
    from db.repos.trailer_profile import TmdbRefreshConfig
    return TmdbRefreshConfig(
        movie_languages=movie_languages or [""],
        series_languages=series_languages or [""],
        has_season_profile=has_season_profile,
    )


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
    async def test_429_returns_none(self):
        mock_resp = AsyncMock()
        mock_resp.status = 429
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        result = await _fetch_tmdb_videos(mock_session, "99", is_movie=True, season=0, api_key="k")
        assert result is None

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


# ─── _get_seasons_to_fetch ───────────────────────────────────────────────────

class TestGetSeasonsToFetch:

    def test_movie_always_returns_zero_only(self):
        media = _make_media(is_movie=True, season_count=5)
        assert _get_seasons_to_fetch(media, True) == [0]
        assert _get_seasons_to_fetch(media, False) == [0]

    def test_series_no_season_profile_returns_zero_only(self):
        media = _make_media(is_movie=False, season_count=3)
        assert _get_seasons_to_fetch(media, False) == [0]

    def test_series_with_season_profile_includes_each_season(self):
        media = _make_media(is_movie=False, season_count=3)
        assert _get_seasons_to_fetch(media, True) == [0, 1, 2, 3]

    def test_series_zero_seasons_returns_zero_only(self):
        media = _make_media(is_movie=False, season_count=0)
        assert _get_seasons_to_fetch(media, True) == [0]


# ─── refresh_tmdb_videos ─────────────────────────────────────────────────────

class TestRefreshTmdbVideos:

    @pytest.mark.asyncio
    async def test_no_api_key_returns_early(self):
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.media_repo.read_all_generator") as mock_gen,
        ):
            mock_settings.tmdb_api_key = ""
            await refresh_tmdb_videos()
        mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_without_tmdb_id_skipped(self):
        media = _make_media(tmdb_id="")
        cfg = _make_cfg()
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos") as mock_fetch,
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()
        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_event_exits_loop(self):
        stop_event = threading.Event()
        stop_event.set()
        media = _make_media()
        cfg = _make_cfg()
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos") as mock_fetch,
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos(stop_event)
        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_upserts_all_youtube_results(self):
        media = _make_media()
        cfg = _make_cfg()
        results = [
            {"site": "YouTube", "type": "Trailer", "key": "yt_trailer"},
            {"site": "YouTube", "type": "Teaser", "key": "yt_teaser"},
            {"site": "Vimeo", "type": "Trailer", "key": "vimeo_skip"},
        ]
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock, return_value=results),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb") as mock_upsert,
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()
        # Vimeo result skipped; only 2 YouTube results upserted
        assert mock_upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_deduplicates_media_ids(self):
        media1 = _make_media(media_id=1)
        media1_dup = _make_media(media_id=1)
        cfg = _make_cfg()
        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media1, media1_dup])),
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock, return_value=[]) as mock_fetch,
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()
        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_movie_languages_for_movies(self):
        media = _make_media(is_movie=True)
        cfg = _make_cfg(movie_languages=["", "de"], series_languages=["", "ja"])
        fetched_langs = []

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key, language=""):
            fetched_langs.append(language)
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        assert set(fetched_langs) == {"", "de"}

    @pytest.mark.asyncio
    async def test_uses_series_languages_for_series(self):
        media = _make_media(is_movie=False)
        cfg = _make_cfg(movie_languages=["", "de"], series_languages=["", "ja"])
        fetched_langs = []

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key, language=""):
            fetched_langs.append(language)
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        assert set(fetched_langs) == {"", "ja"}

    @pytest.mark.asyncio
    async def test_no_season_calls_without_season_profile(self):
        media = _make_media(is_movie=False, season_count=3)
        cfg = _make_cfg(has_season_profile=False)
        fetch_seasons = []

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key, language=""):
            fetch_seasons.append(season)
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        assert fetch_seasons == [0]

    @pytest.mark.asyncio
    async def test_season_calls_with_season_profile(self):
        media = _make_media(is_movie=False, season_count=2)
        cfg = _make_cfg(has_season_profile=True)
        fetch_seasons = []

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key, language=""):
            fetch_seasons.append(season)
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        assert fetch_seasons == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_fetch_error_does_not_abort_run(self):
        media1 = _make_media(media_id=1)
        media2 = _make_media(media_id=2)
        cfg = _make_cfg()
        fetch_count = 0

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key, language=""):
            nonlocal fetch_count
            fetch_count += 1
            if fetch_count == 1:
                raise Exception("network error")
            return []

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media1, media2])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("asyncio.sleep"),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        assert fetch_count == 2

    @pytest.mark.asyncio
    async def test_429_triggers_backoff_and_retry(self):
        media = _make_media()
        cfg = _make_cfg()
        fetch_calls = []

        async def fake_fetch(session, tmdb_id, is_movie, season, api_key, language=""):
            fetch_calls.append(1)
            if len(fetch_calls) == 1:
                return None  # first call is 429
            return []

        sleep_calls = []

        async def fake_sleep(seconds):
            sleep_calls.append(seconds)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=fake_fetch),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("services.tmdb_service.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        # Retry attempted — two fetch calls for the same combo
        assert len(fetch_calls) == 2
        # Rate-limit sleep was triggered (>= _RATE_LIMIT_BASE = 60s)
        assert any(s >= 60 for s in sleep_calls)

    @pytest.mark.asyncio
    async def test_429_sleep_doubles_on_consecutive_hits(self):
        media1 = _make_media(media_id=1)
        media2 = _make_media(media_id=2)
        cfg = _make_cfg()

        async def always_429(session, tmdb_id, is_movie, season, api_key, language=""):
            return None

        sleep_calls = []

        async def fake_sleep(seconds):
            sleep_calls.append(seconds)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter([media1, media2])),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=always_429),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("services.tmdb_service.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        rate_limit_sleeps = sorted(s for s in sleep_calls if s >= 60)
        # Sleep doubled between first and second 429 event
        assert len(rate_limit_sleeps) >= 2
        assert rate_limit_sleeps[1] > rate_limit_sleeps[0]

    @pytest.mark.asyncio
    async def test_rate_limit_sleep_capped_at_max(self):
        from services.tmdb_service import _RATE_LIMIT_MAX
        # Create enough media items to exceed max through doubling
        items = [_make_media(media_id=i) for i in range(1, 20)]
        cfg = _make_cfg()

        async def always_429(session, tmdb_id, is_movie, season, api_key, language=""):
            return None

        sleep_calls = []

        async def fake_sleep(seconds):
            sleep_calls.append(seconds)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service.trailer_profile_repo.get_tmdb_refresh_config", return_value=cfg),
            patch("services.tmdb_service.media_repo.read_all_generator", return_value=iter(items)),
            patch("services.tmdb_service._fetch_tmdb_videos", side_effect=always_429),
            patch("services.tmdb_service.video_id_repo.upsert_tmdb"),
            patch("services.tmdb_service.asyncio.sleep", side_effect=fake_sleep),
        ):
            mock_settings.tmdb_api_key = "key"
            await refresh_tmdb_videos()

        rate_limit_sleeps = [s for s in sleep_calls if s >= 60]
        assert all(s <= _RATE_LIMIT_MAX for s in rate_limit_sleeps)
