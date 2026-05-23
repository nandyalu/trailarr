"""Tests for trailer_profile_service.py — Plan 2 coverage (new media + season rows)."""

import datetime
import pytest
from unittest.mock import MagicMock, patch, call

from db.models.media import MediaRead
from services.trailer_profile_service import (
    append_season_rows_for_media,
    create_rows_for_new_media,
)


def _make_media_read(**kwargs) -> MediaRead:
    defaults = dict(
        id=1,
        connection_id=1,
        arr_id=1,
        is_movie=True,
        title="Test Movie",
        clean_title="test movie",
        year=2024,
        language="en",
        studio="Studio",
        txdb_id="12345",
        title_slug="test-movie",
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        downloaded_at=None,
        folder_path="/media/test",
    )
    defaults.update(kwargs)
    return MediaRead(**defaults)


def _make_profile(profile_id: int = 1, for_movies: bool = True, enabled: bool = True,
                  download_season_videos: bool = False) -> MagicMock:
    p = MagicMock()
    p.id = profile_id
    p.enabled = enabled
    p.for_movies = for_movies
    p.max_count = 1
    p.download_season_videos = download_season_videos
    p.customfilter = MagicMock()
    p.customfilter.filter_name = f"Profile {profile_id}"
    p.customfilter.filters = []
    return p


class TestCreateRowsForNewMedia:
    """2a — create_rows_for_new_media must call create_rows_for_profile for matching profiles."""

    def test_creates_rows_for_matching_movie_profile(self):
        media = _make_media_read(is_movie=True)
        profile = _make_profile(for_movies=True)

        with (
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=1) as mock_create,
        ):
            result = create_rows_for_new_media(media)

        assert result == 1
        mock_create.assert_called_once_with(
            profile_id=profile.id,
            for_movies=True,
            max_count=profile.max_count,
            download_season_videos=profile.download_season_videos,
            media_list=[media],
        )

    def test_skips_disabled_profiles(self):
        media = _make_media_read(is_movie=True)
        profile = _make_profile(for_movies=True, enabled=False)

        with (
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = create_rows_for_new_media(media)

        assert result == 0
        mock_create.assert_not_called()

    def test_skips_wrong_scope_movie_vs_series(self):
        media = _make_media_read(is_movie=True)
        profile = _make_profile(for_movies=False)  # series profile

        with (
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = create_rows_for_new_media(media)

        assert result == 0
        mock_create.assert_not_called()

    def test_skips_non_matching_filters(self):
        media = _make_media_read(is_movie=True)
        profile = _make_profile(for_movies=True)

        with (
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.matches_filters", return_value=False),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = create_rows_for_new_media(media)

        assert result == 0
        mock_create.assert_not_called()

    def test_sums_rows_across_multiple_profiles(self):
        media = _make_media_read(is_movie=True)
        p1 = _make_profile(1, for_movies=True)
        p2 = _make_profile(2, for_movies=True)

        with (
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[p1, p2]),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=1),
        ):
            result = create_rows_for_new_media(media)

        assert result == 2

    def test_returns_zero_when_no_profiles(self):
        media = _make_media_read()
        with (
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[]),
        ):
            result = create_rows_for_new_media(media)
        assert result == 0


