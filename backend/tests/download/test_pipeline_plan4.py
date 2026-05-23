"""Tests for download/pipeline.py and related modules — Plan 4 coverage.

4a: season/sequence propagated into download_trailer and call sites
4b: TMDB-first for non-trailer video types; YouTube search for trailers
4c: get_tmdb_youtube_key helper in tmdb_service
4d: template variables {season}, {sequence}, {video_type} in search/filename
"""

import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from db.models.media import MediaRead
from db.models.mediatrailerstatus import TrailerStatusEnum
from db.models.trailerprofile import VideoType
from download.pipeline import download_trailer


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_media(**kwargs) -> MediaRead:
    defaults = dict(
        id=1, connection_id=1, arr_id=1, is_movie=True,
        title="Test Movie", clean_title="test movie", year=2024,
        language="en", studio="Studio", txdb_id="12345", title_slug="test-movie",
        monitor=True, arr_monitored=True, media_exists=False, media_filename="",
        season_count=0, runtime=120,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        downloaded_at=None, folder_path="/media/test",
    )
    defaults.update(kwargs)
    return MediaRead(**defaults)


def _make_profile(video_type: VideoType = VideoType.TRAILER) -> MagicMock:
    p = MagicMock()
    p.id = 1
    p.video_type = video_type
    p.customfilter.filter_name = "Test"
    p.always_search = False
    p.skip_if_plex_trailer = False
    p.remove_silence = False
    p.stop_monitoring = False
    p.notify_plex = False
    p.retry_count = 0
    p.tmdb_language = ""
    return p


# ─── 4b: TMDB-first / YouTube-for-trailer ────────────────────────────────────

class TestVideoTypeBranching:
    """4b — non-trailer uses TMDB; trailer uses YouTube search."""

    @pytest.mark.asyncio
    async def test_non_trailer_uses_tmdb_not_youtube(self):
        media = _make_media()
        profile = _make_profile(VideoType.FEATURETTE)

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.get_tmdb_youtube_key", new_callable=AsyncMock, return_value="tmdb_abc") as mock_tmdb,
            patch("download.pipeline.trailer_search.get_video_id") as mock_yt,
            patch("download.pipeline._update_media_status"),
            patch("download.pipeline._download_and_verify_trailer", return_value=("/tmp/f.mkv", MagicMock())),
            patch("download.pipeline.trailer_file.move_trailer_to_folder", return_value="/final/f.mkv"),
            patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock),
            patch("download.pipeline.trailer_status_repo.read", return_value=None),
            patch("download.pipeline.event_service.track_trailer_downloaded"),
            patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock),
        ):
            mock_settings.tmdb_api_key = "key123"
            mock_settings.wait_for_media = False
            result = await download_trailer(media, profile, retry_count=0)

        assert result is True
        mock_tmdb.assert_called_once_with(media, "featurette", 0, language="")
        mock_yt.assert_not_called()

    @pytest.mark.asyncio
    async def test_trailer_type_uses_youtube_not_tmdb(self):
        media = _make_media()
        profile = _make_profile(VideoType.TRAILER)

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.get_tmdb_youtube_key", new_callable=AsyncMock) as mock_tmdb,
            patch("download.pipeline.trailer_search.get_video_id", return_value="yt_abc"),
            patch("download.pipeline._update_media_status"),
            patch("download.pipeline._download_and_verify_trailer", return_value=("/tmp/t.mkv", MagicMock())),
            patch("download.pipeline.trailer_file.move_trailer_to_folder", return_value="/final/t.mkv"),
            patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock),
            patch("download.pipeline.trailer_status_repo.read", return_value=None),
            patch("download.pipeline.event_service.track_trailer_downloaded"),
            patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock),
        ):
            result = await download_trailer(media, profile, retry_count=0)

        assert result is True
        mock_tmdb.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_trailer_no_tmdb_key_sets_not_available(self):
        media = _make_media()
        profile = _make_profile(VideoType.FEATURETTE)

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.trailer_status_repo.update_row_status") as mock_upd,
        ):
            mock_settings.tmdb_api_key = ""
            result = await download_trailer(media, profile, retry_count=0, status_row_id=42)

        assert result is False
        mock_upd.assert_called_once_with(42, TrailerStatusEnum.NOT_AVAILABLE)

    @pytest.mark.asyncio
    async def test_non_trailer_no_tmdb_result_sets_not_available(self):
        media = _make_media()
        profile = _make_profile(VideoType.FEATURETTE)

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.get_tmdb_youtube_key", new_callable=AsyncMock, return_value=None),
            patch("download.pipeline.trailer_status_repo.update_row_status") as mock_upd,
        ):
            mock_settings.tmdb_api_key = "key123"
            result = await download_trailer(media, profile, retry_count=0, status_row_id=77)

        assert result is False
        mock_upd.assert_called_once_with(77, TrailerStatusEnum.NOT_AVAILABLE)

    @pytest.mark.asyncio
    async def test_non_trailer_no_status_row_no_update(self):
        media = _make_media()
        profile = _make_profile(VideoType.FEATURETTE)

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.get_tmdb_youtube_key", new_callable=AsyncMock, return_value=None),
            patch("download.pipeline.trailer_status_repo.update_row_status") as mock_upd,
        ):
            mock_settings.tmdb_api_key = "key123"
            result = await download_trailer(media, profile, retry_count=0, status_row_id=None)

        assert result is False
        mock_upd.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_trailer_season_passed_to_tmdb(self):
        media = _make_media()
        profile = _make_profile(VideoType.FEATURETTE)

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.get_tmdb_youtube_key", new_callable=AsyncMock, return_value="tmdb_abc") as mock_tmdb,
            patch("download.pipeline._update_media_status"),
            patch("download.pipeline._download_and_verify_trailer", return_value=("/tmp/f.mkv", MagicMock())),
            patch("download.pipeline.trailer_file.move_trailer_to_folder", return_value="/final/f.mkv"),
            patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock),
            patch("download.pipeline.trailer_status_repo.read", return_value=None),
            patch("download.pipeline.event_service.track_trailer_downloaded"),
            patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock),
        ):
            mock_settings.tmdb_api_key = "key123"
            mock_settings.wait_for_media = False
            await download_trailer(media, profile, retry_count=0, season=3, sequence=2)

        mock_tmdb.assert_called_once_with(media, "featurette", 3, language="")


