"""Comprehensive tests for services/trailer_profile_service.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from services import trailer_profile_service


def _make_profile(profile_id: int = 1, for_movies: bool = True, max_count: int = 1):
    profile = MagicMock()
    profile.id = profile_id
    profile.for_movies = for_movies
    profile.max_count = max_count
    profile.download_season_videos = False
    profile.customfilter = MagicMock()
    profile.customfilter.filter_name = "Test Filter"
    profile.customfilter.filters = []
    return profile


class TestSyncStatusRows:
    """Tests for the internal _sync_status_rows via the public API."""

    def test_creates_rows_for_matching_media(self):
        profile = _make_profile()
        media_list = [MagicMock(id=1), MagicMock(id=2)]

        with (
            patch("services.trailer_profile_service.media_repo.read_all", return_value=media_list),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=2) as mock_create,
            patch("services.trailer_profile_service.status_repo.delete_undownloaded_rows_for_profile", return_value=0),
        ):
            trailer_profile_service._sync_status_rows(profile)

        mock_create.assert_called_once_with(
            profile_id=profile.id,
            for_movies=profile.for_movies,
            max_count=profile.max_count,
            download_season_videos=profile.download_season_videos,
            media_list=media_list,
        )

    def test_deletes_rows_for_non_matching_media(self):
        profile = _make_profile()
        media1 = MagicMock(id=10)
        media2 = MagicMock(id=20)
        media_list = [media1, media2]

        def fake_matches(media, filters):
            return media.id == 10  # only media1 matches

        with (
            patch("services.trailer_profile_service.media_repo.read_all", return_value=media_list),
            patch("services.trailer_profile_service.matches_filters", side_effect=fake_matches),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=0),
            patch("services.trailer_profile_service.status_repo.delete_undownloaded_rows_for_profile", return_value=1) as mock_delete,
        ):
            trailer_profile_service._sync_status_rows(profile)

        mock_delete.assert_called_once_with(profile_id=profile.id, media_ids=[20])

    def test_no_creates_when_no_matching_media(self):
        profile = _make_profile()
        media_list = [MagicMock(id=1)]

        with (
            patch("services.trailer_profile_service.media_repo.read_all", return_value=media_list),
            patch("services.trailer_profile_service.matches_filters", return_value=False),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile") as mock_create,
            patch("services.trailer_profile_service.status_repo.delete_undownloaded_rows_for_profile", return_value=0),
        ):
            trailer_profile_service._sync_status_rows(profile)

        mock_create.assert_not_called()

    def test_no_deletes_when_all_media_matches(self):
        profile = _make_profile()
        media_list = [MagicMock(id=1), MagicMock(id=2)]

        with (
            patch("services.trailer_profile_service.media_repo.read_all", return_value=media_list),
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=0),
            patch("services.trailer_profile_service.status_repo.delete_undownloaded_rows_for_profile") as mock_delete,
        ):
            trailer_profile_service._sync_status_rows(profile)

        mock_delete.assert_not_called()

    def test_filters_movies_only_for_movie_profile(self):
        profile = _make_profile(for_movies=True)

        with (
            patch("services.trailer_profile_service.media_repo.read_all") as mock_read,
            patch("services.trailer_profile_service.matches_filters", return_value=True),
            patch("services.trailer_profile_service.status_repo.create_rows_for_profile", return_value=0),
            patch("services.trailer_profile_service.status_repo.delete_undownloaded_rows_for_profile", return_value=0),
        ):
            mock_read.return_value = []
            trailer_profile_service._sync_status_rows(profile)

        mock_read.assert_called_once_with(movies_only=True)


class TestCreate:

    def test_creates_profile_and_syncs_rows(self):
        profile_create = MagicMock()
        mock_profile = _make_profile()

        with (
            patch("services.trailer_profile_service.profile_repo.create", return_value=mock_profile) as mock_create,
            patch("services.trailer_profile_service._sync_status_rows") as mock_sync,
        ):
            result = trailer_profile_service.create(profile_create)

        mock_create.assert_called_once_with(profile_create)
        mock_sync.assert_called_once_with(mock_profile)
        assert result is mock_profile


class TestRead:

    def test_delegates_to_repo(self):
        mock_profile = _make_profile()
        with patch("services.trailer_profile_service.profile_repo.read", return_value=mock_profile) as mock_read:
            result = trailer_profile_service.read(7)
        mock_read.assert_called_once_with(7)
        assert result is mock_profile


class TestReadAll:

    def test_delegates_to_repo(self):
        profiles = [_make_profile(), _make_profile(2)]
        with patch("services.trailer_profile_service.profile_repo.read_all", return_value=profiles) as mock_read:
            result = trailer_profile_service.read_all()
        mock_read.assert_called_once()
        assert result is profiles


class TestUpdate:

    def test_updates_profile_and_syncs_rows(self):
        profile_create = MagicMock()
        mock_profile = _make_profile()

        with (
            patch("services.trailer_profile_service.profile_repo.update", return_value=mock_profile) as mock_update,
            patch("services.trailer_profile_service._sync_status_rows") as mock_sync,
        ):
            result = trailer_profile_service.update(3, profile_create)

        mock_update.assert_called_once_with(3, profile_create)
        mock_sync.assert_called_once_with(mock_profile)
        assert result is mock_profile


class TestUpdateSetting:

    def test_updates_setting_and_syncs_rows(self):
        mock_profile = _make_profile()

        with (
            patch("services.trailer_profile_service.profile_repo.update_setting", return_value=mock_profile) as mock_update,
            patch("services.trailer_profile_service._sync_status_rows") as mock_sync,
        ):
            result = trailer_profile_service.update_setting(5, "stop_monitoring", True)

        mock_update.assert_called_once_with(5, "stop_monitoring", True)
        mock_sync.assert_called_once_with(mock_profile)
        assert result is mock_profile


class TestDelete:

    def test_delegates_to_repo(self):
        with patch("services.trailer_profile_service.profile_repo.delete", return_value=True) as mock_delete:
            result = trailer_profile_service.delete(4)
        mock_delete.assert_called_once_with(4)
        assert result is True

    def test_returns_false_when_not_found(self):
        with patch("services.trailer_profile_service.profile_repo.delete", return_value=False):
            result = trailer_profile_service.delete(9999)
        assert result is False
