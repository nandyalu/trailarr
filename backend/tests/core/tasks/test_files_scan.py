"""Tests for core/tasks/files_scan.py — folder-change detection and scan_media_folder."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.tasks.files_scan import (
    _ctime_matches_stored,
    _has_folder_changed,
    scan_media_folder,
)


def make_mock_media(
    media_id: int = 1,
    title: str = "Test Movie",
    folder_path: str | None = "/media/Test Movie (2025)",
    downloads: list | None = None,
    trailer_exists: bool = False,
    media_exists: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        title=title,
        folder_path=folder_path,
        downloads=downloads if downloads is not None else [],
        trailer_exists=trailer_exists,
        media_exists=media_exists,
    )


class TestCtimeMatchesStored:
    def test_naive_local_datetime_matches(self):
        # DB returns naive datetime in local time; in test env local TZ is UTC
        ctime = 1_700_000_000.0
        stored = datetime.fromtimestamp(ctime).replace(tzinfo=None)  # naive local
        assert _ctime_matches_stored(ctime, stored) is True

    def test_aware_utc_datetime_matches(self):
        ctime = 1_700_000_000.0
        stored = datetime.fromtimestamp(ctime, tz=timezone.utc)
        assert _ctime_matches_stored(ctime, stored) is True

    def test_mismatch_returns_false(self):
        ctime = 1_700_000_000.0
        stored = datetime.fromtimestamp(ctime - 120, tz=timezone.utc)
        assert _ctime_matches_stored(ctime, stored) is False

    def test_within_tolerance_returns_true(self):
        ctime = 1_700_000_000.0
        stored = datetime.fromtimestamp(ctime - 0.5, tz=timezone.utc)
        assert _ctime_matches_stored(ctime, stored) is True

    def test_just_over_tolerance_returns_false(self):
        ctime = 1_700_000_000.0
        stored = datetime.fromtimestamp(ctime - 1.5, tz=timezone.utc)
        assert _ctime_matches_stored(ctime, stored) is False


class TestHasFolderChanged:
    TZ = timezone.utc  # test env uses UTC as local timezone

    def test_no_stored_data_triggers_scan(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()

        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value={},
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is True

    def test_unchanged_root_no_subdirs_skips(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()

        stored_dt = datetime.fromtimestamp(folder.stat().st_ctime, tz=timezone.utc)
        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value={str(folder): stored_dt},
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is False

    def test_changed_root_triggers_scan(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()

        old_dt = datetime.fromtimestamp(
            folder.stat().st_ctime - 120, tz=timezone.utc
        )
        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value={str(folder): old_dt},
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is True

    def test_root_not_in_stored_triggers_scan(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()

        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value={"/some/other/path": datetime.now(tz=timezone.utc)},
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is True

    def test_unchanged_root_and_subdirs_skips(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()
        trailers = folder / "Trailers"
        trailers.mkdir()

        stored = {
            str(folder): datetime.fromtimestamp(
                folder.stat().st_ctime, tz=timezone.utc
            ),
            str(trailers): datetime.fromtimestamp(
                trailers.stat().st_ctime, tz=timezone.utc
            ),
        }
        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value=stored,
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is False

    def test_changed_subdir_triggers_scan(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()
        trailers = folder / "Trailers"
        trailers.mkdir()

        stored = {
            str(folder): datetime.fromtimestamp(
                folder.stat().st_ctime, tz=timezone.utc
            ),
            str(trailers): datetime.fromtimestamp(
                trailers.stat().st_ctime - 120, tz=timezone.utc  # old time
            ),
        }
        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value=stored,
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is True

    def test_new_subdir_not_in_stored_triggers_scan(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()
        trailers = folder / "Trailers"
        trailers.mkdir()

        # Only root folder is stored — Trailers subdir is new/untracked
        stored = {
            str(folder): datetime.fromtimestamp(
                folder.stat().st_ctime, tz=timezone.utc
            ),
        }
        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value=stored,
        ):
            assert _has_folder_changed(str(folder), 1, self.TZ) is True

    def test_oserror_triggers_scan(self):
        with patch(
            "core.tasks.files_scan.files_manager.get_folder_modified_times",
            return_value={"/nonexistent": datetime.now(tz=timezone.utc)},
        ):
            assert _has_folder_changed("/nonexistent", 1, timezone.utc) is True


class TestScanMediaFolder:
    @pytest.mark.asyncio
    async def test_no_folder_path_returns_zero(self):
        media = make_mock_media(folder_path=None)
        new, missing = await scan_media_folder(media)
        assert (new, missing) == (0, 0)

    @pytest.mark.asyncio
    async def test_system_initiated_unchanged_folder_skips(self):
        media = make_mock_media()
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan._has_folder_changed", return_value=False
        ) as mock_changed:
            new, missing = await scan_media_folder(
                media, scanner=mock_scanner, user_initiated=False
            )

        assert (new, missing) == (0, 0)
        mock_changed.assert_called_once_with(
            media.folder_path, media.id, mock_scanner.tz
        )

    @pytest.mark.asyncio
    async def test_system_initiated_changed_folder_proceeds(self):
        media = make_mock_media()
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan._has_folder_changed", return_value=True
        ):
            await scan_media_folder(media, scanner=mock_scanner, user_initiated=False)

        mock_scanner.get_folder_files.assert_called_once_with(
            media.folder_path, media.id
        )

    @pytest.mark.asyncio
    async def test_user_initiated_always_scans(self):
        """user_initiated=True bypasses the folder-change check entirely."""
        media = make_mock_media()
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan._has_folder_changed"
        ) as mock_changed:
            await scan_media_folder(media, scanner=mock_scanner, user_initiated=True)

        mock_changed.assert_not_called()
        mock_scanner.get_folder_files.assert_called_once_with(
            media.folder_path, media.id
        )

    @pytest.mark.asyncio
    async def test_folder_gone_resets_trailer_exists(self):
        """When the folder is inaccessible/deleted, trailer_exists is cleared."""
        media = make_mock_media(trailer_exists=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan.media_manager.update_trailer_exists"
        ) as mock_update:
            new, missing = await scan_media_folder(media, scanner=mock_scanner)

        assert (new, missing) == (0, 0)
        mock_update.assert_called_once_with(media.id, False)

    @pytest.mark.asyncio
    async def test_folder_gone_no_trailers_skips_update(self):
        """When the folder is gone but trailer_exists is already False, no update."""
        media = make_mock_media(trailer_exists=False)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan.media_manager.update_trailer_exists"
        ) as mock_update:
            new, missing = await scan_media_folder(media, scanner=mock_scanner)

        assert (new, missing) == (0, 0)
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_folder_gone_resets_media_exists(self):
        """When the folder is gone and media_exists is True, it is cleared."""
        media = make_mock_media(media_exists=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan.media_manager.update_media_exists"
        ) as mock_update:
            new, missing = await scan_media_folder(media, scanner=mock_scanner)

        assert (new, missing) == (0, 0)
        mock_update.assert_called_once_with(media.id, False)

    @pytest.mark.asyncio
    async def test_folder_gone_media_already_false_skips_update(self):
        """When the folder is gone and media_exists is already False, no update."""
        media = make_mock_media(media_exists=False)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan.media_manager.update_media_exists"
        ) as mock_update:
            new, missing = await scan_media_folder(media, scanner=mock_scanner)

        assert (new, missing) == (0, 0)
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_stale_media_exists_true_corrected_to_false(self):
        """When media_exists=True in DB but no media file on disk, it is reset."""
        media = make_mock_media(media_exists=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=False)
        mock_scanner.get_trailer_paths = MagicMock(return_value=set())

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch(
                "core.tasks.files_scan.media_manager.update_media_exists"
            ) as mock_update,
        ):
            await scan_media_folder(media, scanner=mock_scanner)

        mock_update.assert_called_once_with(media.id, False)

    @pytest.mark.asyncio
    async def test_stale_media_exists_false_corrected_to_true(self):
        """When media_exists=False in DB but media file exists on disk, it is set True."""
        media = make_mock_media(media_exists=False)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value=set())

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch(
                "core.tasks.files_scan.media_manager.update_media_exists"
            ) as mock_update,
        ):
            await scan_media_folder(media, scanner=mock_scanner)

        mock_update.assert_called_once_with(media.id, True)

    @pytest.mark.asyncio
    async def test_media_exists_already_correct_skips_update(self):
        """When media_exists in DB matches disk, no update is made."""
        media = make_mock_media(media_exists=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value=set())

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch(
                "core.tasks.files_scan.media_manager.update_media_exists"
            ) as mock_update,
        ):
            await scan_media_folder(media, scanner=mock_scanner)

        mock_update.assert_not_called()