# ─── 4c: get_tmdb_youtube_key ─────────────────────────────────────────────────

class TestGetTmdbYoutubeKey:
    """4c — get_tmdb_youtube_key public helper."""

    @pytest.mark.asyncio
    async def test_returns_key_for_matching_type(self):
        from services.tmdb_service import get_tmdb_youtube_key
        media = _make_media(txdb_id="12345", is_movie=True)
        results = [{"site": "YouTube", "type": "Featurette", "key": "abc123"}]

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock, return_value=results),
        ):
            mock_settings.tmdb_api_key = "key"
            result = await get_tmdb_youtube_key(media, "featurette", season=0)

        assert result == "abc123"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_match(self):
        from services.tmdb_service import get_tmdb_youtube_key
        media = _make_media(txdb_id="12345", is_movie=True)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock, return_value=[]),
        ):
            mock_settings.tmdb_api_key = "key"
            result = await get_tmdb_youtube_key(media, "featurette", season=0)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_without_api_key(self):
        from services.tmdb_service import get_tmdb_youtube_key
        media = _make_media(txdb_id="12345")

        with patch("services.tmdb_service.app_settings") as mock_settings:
            mock_settings.tmdb_api_key = ""
            result = await get_tmdb_youtube_key(media, "featurette")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_without_txdb_id(self):
        from services.tmdb_service import get_tmdb_youtube_key
        media = _make_media(txdb_id="")

        with patch("services.tmdb_service.app_settings") as mock_settings:
            mock_settings.tmdb_api_key = "key"
            result = await get_tmdb_youtube_key(media, "featurette")

        assert result is None

    @pytest.mark.asyncio
    async def test_passes_season_to_fetch(self):
        from services.tmdb_service import get_tmdb_youtube_key
        media = _make_media(txdb_id="999", is_movie=False)

        with (
            patch("services.tmdb_service.app_settings") as mock_settings,
            patch("services.tmdb_service._fetch_tmdb_videos", new_callable=AsyncMock, return_value=[]) as mock_fetch,
        ):
            mock_settings.tmdb_api_key = "key"
            await get_tmdb_youtube_key(media, "trailer", season=2)

        mock_fetch.assert_called_once()
        _, _, _, season_arg, _ = mock_fetch.call_args[0]
        assert season_arg == 2


# ─── 4d: template variables in search ────────────────────────────────────────

