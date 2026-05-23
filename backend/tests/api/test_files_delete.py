"""Tests for the delete_file_fol endpoint in api/v1/endpoints/files.py.

Covers the download-lookup logic for multi-trailer support:
- download.file_exists is marked False for matched download records
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from api.v1.endpoints.files import delete_file_fol

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
            patch("api.v1.endpoints.files._is_path_safe", return_value=True),
            patch("api.v1.endpoints.files.FilesHandler.delete_file_fol", AsyncMock(return_value=False)),
            patch("api.v1.endpoints.files.download_repo.read_by_media_id") as mock_read,
            patch("api.v1.endpoints.files.download_repo.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is False
        mock_read.assert_not_called()
        mock_mark.assert_not_called()


class TestDeleteFileFolNoMediaId:
    @pytest.mark.asyncio
    async def test_no_media_id_skips_db_updates(self):
        with (
            patch("api.v1.endpoints.files._is_path_safe", return_value=True),
            patch("api.v1.endpoints.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.endpoints.files.download_repo.read_by_media_id") as mock_read,
            patch("api.v1.endpoints.files.download_repo.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH)  # media_id defaults to -1

        assert result is True
        mock_read.assert_not_called()
        mock_mark.assert_not_called()


class TestDeleteFileFolNonTrailerFile:
    @pytest.mark.asyncio
    async def test_non_trailer_file_skips_db_updates(self):
        """Deleting a file with no matching download record doesn't mark anything."""
        downloads = [make_download(1, TRAILER_PATH)]
        with (
            patch("api.v1.endpoints.files._is_path_safe", return_value=True),
            patch("api.v1.endpoints.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.endpoints.files.download_repo.read_by_media_id", return_value=downloads),
            patch("api.v1.endpoints.files.download_repo.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(NON_TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_not_called()


class TestDeleteFileFolTrailerFile:
    @pytest.mark.asyncio
    async def test_trailer_file_marks_download_deleted(self):
        """Deleting a trailer marks the download record as deleted."""
        downloads = [make_download(1, TRAILER_PATH)]
        with (
            patch("api.v1.endpoints.files._is_path_safe", return_value=True),
            patch("api.v1.endpoints.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.endpoints.files.download_repo.read_by_media_id", return_value=downloads),
            patch("api.v1.endpoints.files.download_repo.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_no_downloads_for_media_does_nothing(self):
        """If media has no download records, nothing is marked deleted."""
        with (
            patch("api.v1.endpoints.files._is_path_safe", return_value=True),
            patch("api.v1.endpoints.files.FilesHandler.delete_file_fol", AsyncMock(return_value=True)),
            patch("api.v1.endpoints.files.download_repo.read_by_media_id", return_value=[]),
            patch("api.v1.endpoints.files.download_repo.mark_as_deleted") as mock_mark,
        ):
            result = await delete_file_fol(NON_TRAILER_PATH, MEDIA_ID)

        assert result is True
        mock_mark.assert_not_called()
