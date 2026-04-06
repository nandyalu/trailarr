"""Tests for trailer.py functions in the download_trailer flow."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from core.download.video_analysis import VideoInfo, StreamInfo
from exceptions import DownloadFailedError


# Fixtures for test data
@pytest.fixture
def mock_media():
    """Create a mock MediaRead object."""
    media = MagicMock()
    media.id = 1
    media.title = "Test Movie"
    media.year = 2024
    media.is_movie = True
    media.folder_path = "/media/movies/Test Movie (2024)"
    media.media_filename = "Test.Movie.2024.1080p.mkv"
    media.youtube_trailer_id = "dQw4w9WgXcQ"
    media.language = "en"
    media.monitor = True
    media.trailer_exists = False
    media.model_dump.return_value = {
        "id": 1,
        "title": "Test Movie",
        "year": 2024,
        "is_movie": True,
        "folder_path": "/media/movies/Test Movie (2024)",
        "media_filename": "Test.Movie.2024.1080p.mkv",
        "youtube_trailer_id": "dQw4w9WgXcQ",
        "language": "en",
    }
    return media


@pytest.fixture
def mock_profile():
    """Create a mock TrailerProfileRead object."""
    profile = MagicMock()
    profile.id = 1
    profile.file_name = "{title}-trailer.{ext}"
    profile.file_format = "mp4"
    profile.folder_enabled = True
    profile.folder_name = "Trailers"
    profile.custom_folder = "{media_folder}"
    profile.video_resolution = 1080
    profile.video_format = "h264"
    profile.audio_format = "aac"
    profile.min_duration = 30
    profile.max_duration = 300
    profile.stop_monitoring = True
    profile.always_search = False
    profile.remove_silence = False
    return profile


@pytest.fixture
def mock_video_info():
    """Create a mock VideoInfo object."""
    return VideoInfo(
        name="test_trailer.mp4",
        file_path="/tmp/test_trailer.mp4",
        format_name="mp4",
        duration_seconds=120,
        duration="0:02:00",
        size=50000000,
        bitrate="3.3 Mbps",
        streams=[
            StreamInfo(
                index=0,
                codec_type="video",
                codec_name="h264",
                coded_height=1080,
                coded_width=1920,
            ),
            StreamInfo(
                index=1,
                codec_type="audio",
                codec_name="aac",
                audio_channels=2,
                sample_rate=48000,
            ),
        ],
        youtube_id="dQw4w9WgXcQ",
        youtube_channel="TestChannel",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# Private functions (__update_media_status, __download_and_verify_trailer)
# are tested through the public download_trailer interface


class TestDownloadTrailer:
    """Tests for download_trailer async function."""

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.trailer_file.move_trailer_to_folder")
    @patch(
        "core.download.trailer.record_new_trailer_download",
        new_callable=AsyncMock,
    )
    @patch("core.download.trailer.event_manager.track_trailer_downloaded")
    @patch("core.download.trailer.media_manager.update_media_status")
    @patch(
        "core.download.trailer.websockets.ws_manager.broadcast",
        new_callable=AsyncMock,
    )
    async def test_successful_download(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        """Successfully downloads trailer and returns True."""
        mock_get_video_id.return_value = "dQw4w9WgXcQ"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/movies/Test/Trailers/trailer.mp4"

        from core.download.trailer import download_trailer

        result = await download_trailer(mock_media, mock_profile)

        assert result is True
        mock_get_video_id.assert_called_once()
        mock_download.assert_called_once()
        mock_verify.assert_called_once()
        mock_move.assert_called_once()
        mock_record.assert_called_once()

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    async def test_raises_error_when_no_video_id(
        self, mock_get_video_id, mock_media, mock_profile
    ):
        """Raises DownloadFailedError when no trailer found."""
        mock_get_video_id.return_value = None

        from core.download.trailer import download_trailer

        with pytest.raises(DownloadFailedError, match="No trailer found"):
            await download_trailer(mock_media, mock_profile)

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.media_manager.update_media_status")
    async def test_retries_on_failure(
        self,
        mock_update_status,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        """Retries download on failure with different video ID."""
        mock_get_video_id.side_effect = ["vid1", "vid2", "vid3"]
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (False, None)

        from core.download.trailer import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=2)

        # Should have tried 3 times (initial + 2 retries)
        assert mock_get_video_id.call_count == 3

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.trailer_file.move_trailer_to_folder")
    @patch(
        "core.download.trailer.record_new_trailer_download",
        new_callable=AsyncMock,
    )
    @patch("core.download.trailer.event_manager.track_trailer_downloaded")
    @patch("core.download.trailer.media_manager.update_media_status")
    @patch(
        "core.download.trailer.websockets.ws_manager.broadcast",
        new_callable=AsyncMock,
    )
    async def test_excludes_existing_trailer_id(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        """Excludes existing trailer ID when trailer_exists."""
        mock_media.trailer_exists = True
        mock_media.youtube_trailer_id = "existing_id"
        mock_get_video_id.return_value = "new_video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from core.download.trailer import download_trailer

        await download_trailer(mock_media, mock_profile)

        # Check that existing ID was passed to exclude
        call_args = mock_get_video_id.call_args
        assert "existing_id" in call_args[0][2]  # exclude list

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.trailer_file.move_trailer_to_folder")
    @patch(
        "core.download.trailer.record_new_trailer_download",
        new_callable=AsyncMock,
    )
    @patch("core.download.trailer.event_manager.track_trailer_downloaded")
    @patch("core.download.trailer.media_manager.update_media_status")
    @patch(
        "core.download.trailer.websockets.ws_manager.broadcast",
        new_callable=AsyncMock,
    )
    async def test_always_search_ignores_existing_id(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        """Ignores existing YouTube ID when always_search is enabled."""
        mock_media.youtube_trailer_id = "existing_id"
        mock_profile.always_search = True
        mock_get_video_id.return_value = "new_video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from core.download.trailer import download_trailer

        await download_trailer(mock_media, mock_profile)

        # media.youtube_trailer_id should have been set to None before search
        mock_get_video_id.assert_called_once()

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.video_analysis.remove_silence_at_end")
    @patch("core.download.trailer.video_analysis.get_media_info")
    @patch("core.download.trailer.trailer_file.move_trailer_to_folder")
    @patch(
        "core.download.trailer.record_new_trailer_download",
        new_callable=AsyncMock,
    )
    @patch("core.download.trailer.event_manager.track_trailer_downloaded")
    @patch("core.download.trailer.media_manager.update_media_status")
    @patch(
        "core.download.trailer.websockets.ws_manager.broadcast",
        new_callable=AsyncMock,
    )
    async def test_removes_silence_when_enabled(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_get_new_info,
        mock_remove_silence,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        """Removes silence from trailer when remove_silence is enabled."""
        mock_profile.remove_silence = True
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_remove_silence.return_value = ("/tmp/trimmed-trailer.mp4", True)
        mock_get_new_info.return_value = mock_video_info
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from core.download.trailer import download_trailer

        await download_trailer(mock_media, mock_profile)

        mock_remove_silence.assert_called_once()
        # Should re-analyze after trimming
        mock_get_new_info.assert_called_once()

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.trailer_file.move_trailer_to_folder")
    @patch(
        "core.download.trailer.record_new_trailer_download",
        new_callable=AsyncMock,
    )
    @patch("core.download.trailer.event_manager.track_trailer_downloaded")
    @patch("core.download.trailer.media_manager.update_media_status")
    @patch(
        "core.download.trailer.websockets.ws_manager.broadcast",
        new_callable=AsyncMock,
    )
    async def test_passes_video_info_to_move_and_record(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        """Passes video_info to move_trailer_to_folder and record_new_trailer_download."""
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from core.download.trailer import download_trailer

        await download_trailer(mock_media, mock_profile)

        # Verify video_info was passed to move_trailer_to_folder
        move_call_args = mock_move.call_args
        assert (
            move_call_args[0][3] == mock_video_info
            or move_call_args.kwargs.get("video_info") == mock_video_info
        )

        # Verify video_info was passed to record_new_trailer_download
        record_call_args = mock_record.call_args
        # Check if video_info is in positional or keyword args
        assert (
            mock_video_info in record_call_args[0]
            or record_call_args.kwargs.get("video_info") == mock_video_info
        )


class TestDownloadTrailerRetryBehavior:
    """Tests for download_trailer retry behavior."""

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.media_manager.update_media_status")
    async def test_excludes_failed_video_id_on_retry(
        self,
        mock_update_status,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        """Adds failed video ID to exclude list on retry."""
        mock_get_video_id.side_effect = ["first_id", "second_id", "third_id"]
        mock_download.side_effect = DownloadFailedError("Download failed")

        from core.download.trailer import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=2)

        # Should have tried 3 times (initial + 2 retries)
        calls = mock_get_video_id.call_args_list
        assert len(calls) == 3

        # Exclude list accumulates failed IDs across retries
        # Second call should have first_id in its exclude list
        second_exclude = calls[1][0][2]
        assert "first_id" in second_exclude

        # Third call should have both first_id and second_id
        third_exclude = calls[2][0][2]
        assert "first_id" in third_exclude
        assert "second_id" in third_exclude

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.media_manager.update_media_status")
    async def test_no_retry_when_retry_count_is_zero(
        self,
        mock_update_status,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        """Doesn't retry when retry_count is 0."""
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test.mp4"
        mock_verify.return_value = (False, None)

        from core.download.trailer import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=0)

        # Should only be called once
        assert mock_get_video_id.call_count == 1