class TestTemplateVariables:
    """4d — {season}, {sequence}, {video_type} expand correctly in search queries."""

    def _call_replace(self, query, **kwargs):
        from download.search import __replace_media_options as _rmo
        # Access the private function via its mangled name
        import download.search as _mod
        fn = getattr(_mod, "_TestTemplateVariables__replace_media_options", None)
        if fn is None:
            # Python name-mangling doesn't apply outside class — access via module
            fn = getattr(_mod, f"_{_mod.__name__.split('.')[-1]}__replace_media_options", None)
        if fn is None:
            # Access directly since it's module-level (double underscore = name-mangled only in classes)
            import importlib
            src = importlib.import_module("download.search")
            fn = src.__dict__.get("_search__replace_media_options") or src.__dict__.get("__replace_media_options")
        return fn

    def _replace(self, query, media, **kwargs):
        import download.search as mod
        # Module-level double-underscore functions are accessible via _module__name
        fn = getattr(mod, "_search__replace_media_options", None) or mod.__dict__.get(
            f"_{mod.__name__.replace('.', '_')}__replace_media_options"
        )
        if fn is None:
            # Try to grab it another way
            for name, obj in mod.__dict__.items():
                if "replace_media_options" in name and callable(obj):
                    fn = obj
                    break
        assert fn is not None, "Could not find __replace_media_options"
        return fn(query, media, **kwargs)

    def _get_replace_fn(self):
        import download.search as mod
        for name, obj in mod.__dict__.items():
            if "replace_media_options" in name and callable(obj):
                return obj
        raise AssertionError("Could not find __replace_media_options in download.search")

    def test_season_variable_expands(self):
        fn = self._get_replace_fn()
        media = _make_media()
        result = fn("{season}", media, season=3)
        assert result == "3"

    def test_sequence_variable_expands(self):
        fn = self._get_replace_fn()
        media = _make_media()
        result = fn("{sequence}", media, sequence=2)
        assert result == "2"

    def test_video_type_variable_expands(self):
        fn = self._get_replace_fn()
        media = _make_media()
        result = fn("{video_type}", media, video_type="featurette")
        assert result == "featurette"

    def test_defaults_are_zero_one_trailer(self):
        fn = self._get_replace_fn()
        media = _make_media()
        result = fn("{season}-{sequence}-{video_type}", media)
        assert result == "0-1-trailer"

    def test_get_search_query_includes_season(self):
        from download.search import get_search_query
        media = _make_media()
        profile = MagicMock()
        profile.search_query = "{title} S{season}"
        profile.customfilter = MagicMock()
        query = get_search_query(media, profile, season=2)
        assert "S2" in query

    def test_get_search_query_includes_video_type(self):
        from download.search import get_search_query
        media = _make_media()
        profile = MagicMock()
        profile.search_query = "{title} {video_type}"
        profile.customfilter = MagicMock()
        query = get_search_query(media, profile, video_type="featurette")
        assert "featurette" in query


# ─── 4d: template variables in filename ──────────────────────────────────────

class TestFilenameTemplateVariables:
    """4d — {season}, {sequence}, {video_type} expand in file/folder name templates."""

    def _make_profile_mock(self, file_name="{title}-trailer.{ext}", video_type=VideoType.TRAILER):
        p = MagicMock()
        p.file_name = file_name
        p.file_format = "mkv"
        p.video_resolution = 1080
        p.video_format = "h264"
        p.audio_format = "aac"
        p.video_type = video_type
        return p

    def test_season_in_filename_template(self):
        from download.filename import get_trailer_filename
        media = _make_media()
        profile = self._make_profile_mock(file_name="{title}-S{season}.{ext}")
        result = get_trailer_filename(media, profile, "mkv", 1, season=2)
        assert "S2" in result

    def test_sequence_in_filename_template(self):
        from download.filename import get_trailer_filename
        media = _make_media()
        profile = self._make_profile_mock(file_name="{title}-{sequence}.{ext}")
        result = get_trailer_filename(media, profile, "mkv", 1, sequence=3)
        assert "-3." in result

    def test_video_type_in_filename_template(self):
        from download.filename import get_trailer_filename
        media = _make_media()
        profile = self._make_profile_mock(
            file_name="{title}-{video_type}.{ext}",
            video_type=VideoType.FEATURETTE,
        )
        result = get_trailer_filename(media, profile, "mkv", 1)
        assert "featurette" in result
