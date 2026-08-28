"""Tests for core/tasks/files_scan.py — folder-change detection and scan_media_folder."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models.event import EventSource
from core.tasks.files_scan import (
    _ctime_matches_stored,
    _has_folder_changed,
    _is_disk_available,
    scan_media_folder,
)


def make_mock_media(
    media_id: int = 1,
    title: str = "Test Movie",
    folder_path: str | None = "/media/Test Movie (2025)",
    downloads: list | None = None,
    media_exists: bool = False,
    monitor: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        title=title,
        folder_path=folder_path,
        downloads=downloads if downloads is not None else [],
        media_exists=media_exists,
        monitor=monitor,
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


class TestIsDiskAvailable:
    def test_reachable_parent_returns_true(self, tmp_path):
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()
        assert _is_disk_available(str(folder)) is True

    def test_walks_up_to_existing_ancestor_when_immediate_parent_missing(self, tmp_path):
        # "Movies" under tmp_path doesn't exist — the folder itself is one
        # level deeper than anything real. tmp_path (the grandparent) does
        # exist and is listable, so availability should still be True.
        folder = tmp_path / "Movies" / "Movie (2025)"
        assert _is_disk_available(str(folder)) is True

    def test_listdir_error_on_existing_ancestor_returns_false(self, tmp_path):
        """Simulates a stale/disconnected mount: the ancestor directory
        "exists" but can't actually be listed (I/O error, stale handle)."""
        folder = tmp_path / "Movie (2025)"
        folder.mkdir()
        with patch(
            "core.tasks.files_scan.os.listdir",
            side_effect=OSError("Stale file handle"),
        ):
            assert _is_disk_available(str(folder)) is False


class TestScanMediaFolder:
    @pytest.mark.asyncio
    async def test_no_folder_path_returns_zero(self):
        media = make_mock_media(folder_path=None)
        new, missing, renamed, modified, unavailable = await scan_media_folder(media)
        assert (new, missing, renamed, modified, unavailable) == (0, 0, 0, 0, 0)

    @pytest.mark.asyncio
    async def test_system_initiated_unchanged_folder_skips(self):
        media = make_mock_media()
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan._has_folder_changed", return_value=False
        ) as mock_changed:
            new, missing, renamed, modified, unavailable = await scan_media_folder(
                media, scanner=mock_scanner, user_initiated=False
            )

        assert (new, missing, renamed, modified, unavailable) == (0, 0, 0, 0, 0)
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
    async def test_folder_gone_resets_media_exists(self):
        """When the folder is gone and media_exists is True, it is cleared."""
        media = make_mock_media(media_exists=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with patch(
            "core.tasks.files_scan.media_manager.update_media_exists"
        ) as mock_update:
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        assert (new, missing, renamed, modified, unavailable) == (0, 0, 0, 0, 0)
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
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        assert (new, missing, renamed, modified, unavailable) == (0, 0, 0, 0, 0)
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

    @pytest.mark.asyncio
    async def test_already_recorded_trailer_not_recorded_again(self):
        """A disk trailer whose path already has a download row is left
        alone — no new download entry is created."""
        existing_dl = SimpleNamespace(path="/media/Test Movie (2025)/Test Movie-trailer.mkv", file_exists=True)
        media = make_mock_media(monitor=False, downloads=[existing_dl])
        trailer_path = existing_dl.path
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=False)
        mock_scanner.get_trailer_paths = MagicMock(return_value={trailer_path})

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        # Trailer was already recorded — no new download entry
        mock_record.assert_not_called()
        assert new == 0

    @pytest.mark.asyncio
    async def test_new_trailer_found_while_monitored_records_download(self):
        """A new trailer found on disk records the download even while
        monitored — download rows alone decide whether a trailer exists
        (satisfaction rule prevents re-downloads)."""
        trailer_path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        # No existing downloads — file is brand new
        media = make_mock_media(monitor=True, downloads=[])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=False)
        mock_scanner.get_trailer_paths = MagicMock(return_value={trailer_path})

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
            patch("core.tasks.files_scan.event_manager.track_trailer_detected"),
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        # File is new — download is recorded
        mock_record.assert_called_once()
        assert new == 1

    @pytest.mark.asyncio
    async def test_missing_trailer_marks_deleted(self):
        """A download whose file no longer exists on disk (and isn't a rename
        match) is marked deleted with reason='file_not_found'."""
        path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        existing_dl = SimpleNamespace(
            id=3,
            path=path,
            file_exists=True,
            file_hash="abc",
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value=set())

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch(
                "core.tasks.files_scan._is_disk_available", return_value=True
            ),
            patch(
                "core.tasks.files_scan.download_manager.mark_as_deleted"
            ) as mock_delete,
            patch(
                "core.tasks.files_scan.event_manager.track_trailer_deleted"
            ) as mock_track,
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        mock_delete.assert_called_once_with(existing_dl.id)
        mock_track.assert_called_once_with(
            media_id=media.id,
            reason="file_not_found",
            source=EventSource.USER,
            source_detail="FilesScan",
        )
        assert missing == 1


