"""Tests for fix_trailer_exists_flags in core/tasks/startup_fixes.py"""

from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from core.tasks.startup_fixes import fix_trailer_exists_flags


def make_profile(profile_id: int = 1, stop_monitoring: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=profile_id, stop_monitoring=stop_monitoring)


def make_media(
    media_id: int = 1,
    monitor: bool = False,
    trailer_exists: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(id=media_id, monitor=monitor, trailer_exists=trailer_exists)


def make_download(
    download_id: int = 1,
    profile_id: int = 1,
    file_exists: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(id=download_id, profile_id=profile_id, file_exists=file_exists)


class TestFixTrailerExistsFlags:

    @pytest.mark.asyncio
    async def test_no_profiles_returns_early(self):
        """No trailer profiles → skip everything, no DB writes."""
        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator") as mock_media,
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_media.assert_not_called()
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_qualifying_media_gets_fixed(self):
        """monitor=False, trailer_exists=False, file_exists=True, stop_monitoring=True → fixed."""
        profile = make_profile(profile_id=1, stop_monitoring=True)
        media = make_media(media_id=10, monitor=False, trailer_exists=False)
        download = make_download(download_id=1, profile_id=1, file_exists=True)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media])),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id", return_value=[download]),
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_update.assert_called_once_with(10, True)

    @pytest.mark.asyncio
    async def test_monitored_media_is_skipped(self):
        """media.monitor=True → not touched regardless of downloads."""
        profile = make_profile(stop_monitoring=True)
        media = make_media(media_id=2, monitor=True, trailer_exists=False)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media])),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id") as mock_downloads,
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_downloads.assert_not_called()
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_with_trailer_exists_is_skipped(self):
        """media.trailer_exists=True → not touched."""
        profile = make_profile(stop_monitoring=True)
        media = make_media(media_id=3, monitor=False, trailer_exists=True)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media])),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id") as mock_downloads,
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_downloads.assert_not_called()
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_file_not_existing_is_skipped(self):
        """Download with file_exists=False → not counted as qualifying."""
        profile = make_profile(stop_monitoring=True)
        media = make_media(media_id=4, monitor=False, trailer_exists=False)
        download = make_download(file_exists=False)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media])),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id", return_value=[download]),
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_profile_with_stop_monitoring_false_is_skipped(self):
        """Profile.stop_monitoring=False → download does not qualify."""
        profile = make_profile(profile_id=1, stop_monitoring=False)
        media = make_media(media_id=5, monitor=False, trailer_exists=False)
        download = make_download(profile_id=1, file_exists=True)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media])),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id", return_value=[download]),
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_qualifying_media_makes_no_writes(self):
        """All media already monitored or has trailer → no update calls."""
        profile = make_profile(stop_monitoring=True)
        media1 = make_media(media_id=1, monitor=True)
        media2 = make_media(media_id=2, trailer_exists=True)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media1, media2])),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id") as mock_downloads,
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_downloads.assert_not_called()
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_only_qualifying_media_fixed_in_mixed_list(self):
        """Mixed list: only the item that meets all criteria is fixed."""
        profile = make_profile(profile_id=1, stop_monitoring=True)

        qualifying = make_media(media_id=10, monitor=False, trailer_exists=False)
        monitored = make_media(media_id=20, monitor=True)
        has_trailer = make_media(media_id=30, trailer_exists=True)
        no_file = make_media(media_id=40, monitor=False, trailer_exists=False)

        qualifying_dl = make_download(profile_id=1, file_exists=True)
        no_file_dl = make_download(profile_id=1, file_exists=False)

        def downloads_for(media_id):
            if media_id == 10:
                return [qualifying_dl]
            if media_id == 40:
                return [no_file_dl]
            return []

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch(
                "core.tasks.startup_fixes.media_manager.read_all_generator",
                return_value=iter([qualifying, monitored, has_trailer, no_file]),
            ),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id", side_effect=downloads_for),
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_update.assert_called_once_with(10, True)

    @pytest.mark.asyncio
    async def test_first_qualifying_download_is_sufficient(self):
        """Multiple downloads per media: only one qualifying download needed; media fixed once."""
        profile = make_profile(profile_id=1, stop_monitoring=True)
        media = make_media(media_id=7, monitor=False, trailer_exists=False)
        dl_no_file = make_download(download_id=1, profile_id=1, file_exists=False)
        dl_qualifies = make_download(download_id=2, profile_id=1, file_exists=True)
        dl_also_qualifies = make_download(download_id=3, profile_id=1, file_exists=True)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch("core.tasks.startup_fixes.media_manager.read_all_generator", return_value=iter([media])),
            patch(
                "core.tasks.startup_fixes.download_manager.read_by_media_id",
                return_value=[dl_no_file, dl_qualifies, dl_also_qualifies],
            ),
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_update.assert_called_once_with(7, True)

    @pytest.mark.asyncio
    async def test_multiple_qualifying_media_all_fixed(self):
        """Multiple qualifying items → update called for each."""
        profile = make_profile(profile_id=1, stop_monitoring=True)
        media1 = make_media(media_id=11, monitor=False, trailer_exists=False)
        media2 = make_media(media_id=22, monitor=False, trailer_exists=False)
        download = make_download(profile_id=1, file_exists=True)

        with (
            patch("core.tasks.startup_fixes.trailerprofile_manager.get_trailerprofiles", return_value=[profile]),
            patch(
                "core.tasks.startup_fixes.media_manager.read_all_generator",
                return_value=iter([media1, media2]),
            ),
            patch("core.tasks.startup_fixes.download_manager.read_by_media_id", return_value=[download]),
            patch("core.tasks.startup_fixes.media_manager.update_trailer_exists") as mock_update,
        ):
            await fix_trailer_exists_flags()

            mock_update.assert_has_calls([call(11, True), call(22, True)])
            assert mock_update.call_count == 2
