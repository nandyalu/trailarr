"""Tests for the delete_file_fol endpoint in api/v1/files.py.

Covers the download-lookup logic added for multi-trailer support:
- download rows matching the deleted path are marked deleted
- download rows alone record whether a trailer exists (Phase 5)
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.files.service import delete_file_or_folder as delete_file_fol

TRAILER_PATH = "/media/Movie (2025)/Trailers/movie-trailer.mkv"
OTHER_PATH = "/media/Movie (2025)/Trailers/movie-trailer2.mkv"
NON_TRAILER_PATH = "/media/Movie (2025)/movie.mkv"
MEDIA_ID = 42


def make_download(id: int, path: str, file_exists: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=id, path=path, file_exists=file_exists)


class TestDeleteFileFolDeletionFailure:
    @pytest.mark.asyncio
    async def test_deletion_failure_skips_db_updates(self):
        with (
            patch("services.files.service.FilesHandler.delete_file_fol", AsyncMock(return_value=False)),
            patch("services.files.service.download_manager.read_by_media_id", MagicMock(return_value=[])) as mock_read,
            patch("services.files.service.download_manager.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is False
        mock_read.assert_not_called()
        mock_mark.assert_not_called()


class TestDeleteFileFolNoMediaId:
    @pytest.mark.asyncio
    async def test_no_media_id_skips_db_updates(self):
        with (
            patch("services.files.service.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("services.files.service.download_manager.read_by_media_id") as mock_read,
            patch("services.files.service.download_manager.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH)  # media_id defaults to -1

        assert result is True
        mock_read.assert_not_called()
        mock_mark.assert_not_called()


class TestDeleteFileFolNonTrailerFile:
    @pytest.mark.asyncio
    async def test_non_trailer_file_skips_db_updates(self):
        """Deleting a file with no matching download record marks nothing deleted."""
        downloads = [make_download(1, TRAILER_PATH)]
        with (
            patch("services.files.service.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("services.files.service.download_manager.read_by_media_id", return_value=downloads),
            patch("services.files.service.download_manager.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(NON_TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_not_called()


class TestDeleteFileFolMarksDownloads:
    @pytest.mark.asyncio
    async def test_matching_download_marked_deleted(self):
        """Deleting a trailer marks its download record as deleted."""
        downloads = [make_download(1, TRAILER_PATH)]
        with (
            patch("services.files.service.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("services.files.service.download_manager.read_by_media_id", return_value=downloads),
            patch("services.files.service.download_manager.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_only_matching_download_marked(self):
        """Deleting one of many trailers marks only the matching download."""
        downloads = [
            make_download(1, TRAILER_PATH, file_exists=True),
            make_download(2, OTHER_PATH, file_exists=True),
        ]
        with (
            patch("services.files.service.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("services.files.service.download_manager.read_by_media_id", return_value=downloads),
            patch("services.files.service.download_manager.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_no_downloads_for_media_marks_nothing(self):
        """If media has no download records at all, nothing is marked deleted."""
        with (
            patch("services.files.service.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("services.files.service.download_manager.read_by_media_id", return_value=[]),
            patch("services.files.service.download_manager.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(NON_TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_not_called()
