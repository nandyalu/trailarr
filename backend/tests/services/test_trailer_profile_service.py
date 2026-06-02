"""Tests for services/trailer_profile_service.py."""

from unittest.mock import MagicMock, patch

from services import trailer_profile_service


def _make_profile(profile_id: int = 1, for_movies: bool = True, max_count: int = 1):
    profile = MagicMock()
    profile.id = profile_id
    profile.for_movies = for_movies
    profile.max_count = max_count
    profile.enabled = True
    profile.retry_count = 2
    profile.download_season_videos = False
    profile.customfilter = MagicMock()
    profile.customfilter.filter_name = "Test Filter"
    profile.customfilter.filters = []
    return profile


class TestCreate:

    def test_creates_profile_via_repo(self):
        profile_create = MagicMock()
        mock_profile = _make_profile()

        with patch("services.trailer_profile_service.profile_repo.create", return_value=mock_profile) as mock_create:
            result = trailer_profile_service.create(profile_create)

        mock_create.assert_called_once_with(profile_create)
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

    def test_updates_profile_via_repo(self):
        profile_create = MagicMock()
        mock_profile = _make_profile()

        with patch("services.trailer_profile_service.profile_repo.update", return_value=mock_profile) as mock_update:
            result = trailer_profile_service.update(3, profile_create)

        mock_update.assert_called_once_with(3, profile_create)
        assert result is mock_profile


class TestUpdateSetting:

    def test_updates_setting_via_repo(self):
        mock_profile = _make_profile()

        with patch("services.trailer_profile_service.profile_repo.update_setting", return_value=mock_profile) as mock_update:
            result = trailer_profile_service.update_setting(5, "stop_monitoring", True)

        mock_update.assert_called_once_with(5, "stop_monitoring", True)
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