class TestRenameAndHashDetection:
    """Tests for rename-by-hash matching and in-place content-change detection."""

    @pytest.mark.asyncio
    async def test_renamed_trailer_matched_by_hash(self):
        """A disk file at a new path whose hash matches a 'missing' download's
        stored hash is treated as a rename — the existing row is updated in
        place, not deleted+recreated."""
        old_path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        new_path = "/media/Test Movie (2025)/Trailers/Test Movie-trailer.mkv"
        existing_dl = SimpleNamespace(
            id=7,
            path=old_path,
            file_exists=True,
            file_hash="abc123",
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value={new_path})

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch(
                "core.tasks.files_scan.compute_file_hash",
                return_value="abc123",
            ),
            patch(
                "core.tasks.files_scan.rename_trailer_download",
                new=AsyncMock(return_value=True),
            ) as mock_rename,
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
            patch(
                "core.tasks.files_scan.event_manager.track_trailer_renamed"
            ) as mock_track,
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        mock_rename.assert_called_once_with(existing_dl, new_path)
        mock_record.assert_not_called()
        mock_track.assert_called_once_with(
            media_id=media.id,
            old_path=old_path,
            new_path=new_path,
            source=EventSource.USER,
            source_detail="FilesScan",
        )
        assert (new, missing, renamed) == (0, 0, 1)

    @pytest.mark.asyncio
    async def test_hash_mismatch_falls_through_to_new_and_missing(self):
        """When hashes don't match, a new disk path and a missing download are
        NOT reconciled as a rename — normal new+missing handling applies."""
        old_path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        new_path = "/media/Test Movie (2025)/Trailers/Test Movie-trailer.mkv"
        existing_dl = SimpleNamespace(
            id=7,
            path=old_path,
            file_exists=True,
            file_hash="abc123",
            profile_id=1,
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value={new_path})

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch(
                "core.tasks.files_scan.compute_file_hash",
                return_value="different_hash",
            ),
            patch(
                "core.tasks.files_scan.rename_trailer_download"
            ) as mock_rename,
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
            patch(
                "core.tasks.files_scan.download_manager.mark_as_deleted"
            ) as mock_delete,
            patch("core.tasks.files_scan.event_manager.track_trailer_detected"),
            patch("core.tasks.files_scan.event_manager.track_trailer_deleted"),
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        mock_rename.assert_not_called()
        mock_record.assert_called_once()
        mock_delete.assert_called_once_with(existing_dl.id)
        assert (new, missing, renamed) == (1, 1, 0)

    @pytest.mark.asyncio
    async def test_content_changed_same_path_triggers_reanalysis(self):
        """A file at an unchanged path whose ctime differs from stored AND
        whose hash differs from stored is re-analyzed in place (hash/metadata
        refreshed on the same download row)."""
        path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        old_updated_at = datetime.fromtimestamp(1_700_000_000.0, tz=timezone.utc)
        existing_dl = SimpleNamespace(
            id=9,
            path=path,
            file_exists=True,
            file_hash="old_hash",
            updated_at=old_updated_at,
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value={path})

        # ctime clearly past the 1-second tolerance used by _ctime_matches_stored
        fake_stat = SimpleNamespace(st_ctime=old_updated_at.timestamp() + 500)

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch("core.tasks.files_scan.os.stat", return_value=fake_stat),
            patch(
                "core.tasks.files_scan.compute_file_hash",
                return_value="new_hash",
            ),
            patch(
                "core.tasks.files_scan.reanalyze_trailer_download",
                new=AsyncMock(return_value=True),
            ) as mock_reanalyze,
            patch(
                "core.tasks.files_scan.event_manager.track_trailer_modified"
            ) as mock_track,
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        mock_reanalyze.assert_called_once_with(existing_dl, path)
        mock_track.assert_called_once_with(
            media_id=media.id,
            old_hash="old_hash",
            new_hash="new_hash",
            source=EventSource.USER,
            source_detail="FilesScan",
        )
        assert modified == 1

    @pytest.mark.asyncio
    async def test_unchanged_ctime_skips_hash_entirely(self):
        """When the on-disk ctime matches the stored updated_at, the expensive
        hash computation is skipped entirely (cheap pre-check short-circuits)."""
        path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        stored_updated_at = datetime.fromtimestamp(1_700_000_000.0, tz=timezone.utc)
        existing_dl = SimpleNamespace(
            id=9,
            path=path,
            file_exists=True,
            file_hash="same_hash",
            updated_at=stored_updated_at,
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value={path})

        fake_stat = SimpleNamespace(st_ctime=stored_updated_at.timestamp())

        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch("core.tasks.files_scan.os.stat", return_value=fake_stat),
            patch("core.tasks.files_scan.compute_file_hash") as mock_hash,
            patch(
                "core.tasks.files_scan.reanalyze_trailer_download"
            ) as mock_reanalyze,
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        mock_hash.assert_not_called()
        mock_reanalyze.assert_not_called()
        assert modified == 0