class TestAppendSeasonRowsForMedia:
    """2b — append_season_rows_for_media must create rows only for series profiles with season videos."""

    def test_creates_rows_for_series_with_download_season_videos(self):
        media = _make_media_read(id=10, is_movie=False, season_count=3)
        profile = _make_profile(1, for_movies=False, download_season_videos=True)

        with (
            patch("services.trailer_profile_service.media_repo.read", return_value=media),
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=2) as mock_create,
        ):
            result = append_season_rows_for_media(10)

        assert result == 2
        mock_create.assert_called_once_with(
            profile_id=profile.id,
            for_movies=False,
            max_count=profile.max_count,
            download_season_videos=True,
            media_list=[media],
        )

    def test_skips_movie_media(self):
        media = _make_media_read(id=5, is_movie=True, season_count=0)

        with (
            patch("services.trailer_profile_service.media_repo.read", return_value=media),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = append_season_rows_for_media(5)

        assert result == 0
        mock_create.assert_not_called()

    def test_skips_series_with_zero_season_count(self):
        media = _make_media_read(id=6, is_movie=False, season_count=0)

        with (
            patch("services.trailer_profile_service.media_repo.read", return_value=media),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = append_season_rows_for_media(6)

        assert result == 0
        mock_create.assert_not_called()

    def test_skips_profiles_without_download_season_videos(self):
        media = _make_media_read(id=7, is_movie=False, season_count=2)
        profile = _make_profile(1, for_movies=False, download_season_videos=False)

        with (
            patch("services.trailer_profile_service.media_repo.read", return_value=media),
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = append_season_rows_for_media(7)

        assert result == 0
        mock_create.assert_not_called()

    def test_skips_movie_profiles(self):
        media = _make_media_read(id=8, is_movie=False, season_count=2)
        profile = _make_profile(1, for_movies=True, download_season_videos=True)

        with (
            patch("services.trailer_profile_service.media_repo.read", return_value=media),
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = append_season_rows_for_media(8)

        assert result == 0
        mock_create.assert_not_called()

    def test_skips_non_matching_filters(self):
        media = _make_media_read(id=9, is_movie=False, season_count=2)
        profile = _make_profile(1, for_movies=False, download_season_videos=True)

        with (
            patch("services.trailer_profile_service.media_repo.read", return_value=media),
            patch("services.trailer_profile_service.profile_repo.read_all", return_value=[profile]),
            patch("services.trailer_profile_service.matches_filters", return_value=False),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
        ):
            result = append_season_rows_for_media(9)

        assert result == 0
        mock_create.assert_not_called()

    def test_handles_media_not_found_gracefully(self):
        with (
            patch("services.trailer_profile_service.media_repo.read", side_effect=Exception("not found")),
        ):
            result = append_season_rows_for_media(999)

        assert result == 0


class TestCreateOrUpdateBulkStatusRows:
    """2c/2d — arr_connection_manager must call service functions on new/updated media."""

    def _make_mock_media(self, media_id=1, is_movie=True, season_count=0):
        m = MagicMock()
        m.id = media_id
        m.is_movie = is_movie
        m.season_count = season_count
        m.model_dump.return_value = {"id": media_id, "folder_path": "/p",
                                     "arr_monitored": True, "monitor": False}
        return m

    def _make_manager(self):
        from db.models.connection import ArrType, ConnectionRead, MonitorType
        from services.arr_connection_manager import BaseConnectionManager

        class _DummyArr:
            async def get_system_status(self): return "ok"
            async def get_rootfolders(self): return []
            async def get_all_media(self): return []

        class _DummyCM(BaseConnectionManager):
            pass

        conn = ConnectionRead(
            id=1, name="Test", arr_type=ArrType.RADARR,
            url="http://test", api_key="key",
            monitor=MonitorType.MONITOR_MISSING,
            added_at=datetime.datetime.now(datetime.timezone.utc),
            path_mappings=[],
        )
        return _DummyCM(connection=conn, arr_manager=_DummyArr(),
                        parse_media=lambda cid, d: d, is_movie=True)

    def test_new_media_triggers_create_rows_for_new_media(self):
        manager = self._make_manager()
        mock_media = self._make_mock_media(1)

        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, True, False, False, 0)]),
            patch("services.arr_connection_manager.event_service.track_media_added"),
            patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create,
        ):
            manager.create_or_update_bulk([MagicMock()])

        mock_create.assert_called_once_with(mock_media)

    def test_existing_media_does_not_trigger_create_rows(self):
        manager = self._make_manager()
        mock_media = self._make_mock_media(1)

        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, False, True, False, 0)]),
            patch("services.trailer_profile_service.create_rows_for_new_media") as mock_create,
        ):
            manager.create_or_update_bulk([MagicMock()])

        mock_create.assert_not_called()

    def test_season_count_increase_triggers_append_season_rows(self):
        manager = self._make_manager()
        mock_media = self._make_mock_media(2, is_movie=False, season_count=3)

        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, False, True, False, 1)]),  # old_season_count=1
            patch("services.trailer_profile_service.append_season_rows_for_media") as mock_append,
        ):
            manager.create_or_update_bulk([MagicMock()])

        mock_append.assert_called_once_with(2)

    def test_season_count_unchanged_no_trigger(self):
        manager = self._make_manager()
        mock_media = self._make_mock_media(3, is_movie=False, season_count=2)

        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, False, True, False, 2)]),  # same count
            patch("services.trailer_profile_service.append_season_rows_for_media") as mock_append,
        ):
            manager.create_or_update_bulk([MagicMock()])

        mock_append.assert_not_called()

    def test_movie_season_count_change_no_trigger(self):
        manager = self._make_manager()
        mock_media = self._make_mock_media(4, is_movie=True, season_count=2)

        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, False, True, False, 0)]),
            patch("services.trailer_profile_service.append_season_rows_for_media") as mock_append,
        ):
            manager.create_or_update_bulk([MagicMock()])

        mock_append.assert_not_called()
