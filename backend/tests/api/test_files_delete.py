"""Tests for the delete_file_fol endpoint in api/v1/files.py.

Covers the download-lookup logic added for multi-trailer support:
- download.file_exists is marked False for matched download records
- media.trailer_exists is reset only when no trailer downloads remain
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from api.v1.files import delete_file_fol

TRAILER_PATH = "/media/Movie (2025)/Trailers/movie-trailer.mkv"
OTHER_PATH = "/media/Movie (2025)/Trailers/movie-trailer2.mkv"
NON_TRAILER_PATH = "/media/Movie (2025)/movie.mkv"
MEDIA_ID = 42


def make_download(id: int, path: str, file_exists: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=id, path=path, file_exists=file_exists)


def _patches(delete_return=True, downloads=None):
    """Return a dict of patch targets and their mock return values."""
    return {
        "api.v1.files._is_path_safe": True,
        "api.v1.files.FilesHandler.delete_file_fol": AsyncMock(return_value=delete_return),
        "api.v1.files.download_manager.read_by_media_id": MagicMock(return_value=downloads or []),
        "api.v1.files.download_manager.mark_as_deleted": MagicMock(),
        "api.v1.files.media_manager.update_trailer_exists": MagicMock(),
    }


class TestDeleteFileFolDeletionFailure:
    @pytest.mark.asyncio
    async def test_deletion_failure_skips_db_updates(self):
        mocks = _patches(delete_return=False)
        with (
            patch("api.v1.files._is_path_safe", return_value=mocks["api.v1.files._is_path_safe"]),
            patch("api.v1.files.FilesHandler.delete_file_fol", mocks["api.v1.files.FilesHandler.delete_file_fol"]),
            patch("api.v1.files.download_manager.read_by_media_id", mocks["api.v1.files.download_manager.read_by_media_id"]) as mock_read,
            patch("api.v1.files.download_manager.mark_as_deleted", mocks["api.v1.files.download_manager.mark_as_deleted"]) as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists", mocks["api.v1.files.media_manager.update_trailer_exists"]) as mock_update,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is False
        mock_read.assert_not_called()
        mock_mark.assert_not_called()
        mock_update.assert_not_called()


class TestDeleteFileFolNoMediaId:
    @pytest.mark.asyncio
    async def test_no_media_id_skips_db_updates(self):
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch("api.v1.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.files.download_manager.read_by_media_id") as mock_read,
            patch("api.v1.files.download_manager.mark_as_deleted") as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists") as mock_update,
        ):
            result = await delete_file_fol(TRAILER_PATH)  # media_id defaults to -1

        assert result is True
        mock_read.assert_not_called()
        mock_mark.assert_not_called()
        mock_update.assert_not_called()


class TestDeleteFileFolNonTrailerFile:
    @pytest.mark.asyncio
    async def test_non_trailer_file_skips_db_updates(self):
        """Deleting a file with no matching download record leaves trailer_exists alone."""
        downloads = [make_download(1, TRAILER_PATH)]
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch("api.v1.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.files.download_manager.read_by_media_id", return_value=downloads),
            patch("api.v1.files.download_manager.mark_as_deleted") as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists") as mock_update,
        ):
            result = await delete_file_fol(NON_TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_not_called()
        mock_update.assert_not_called()


class TestDeleteFileFolLastTrailer:
    @pytest.mark.asyncio
    async def test_last_trailer_resets_trailer_exists(self):
        """Deleting the only trailer marks download deleted and resets trailer_exists."""
        downloads = [make_download(1, TRAILER_PATH)]
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch("api.v1.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.files.download_manager.read_by_media_id", return_value=downloads),
            patch("api.v1.files.download_manager.mark_as_deleted") as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists") as mock_update,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_called_once_with(1)
        mock_update.assert_called_once_with(MEDIA_ID, False)

    @pytest.mark.asyncio
    async def test_last_trailer_with_already_deleted_download_resets_trailer_exists(self):
        """A pre-existing file_exists=False record is not treated as a remaining trailer."""
        downloads = [
            make_download(1, TRAILER_PATH, file_exists=True),
            make_download(2, OTHER_PATH, file_exists=False),  # already deleted
        ]
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch("api.v1.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.files.download_manager.read_by_media_id", return_value=downloads),
            patch("api.v1.files.download_manager.mark_as_deleted") as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists") as mock_update,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_called_once_with(1)
        mock_update.assert_called_once_with(MEDIA_ID, False)


class TestDeleteFileFolRemainingTrailers:
    @pytest.mark.asyncio
    async def test_other_trailer_remains_keeps_trailer_exists(self):
        """Deleting one of many trailers marks it deleted but preserves trailer_exists."""
        downloads = [
            make_download(1, TRAILER_PATH, file_exists=True),
            make_download(2, OTHER_PATH, file_exists=True),
        ]
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch("api.v1.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.files.download_manager.read_by_media_id", return_value=downloads),
            patch("api.v1.files.download_manager.mark_as_deleted") as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists") as mock_update,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_called_once_with(1)
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_downloads_for_media_does_not_reset(self):
        """If media has no download records at all, trailer_exists is untouched."""
        with (
            patch("api.v1.files._is_path_safe", return_value=True),
            patch("api.v1.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.files.download_manager.read_by_media_id", return_value=[]),
            patch("api.v1.files.download_manager.mark_as_deleted") as mock_mark,
            patch("api.v1.files.media_manager.update_trailer_exists") as mock_update,
        ):
            result = await delete_file_fol(NON_TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_not_called()
        mock_update.assert_not_called()
