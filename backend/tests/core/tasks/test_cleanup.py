"""Tests for the trailer_cleanup function in core/tasks/cleanup.py"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core.tasks.cleanup import trailer_cleanup, delete_trailer


def create_mock_download(
    download_id: int = 1,
    path: str = "/path/to/trailer.mkv",
    file_exists: bool = True,
) -> SimpleNamespace:
    """Create a mock download object for testing."""
    return SimpleNamespace(
        id=download_id,
        path=path,
        file_exists=file_exists,
    )


def create_mock_media(
    media_id: int = 1,
    title: str = "Test Media",
    downloads: list | None = None,
) -> SimpleNamespace:
    """Create a mock media object for testing."""
    return SimpleNamespace(
        id=media_id,
        title=title,
        downloads=downloads or [],
    )


class TestDeleteTrailer:
    """Tests for the delete_trailer function."""

    @pytest.mark.asyncio
    async def test_delete_trailer_success(self):
        """Test successful trailer deletion."""
        trailer_path = "/path/to/trailer.mkv"
        download_id = 1

        with (
            patch(
                "core.tasks.cleanup.FilesHandler.delete_file",
                new_callable=AsyncMock,
            ) as mock_delete,
            patch(
                "core.tasks.cleanup.download_manager.mark_as_deleted"
            ) as mock_mark_deleted,
        ):
            result = await delete_trailer(trailer_path, download_id)

            mock_delete.assert_called_once_with(trailer_path)
            mock_mark_deleted.assert_called_once_with(download_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_trailer_with_different_paths(self):
        """Test deletion with various path formats."""
        test_cases = [
            ("/media/movies/Test Movie (2025)/trailer.mkv", 1),
            ("/media/tv/Show/Season 1/trailer.mkv", 42),
            ("/path/with spaces/trailer file.mkv", 100),
        ]

        for trailer_path, download_id in test_cases:
            with (
                patch(
                    "core.tasks.cleanup.FilesHandler.delete_file",
                    new_callable=AsyncMock,
                ) as mock_delete,
                patch(
                    "core.tasks.cleanup.download_manager.mark_as_deleted"
                ) as mock_mark_deleted,
            ):
                await delete_trailer(trailer_path, download_id)

                mock_delete.assert_called_once_with(trailer_path)
                mock_mark_deleted.assert_called_once_with(download_id)


class TestTrailerCleanup:
    """Tests for the trailer_cleanup function."""

    @pytest.mark.asyncio
    async def test_cleanup_empty_media_list(self):
        """Test cleanup when no media items exist."""
        with patch(
            "core.tasks.cleanup.media_manager.read_all_generator"
        ) as mock_read:
            mock_read.return_value = iter([])

            result = await trailer_cleanup()

            assert result is None
            mock_read.assert_called_once_with(downloaded_only=True)

    @pytest.mark.asyncio
    async def test_cleanup_media_without_downloads(self):
        """Test cleanup for media with no downloads triggers update."""
        media = create_mock_media(
            media_id=1, title="No Downloads", downloads=[]
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.media_manager.update_no_trailers_exist"
            ) as mock_update,
        ):
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_update.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_cleanup_skips_already_deleted_downloads(self):
        """Test that downloads marked as not existing are skipped."""
        download = create_mock_download(
            download_id=1,
            path="/path/to/trailer.mkv",
            file_exists=False,
        )
        media = create_mock_media(
            media_id=1,
            title="Test Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch("core.tasks.cleanup.aiofiles.os.path.exists") as mock_exists,
            patch("core.tasks.cleanup.video_analysis") as mock_video,
        ):
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_exists.assert_not_called()
            mock_video.verify_trailer_streams.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_marks_missing_file_as_deleted(self):
        """Test that files not found on disk are marked as deleted."""
        download = create_mock_download(
            download_id=5,
            path="/missing/trailer.mkv",
            file_exists=True,
        )
        media = create_mock_media(
            media_id=2,
            title="Missing File Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "core.tasks.cleanup.download_manager.mark_as_deleted"
            ) as mock_mark_deleted,
        ):
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_mark_deleted.assert_called_once_with(5)
            assert download.file_exists is False

    @pytest.mark.asyncio
    async def test_cleanup_skips_download_with_empty_path(self):
        """Test that downloads with empty paths are marked as deleted."""
        download = create_mock_download(
            download_id=3,
            path="",
            file_exists=True,
        )
        media = create_mock_media(
            media_id=1,
            title="Empty Path Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.download_manager.mark_as_deleted"
            ) as mock_mark_deleted,
        ):
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_mark_deleted.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_cleanup_skips_when_verification_returns_none(self):
        """Test that files that cannot be analyzed are skipped."""
        download = create_mock_download(
            download_id=1,
            path="/path/to/unanalyzable.mkv",
            file_exists=True,
        )
        media = create_mock_media(
            media_id=1,
            title="Unanalyzable Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                return_value=None,
            ),
            patch(
                "core.tasks.cleanup.delete_trailer",
                new_callable=AsyncMock,
            ) as mock_delete_trailer,
        ):
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_delete_trailer.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_deletes_failed_trailer_when_enabled(self):
        """Test that corrupted trailers are deleted when setting is enabled."""
        download = create_mock_download(
            download_id=7,
            path="/path/to/corrupted.mkv",
            file_exists=True,
        )
        media = create_mock_media(
            media_id=3,
            title="Corrupted Trailer Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                return_value=False,
            ),
            patch("core.tasks.cleanup.app_settings") as mock_settings,
            patch(
                "core.tasks.cleanup.delete_trailer",
                new_callable=AsyncMock,
            ) as mock_delete_trailer,
        ):
            mock_settings.delete_corrupted_trailers = True
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_delete_trailer.assert_called_once_with(
                "/path/to/corrupted.mkv", 7
            )
            assert download.file_exists is False

    @pytest.mark.asyncio
    async def test_cleanup_skips_deletion_when_disabled(self):
        """Test that corrupted trailers are not deleted when setting is disabled."""
        download = create_mock_download(
            download_id=8,
            path="/path/to/corrupted.mkv",
            file_exists=True,
        )
        media = create_mock_media(
            media_id=4,
            title="Corrupted No Delete Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                return_value=False,
            ),
            patch("core.tasks.cleanup.app_settings") as mock_settings,
            patch(
                "core.tasks.cleanup.delete_trailer",
                new_callable=AsyncMock,
            ) as mock_delete_trailer,
        ):
            mock_settings.delete_corrupted_trailers = False
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_delete_trailer.assert_not_called()
            assert download.file_exists is False

    @pytest.mark.asyncio
    async def test_cleanup_skips_verified_trailers(self):
        """Test that valid trailers are not modified."""
        download = create_mock_download(
            download_id=10,
            path="/path/to/valid.mkv",
            file_exists=True,
        )
        media = create_mock_media(
            media_id=5,
            title="Valid Trailer Media",
            downloads=[download],
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.delete_trailer",
                new_callable=AsyncMock,
            ) as mock_delete_trailer,
            patch(
                "core.tasks.cleanup.download_manager.mark_as_deleted"
            ) as mock_mark_deleted,
        ):
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            mock_delete_trailer.assert_not_called()
            mock_mark_deleted.assert_not_called()
            assert download.file_exists is True

    @pytest.mark.asyncio
    async def test_cleanup_processes_multiple_media_items(self):
        """Test cleanup processes multiple media items correctly."""
        download1 = create_mock_download(download_id=1, file_exists=True)
        download2 = create_mock_download(download_id=2, file_exists=True)
        download3 = create_mock_download(download_id=3, file_exists=True)

        media1 = create_mock_media(
            media_id=1, title="Media 1", downloads=[download1]
        )
        media2 = create_mock_media(
            media_id=2, title="Media 2", downloads=[download2]
        )
        media3 = create_mock_media(
            media_id=3, title="Media 3", downloads=[download3]
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                return_value=True,
            ),
        ):
            mock_read.return_value = iter([media1, media2, media3])

            result = await trailer_cleanup()

            assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_processes_multiple_downloads_per_media(self):
        """Test cleanup handles multiple downloads for a single media item."""
        download1 = create_mock_download(
            download_id=1,
            path="/path/to/valid.mkv",
            file_exists=True,
        )
        download2 = create_mock_download(
            download_id=2,
            path="/path/to/corrupted.mkv",
            file_exists=True,
        )
        download3 = create_mock_download(
            download_id=3,
            path="/path/to/missing.mkv",
            file_exists=True,
        )

        media = create_mock_media(
            media_id=1,
            title="Multi Download Media",
            downloads=[download1, download2, download3],
        )

        async def mock_exists(path):
            return path != "/path/to/missing.mkv"

        def mock_verify(path):
            if path == "/path/to/valid.mkv":
                return True
            if path == "/path/to/corrupted.mkv":
                return False
            return None

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                side_effect=mock_exists,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                side_effect=mock_verify,
            ),
            patch("core.tasks.cleanup.app_settings") as mock_settings,
            patch(
                "core.tasks.cleanup.delete_trailer",
                new_callable=AsyncMock,
            ) as mock_delete_trailer,
            patch(
                "core.tasks.cleanup.download_manager.mark_as_deleted"
            ) as mock_mark_deleted,
        ):
            mock_settings.delete_corrupted_trailers = True
            mock_read.return_value = iter([media])

            result = await trailer_cleanup()

            assert result is None
            # Missing file should be marked as deleted
            mock_mark_deleted.assert_called_once_with(3)
            # Corrupted file should be deleted via delete_trailer
            mock_delete_trailer.assert_called_once_with(
                "/path/to/corrupted.mkv", 2
            )

    @pytest.mark.asyncio
    async def test_cleanup_mixed_scenario(self):
        """Test cleanup with a mix of different scenarios."""
        # Media with no downloads
        media_no_downloads = create_mock_media(
            media_id=1, title="No Downloads", downloads=[]
        )

        # Media with already deleted download
        deleted_download = create_mock_download(
            download_id=2, file_exists=False
        )
        media_deleted = create_mock_media(
            media_id=2, title="Deleted", downloads=[deleted_download]
        )

        # Media with valid trailer
        valid_download = create_mock_download(
            download_id=3,
            path="/path/valid.mkv",
            file_exists=True,
        )
        media_valid = create_mock_media(
            media_id=3, title="Valid", downloads=[valid_download]
        )

        with (
            patch(
                "core.tasks.cleanup.media_manager.read_all_generator"
            ) as mock_read,
            patch(
                "core.tasks.cleanup.media_manager.update_no_trailers_exist"
            ) as mock_update_no_trailers,
            patch(
                "core.tasks.cleanup.aiofiles.os.path.exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "core.tasks.cleanup.video_analysis.verify_trailer_streams",
                return_value=True,
            ),
        ):
            mock_read.return_value = iter(
                [
                    media_no_downloads,
                    media_deleted,
                    media_valid,
                ]
            )

            result = await trailer_cleanup()

            assert result is None
            mock_update_no_trailers.assert_called_once_with(1)
