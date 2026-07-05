"""Tests for the rename_file_fol endpoint in api/v1/files.py.

Covers the download-lookup logic added so renaming a trailer file from the
UI updates the existing Download record in place (path/file_name), instead
of leaving it stale until the next files-scan pass recreates it as a new row.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.v1.files import rename_file_fol

OLD_PATH = "/media/Movie (2025)/Trailers/movie-trailer.mkv"
NEW_PATH = "/media/Movie (2025)/Trailers/movie-trailer-renamed.mkv"
NON_TRAILER_PATH = "/media/Movie (2025)/movie.mkv"
MEDIA_ID = 42


def make_download(id: int, path: str) -> SimpleNamespace:
    return SimpleNamespace(id=id, path=path)


class TestRenameFileFolRenameFailure:
    @pytest.mark.asyncio
    async def test_rename_failure_skips_db_update(self):
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch(
                "api.v1.files.FilesHandler.rename_file_fol",
                AsyncMock(return_value=False),
            ),
            patch("api.v1.files.download_manager.read_by_media_id") as mock_read,
            patch("api.v1.files.rename_trailer_download") as mock_rename,
        ):
            result = await rename_file_fol(OLD_PATH, NEW_PATH, MEDIA_ID)

        assert result is False
        mock_read.assert_not_called()
        mock_rename.assert_not_called()


class TestRenameFileFolNoMediaId:
    @pytest.mark.asyncio
    async def test_rename_without_media_id_skips_db_update(self):
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch(
                "api.v1.files.FilesHandler.rename_file_fol",
                AsyncMock(return_value=True),
            ),
            patch("api.v1.files.download_manager.read_by_media_id") as mock_read,
            patch("api.v1.files.rename_trailer_download") as mock_rename,
        ):
            result = await rename_file_fol(OLD_PATH, NEW_PATH)  # media_id defaults to -1

        assert result is True
        mock_read.assert_not_called()
        mock_rename.assert_not_called()


class TestRenameFileFolNoMatchingDownload:
    @pytest.mark.asyncio
    async def test_rename_no_matching_download_skips_update(self):
        """Renaming a file with no matching download record leaves the DB alone."""
        downloads = [make_download(1, OLD_PATH)]
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch(
                "api.v1.files.FilesHandler.rename_file_fol",
                AsyncMock(return_value=True),
            ),
            patch(
                "api.v1.files.download_manager.read_by_media_id",
                return_value=downloads,
            ),
            patch("api.v1.files.rename_trailer_download") as mock_rename,
        ):
            result = await rename_file_fol(NON_TRAILER_PATH, NEW_PATH, MEDIA_ID)

        assert result is True
        mock_rename.assert_not_called()


class TestRenameFileFolUpdatesMatchingDownload:
    @pytest.mark.asyncio
    async def test_rename_updates_matching_download(self):
        """Renaming a tracked trailer file updates the matching Download row in place."""
        download = make_download(1, OLD_PATH)
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch(
                "api.v1.files.FilesHandler.rename_file_fol",
                AsyncMock(return_value=True),
            ),
            patch(
                "api.v1.files.download_manager.read_by_media_id",
                return_value=[download],
            ),
            patch(
                "api.v1.files.rename_trailer_download",
                new=AsyncMock(return_value=True),
            ) as mock_rename,
        ):
            result = await rename_file_fol(OLD_PATH, NEW_PATH, MEDIA_ID)

        assert result is True
        mock_rename.assert_called_once_with(download, NEW_PATH)