class TestDiskUnavailable:
    """Tests for the reachability guard that prevents a disconnected network
    drive from being mistaken for a genuine mass-deletion of trailers."""

    @pytest.mark.asyncio
    async def test_empty_trailer_paths_with_existing_downloads_skips_when_disk_unavailable(self):
        """Folder scan succeeds but finds zero trailers, and we have existing
        download records — if the storage looks unreachable, skip entirely
        rather than marking everything missing."""
        existing_dl = SimpleNamespace(
            id=1,
            path="/mnt/network-share/Movie (2025)/Movie-trailer.mkv",
            file_exists=True,
            file_hash="abc",
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(
            folder_path="/mnt/network-share/Movie (2025)",
            downloads=[existing_dl],
        )
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.get_trailer_paths = MagicMock(return_value=set())

        with (
            patch(
                "core.tasks.files_scan._is_disk_available", return_value=False
            ) as mock_available,
            patch("core.tasks.files_scan.files_manager.update") as mock_files_update,
            patch(
                "core.tasks.files_scan.media_manager.update_media_exists"
            ) as mock_media_update,
            patch(
                "core.tasks.files_scan.download_manager.mark_as_deleted"
            ) as mock_delete,
        ):
            result = await scan_media_folder(media, scanner=mock_scanner)

        assert result == (0, 0, 0, 0, 1)
        mock_available.assert_called_once_with(media.folder_path)
        # Nothing should have been touched — no destructive updates at all.
        mock_files_update.assert_not_called()
        mock_media_update.assert_not_called()
        mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_trailer_paths_with_existing_downloads_proceeds_when_disk_available(self):
        """Same as above, but the reachability check passes — this is a
        genuine deletion, so normal missing-trailer handling should apply."""
        path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        existing_dl = SimpleNamespace(
            id=1,
            path=path,
            file_exists=True,
            file_hash="abc",
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=True)
        mock_scanner.get_trailer_paths = MagicMock(return_value=set())

        with (
            patch(
                "core.tasks.files_scan._is_disk_available", return_value=True
            ),
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch(
                "core.tasks.files_scan.download_manager.mark_as_deleted"
            ) as mock_delete,
        ):
            new, missing, renamed, modified, unavailable = await scan_media_folder(media, scanner=mock_scanner)

        mock_delete.assert_called_once_with(existing_dl.id)
        assert (missing, unavailable) == (1, 0)

    @pytest.mark.asyncio
    async def test_folder_gone_skips_reset_when_disk_unavailable(self):
        """get_folder_files returns None (folder appears gone) — if the
        storage looks unreachable, don't reset media_exists."""
        existing_dl = SimpleNamespace(
            id=1,
            path="/mnt/network-share/Movie (2025)/Movie-trailer.mkv",
            file_exists=True,
            file_hash="abc",
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(
            folder_path="/mnt/network-share/Movie (2025)",
            downloads=[existing_dl],
            media_exists=True,
        )
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with (
            patch(
                "core.tasks.files_scan._is_disk_available", return_value=False
            ),
            patch(
                "core.tasks.files_scan.media_manager.update_media_exists"
            ) as mock_media_update,
        ):
            result = await scan_media_folder(media, scanner=mock_scanner)

        assert result == (0, 0, 0, 0, 1)
        mock_media_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_folder_gone_with_no_existing_downloads_skips_availability_check(self):
        """When there's nothing to lose (no existing downloads), the
        reachability check isn't even invoked — existing folder-gone
        behavior for fresh/empty media is unaffected."""
        media = make_mock_media(downloads=[], media_exists=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=None)

        with (
            patch(
                "core.tasks.files_scan._is_disk_available"
            ) as mock_available,
            patch(
                "core.tasks.files_scan.media_manager.update_media_exists"
            ) as mock_media_update,
        ):
            result = await scan_media_folder(media, scanner=mock_scanner)

        assert result == (0, 0, 0, 0, 0)
        mock_available.assert_not_called()
        mock_media_update.assert_called_once_with(media.id, False)


class TestNewTrailerAttribution:
    """New trailer files found on disk are attributed to the highest-priority
    matching profile that doesn't already own an active download."""

    @staticmethod
    def _make_profile(profile_id: int, priority: int = 100) -> SimpleNamespace:
        return SimpleNamespace(
            id=profile_id,
            priority=priority,
            customfilter=SimpleNamespace(
                filter_name=f"Profile {profile_id}", filters=[]
            ),
        )

    @pytest.mark.asyncio
    async def test_new_trailer_claimed_by_matching_profile(self):
        trailer_path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        media = make_mock_media(downloads=[], monitor=True)
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=False)
        mock_scanner.get_trailer_paths = MagicMock(return_value={trailer_path})

        profile = self._make_profile(5)
        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch("core.tasks.files_scan.event_manager.track_trailer_detected"),
            patch(
                "core.tasks.files_scan.trailerprofile.get_trailerprofiles",
                return_value=[profile],
            ),
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
        ):
            await scan_media_folder(media, scanner=mock_scanner)

        mock_record.assert_called_once_with(media, 5, trailer_path)

    @pytest.mark.asyncio
    async def test_profile_owning_active_download_not_claimed_again(self):
        """When the only matching profile already owns an active download,
        a second new file is recorded unattributed (profile_id=0)."""
        existing_path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        new_path = "/media/Test Movie (2025)/Trailers/Extra-trailer.mkv"
        existing_dl = SimpleNamespace(
            id=3,
            path=existing_path,
            file_exists=True,
            file_hash="abc",
            profile_id=5,
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(downloads=[existing_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=False)
        mock_scanner.get_trailer_paths = MagicMock(
            return_value={existing_path, new_path}
        )

        profile = self._make_profile(5)
        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch("core.tasks.files_scan.event_manager.track_trailer_detected"),
            patch(
                "core.tasks.files_scan.trailerprofile.get_trailerprofiles",
                return_value=[profile],
            ),
            # existing file "exists" so its download is not treated as stale
            patch("core.tasks.files_scan.os.path.exists", return_value=True),
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
        ):
            await scan_media_folder(media, scanner=mock_scanner)

        mock_record.assert_called_once_with(media, 0, new_path)

    @pytest.mark.asyncio
    async def test_replaced_trailer_frees_profile_for_new_file(self):
        """A stale download (file gone, about to be marked deleted) does not
        block its profile — the replacement file claims the same profile."""
        old_path = "/media/Test Movie (2025)/Test Movie-trailer.mkv"
        new_path = "/media/Test Movie (2025)/Test Movie [new]-trailer.mkv"
        stale_dl = SimpleNamespace(
            id=3,
            path=old_path,
            file_exists=True,
            file_hash="abc",
            profile_id=5,
            updated_at=datetime.now(tz=timezone.utc),
        )
        media = make_mock_media(downloads=[stale_dl])
        mock_scanner = MagicMock()
        mock_scanner.get_folder_files = AsyncMock(return_value=MagicMock())
        mock_scanner.check_media_exists = AsyncMock(return_value=False)
        mock_scanner.get_trailer_paths = MagicMock(return_value={new_path})

        profile = self._make_profile(5)
        with (
            patch("core.tasks.files_scan.files_manager.update"),
            patch("core.tasks.files_scan.media_manager.update_media_exists"),
            patch("core.tasks.files_scan.event_manager.track_trailer_detected"),
            patch("core.tasks.files_scan.event_manager.track_trailer_deleted"),
            patch(
                "core.tasks.files_scan.trailerprofile.get_trailerprofiles",
                return_value=[profile],
            ),
            # hashes differ → not a rename; old file is gone → stale
            patch(
                "core.tasks.files_scan.compute_file_hash",
                return_value="different",
            ),
            patch("core.tasks.files_scan.os.path.exists", return_value=False),
            patch("core.tasks.files_scan.download_manager.mark_as_deleted"),
            patch(
                "core.tasks.files_scan.record_new_trailer_download"
            ) as mock_record,
        ):
            await scan_media_folder(media, scanner=mock_scanner)

        mock_record.assert_called_once_with(media, 5, new_path)