class TestDownloadTrailerMediaStatus:
    """Tests for media status updates during download."""

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.trailer_file.verify_download")
    @patch("core.download.trailer.trailer_file.move_trailer_to_folder")
    @patch(
        "core.download.trailer.record_new_trailer_download",
        new_callable=AsyncMock,
    )
    @patch("core.download.trailer.event_manager.track_trailer_downloaded")
    @patch("core.download.trailer.media_manager.update_media_status")
    @patch(
        "core.download.trailer.websockets.ws_manager.broadcast",
        new_callable=AsyncMock,
    )
    async def test_updates_status_to_downloading_then_downloaded(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        """Updates media status to DOWNLOADING then DOWNLOADED."""
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from core.download.trailer import download_trailer

        await download_trailer(mock_media, mock_profile)

        # Should have been called at least twice (DOWNLOADING and DOWNLOADED)
        assert mock_update_status.call_count >= 2

    @pytest.mark.asyncio
    @patch("core.download.trailer.trailer_search.get_video_id")
    @patch("core.download.trailer.download_video")
    @patch("core.download.trailer.media_manager.update_media_status")
    async def test_updates_status_to_missing_on_final_failure(
        self,
        mock_update_status,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        """Updates media status to MISSING after all retries fail."""
        mock_get_video_id.return_value = "video_id"
        mock_download.side_effect = DownloadFailedError("Download failed")

        from core.download.trailer import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=0)

        # Should update status including MISSING
        assert mock_update_status.call_count >= 1
