"""Tests for pipeline.py download_trailer and _check_plex_trailer functions."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from download.analysis import VideoInfo, StreamInfo
from exceptions import DownloadFailedError


@pytest.fixture
def mock_media():
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
    media.plex_connection_id = None
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
    profile.skip_if_plex_trailer = False
    profile.tmdb_language = ""
    from db.models.trailerprofile import VideoType
    profile.video_type = VideoType.TRAILER
    return profile


@pytest.fixture
def mock_video_info():
    return VideoInfo(
        name="test_trailer.mp4",
        file_path="/tmp/test_trailer.mp4",
        format_name="mp4",
        duration_seconds=120,
        duration="0:02:00",
        size=50000000,
        bitrate="3.3 Mbps",
        streams=[
            StreamInfo(index=0, codec_type="video", codec_name="h264", coded_height=1080, coded_width=1920),
            StreamInfo(index=1, codec_type="audio", codec_name="aac", audio_channels=2, sample_rate=48000),
        ],
        youtube_id="dQw4w9WgXcQ",
        youtube_channel="TestChannel",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestDownloadTrailer:

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.trailer_file.move_trailer_to_folder")
    @patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock)
    @patch("download.pipeline.event_service.track_trailer_downloaded")
    @patch("download.pipeline.media_repo.update_media_status")
    @patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock)
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
        mock_media.youtube_trailer_id = None  # force YouTube search path
        mock_get_video_id.return_value = "dQw4w9WgXcQ"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/movies/Test/Trailers/trailer.mp4"

        from download.pipeline import download_trailer

        result = await download_trailer(mock_media, mock_profile)

        assert result is True
        mock_get_video_id.assert_called_once()
        mock_download.assert_called_once()
        mock_verify.assert_called_once()
        mock_move.assert_called_once()
        mock_record.assert_called_once()

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    async def test_raises_error_when_no_video_id(self, mock_get_video_id, mock_media, mock_profile):
        mock_media.youtube_trailer_id = None  # no cached ID — must search
        mock_get_video_id.return_value = None

        from download.pipeline import download_trailer

        with pytest.raises(DownloadFailedError, match="No trailer found"):
            await download_trailer(mock_media, mock_profile)

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.media_repo.update_media_status")
    async def test_retries_on_failure(
        self,
        mock_update_status,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        mock_media.youtube_trailer_id = None  # force YouTube search on all attempts
        mock_get_video_id.side_effect = ["vid1", "vid2", "vid3"]
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (False, None)

        from download.pipeline import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=2)

        assert mock_get_video_id.call_count == 3

    @pytest.mark.asyncio
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.trailer_file.move_trailer_to_folder")
    @patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock)
    @patch("download.pipeline.event_service.track_trailer_downloaded")
    @patch("download.pipeline.media_repo.update_media_status")
    @patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock)
    async def test_uses_existing_trailer_id_directly(
        self,
        mock_broadcast,
        mock_update_status,
        mock_track_download,
        mock_record,
        mock_move,
        mock_verify,
        mock_download,
        mock_media,
        mock_profile,
        mock_video_info,
    ):
        # When youtube_trailer_id is set and always_search=False, the pipeline uses
        # it directly as the video ID without calling YouTube search.
        mock_media.trailer_exists = True
        mock_media.youtube_trailer_id = "existing_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from download.pipeline import download_trailer

        result = await download_trailer(mock_media, mock_profile)

        assert result is True
        # The video ID passed to the download should be the existing ID.
        assert "existing_id" in mock_download.call_args[0][0]

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.trailer_file.move_trailer_to_folder")
    @patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock)
    @patch("download.pipeline.event_service.track_trailer_downloaded")
    @patch("download.pipeline.media_repo.update_media_status")
    @patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock)
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
        mock_media.youtube_trailer_id = "existing_id"
        mock_profile.always_search = True
        mock_get_video_id.return_value = "new_video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from download.pipeline import download_trailer

        await download_trailer(mock_media, mock_profile)

        mock_get_video_id.assert_called_once()

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.video_analysis.remove_silence_at_end")
    @patch("download.pipeline.video_analysis.get_media_info")
    @patch("download.pipeline.trailer_file.move_trailer_to_folder")
    @patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock)
    @patch("download.pipeline.event_service.track_trailer_downloaded")
    @patch("download.pipeline.media_repo.update_media_status")
    @patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock)
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
        mock_profile.remove_silence = True
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_remove_silence.return_value = ("/tmp/trimmed-trailer.mp4", True)
        mock_get_new_info.return_value = mock_video_info
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from download.pipeline import download_trailer

        await download_trailer(mock_media, mock_profile)

        mock_remove_silence.assert_called_once()
        mock_get_new_info.assert_called_once()

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.trailer_file.move_trailer_to_folder")
    @patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock)
    @patch("download.pipeline.event_service.track_trailer_downloaded")
    @patch("download.pipeline.media_repo.update_media_status")
    @patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock)
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
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from download.pipeline import download_trailer

        await download_trailer(mock_media, mock_profile)

        move_call_args = mock_move.call_args
        assert (
            move_call_args[0][3] == mock_video_info
            or move_call_args.kwargs.get("video_info") == mock_video_info
        )

        record_call_args = mock_record.call_args
        assert (
            mock_video_info in record_call_args[0]
            or record_call_args.kwargs.get("video_info") == mock_video_info
        )

    @pytest.mark.asyncio
    @patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock)
    async def test_skips_download_when_plex_has_trailer(self, mock_check_plex, mock_media, mock_profile):
        mock_check_plex.return_value = True
        mock_profile.skip_if_plex_trailer = True

        from download.pipeline import download_trailer

        result = await download_trailer(mock_media, mock_profile)

        assert result is False
        mock_check_plex.assert_called_once_with(mock_media, mock_profile)

    @pytest.mark.asyncio
    @patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock)
    @patch("download.pipeline.trailer_search.get_video_id")
    async def test_proceeds_when_plex_has_no_trailer(
        self, mock_get_video_id, mock_check_plex, mock_media, mock_profile
    ):
        mock_media.youtube_trailer_id = None  # force YouTube search path
        mock_check_plex.return_value = False
        mock_get_video_id.return_value = None

        from download.pipeline import download_trailer

        with pytest.raises(Exception):
            await download_trailer(mock_media, mock_profile)

        mock_get_video_id.assert_called_once()


class TestDownloadTrailerRetryBehavior:

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.media_repo.update_media_status")
    async def test_excludes_failed_video_id_on_retry(
        self,
        mock_update_status,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        mock_media.youtube_trailer_id = None  # force YouTube search on all attempts
        mock_get_video_id.side_effect = ["first_id", "second_id", "third_id"]
        mock_download.side_effect = DownloadFailedError("Download failed")

        from download.pipeline import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=2)

        calls = mock_get_video_id.call_args_list
        assert len(calls) == 3

        second_exclude = calls[1][0][2]
        assert "first_id" in second_exclude

        third_exclude = calls[2][0][2]
        assert "first_id" in third_exclude
        assert "second_id" in third_exclude

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.media_repo.update_media_status")
    async def test_no_retry_when_retry_count_is_zero(
        self,
        mock_update_status,
        mock_verify,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        mock_media.youtube_trailer_id = None  # force YouTube search path
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test.mp4"
        mock_verify.return_value = (False, None)

        from download.pipeline import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=0)

        assert mock_get_video_id.call_count == 1


class TestDownloadTrailerMediaStatus:

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.trailer_file.verify_download")
    @patch("download.pipeline.trailer_file.move_trailer_to_folder")
    @patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock)
    @patch("download.pipeline.event_service.track_trailer_downloaded")
    @patch("download.pipeline.media_repo.update_media_status")
    @patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock)
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
        mock_get_video_id.return_value = "video_id"
        mock_download.return_value = "/tmp/test-trailer.mp4"
        mock_verify.return_value = (True, mock_video_info)
        mock_move.return_value = "/media/Test/Trailers/trailer.mp4"

        from download.pipeline import download_trailer

        await download_trailer(mock_media, mock_profile)

        assert mock_update_status.call_count >= 2

    @pytest.mark.asyncio
    @patch("download.pipeline.trailer_search.get_video_id")
    @patch("download.pipeline.download_video")
    @patch("download.pipeline.media_repo.update_media_status")
    async def test_updates_status_to_missing_on_final_failure(
        self,
        mock_update_status,
        mock_download,
        mock_get_video_id,
        mock_media,
        mock_profile,
    ):
        mock_get_video_id.return_value = "video_id"
        mock_download.side_effect = DownloadFailedError("Download failed")

        from download.pipeline import download_trailer

        with pytest.raises(DownloadFailedError):
            await download_trailer(mock_media, mock_profile, retry_count=0)

        assert mock_update_status.call_count >= 1


class TestCheckPlexTrailer:

    @pytest.fixture
    def mock_media_plex(self):
        media = MagicMock()
        media.id = 1
        media.title = "Test Movie"
        media.plex_connection_id = 10
        media.plex_rating_key = "123"
        media.plex_trailer = None
        return media

    @pytest.fixture
    def mock_profile_plex(self):
        profile = MagicMock()
        profile.skip_if_plex_trailer = True
        profile.skip_if_plex_trailer_resolution = 0
        return profile

    @pytest.mark.asyncio
    async def test_returns_false_when_flag_disabled(self, mock_media_plex, mock_profile_plex):
        mock_profile_plex.skip_if_plex_trailer = False
        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_plex_connection(self, mock_media_plex, mock_profile_plex):
        mock_media_plex.plex_connection_id = None
        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_plex_rating_key(self, mock_media_plex, mock_profile_plex):
        mock_media_plex.plex_rating_key = None
        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)
        assert result is False

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("integrations.plex.client.PlexAPI.get_library_item_extras", new_callable=AsyncMock)
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_returns_true_and_updates_db_when_trailer_found(
        self,
        mock_update_plex_trailer,
        mock_get_extras,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        from db.models.connection import ArrType
        from integrations.plex.models import PlexMediaExtra

        mock_conn = MagicMock()
        mock_conn.arr_type = ArrType.PLEX
        mock_conn.url = "http://plex"
        mock_conn.api_key = "token"
        mock_read_conn.return_value = mock_conn

        trailer_extra = PlexMediaExtra(subtype="trailer", title="Official Trailer")
        mock_get_extras.return_value = [trailer_extra]

        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is True
        mock_update_plex_trailer.assert_called_once_with(mock_media_plex.id, True)

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("integrations.plex.client.PlexAPI.get_library_item_extras", new_callable=AsyncMock)
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_returns_false_and_updates_db_when_no_trailer(
        self,
        mock_update_plex_trailer,
        mock_get_extras,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        from db.models.connection import ArrType
        from integrations.plex.models import PlexMediaExtra

        mock_conn = MagicMock()
        mock_conn.arr_type = ArrType.PLEX
        mock_conn.url = "http://plex"
        mock_conn.api_key = "token"
        mock_read_conn.return_value = mock_conn

        featurette = PlexMediaExtra(subtype="featurette", title="Behind the Scenes")
        mock_get_extras.return_value = [featurette]

        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is False
        mock_update_plex_trailer.assert_called_once_with(mock_media_plex.id, False)

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("integrations.plex.client.PlexAPI.get_library_item_extras", new_callable=AsyncMock)
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_returns_false_when_connection_is_not_plex(
        self,
        mock_update_plex_trailer,
        mock_get_extras,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        from db.models.connection import ArrType

        mock_conn = MagicMock()
        mock_conn.arr_type = ArrType.RADARR
        mock_read_conn.return_value = mock_conn

        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is False
        mock_get_extras.assert_not_called()
        mock_update_plex_trailer.assert_not_called()

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_returns_false_gracefully_on_exception(
        self,
        mock_update_plex_trailer,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        mock_read_conn.side_effect = Exception("DB error")
        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is False
        mock_update_plex_trailer.assert_not_called()

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("integrations.plex.client.PlexAPI.get_library_item_extras", new_callable=AsyncMock)
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_ignores_local_file_trailers(
        self,
        mock_update_plex_trailer,
        mock_get_extras,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        from db.models.connection import ArrType
        from integrations.plex.models import PlexMediaExtra

        mock_conn = MagicMock()
        mock_conn.arr_type = ArrType.PLEX
        mock_conn.url = "http://plex"
        mock_conn.api_key = "token"
        mock_read_conn.return_value = mock_conn

        local_trailer = PlexMediaExtra(subtype="trailer", title="My Trailer", guid="file:///media/trailers/t.mkv")
        mock_get_extras.return_value = [local_trailer]

        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is False
        mock_update_plex_trailer.assert_called_once_with(mock_media_plex.id, False)

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("integrations.plex.client.PlexAPI.get_library_item_extras", new_callable=AsyncMock)
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_resolution_threshold_met_returns_true(
        self,
        mock_update_plex_trailer,
        mock_get_extras,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        from db.models.connection import ArrType
        from integrations.plex.models import PlexMediaExtra

        mock_conn = MagicMock()
        mock_conn.arr_type = ArrType.PLEX
        mock_conn.url = "http://plex"
        mock_conn.api_key = "token"
        mock_read_conn.return_value = mock_conn

        mock_profile_plex.skip_if_plex_trailer_resolution = 720
        hd_trailer = PlexMediaExtra.model_construct(subtype="trailer", guid="iva://remote/123", resolution=1080)
        mock_get_extras.return_value = [hd_trailer]

        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is True

    @pytest.mark.asyncio
    @patch("download.pipeline.connection_repo.read")
    @patch("integrations.plex.client.PlexAPI.get_library_item_extras", new_callable=AsyncMock)
    @patch("download.pipeline.media_repo.update_plex_trailer")
    async def test_resolution_threshold_not_met_returns_false(
        self,
        mock_update_plex_trailer,
        mock_get_extras,
        mock_read_conn,
        mock_media_plex,
        mock_profile_plex,
    ):
        from db.models.connection import ArrType
        from integrations.plex.models import PlexMediaExtra

        mock_conn = MagicMock()
        mock_conn.arr_type = ArrType.PLEX
        mock_conn.url = "http://plex"
        mock_conn.api_key = "token"
        mock_read_conn.return_value = mock_conn

        mock_profile_plex.skip_if_plex_trailer_resolution = 1080
        sd_trailer = PlexMediaExtra.model_construct(subtype="trailer", guid="iva://remote/456", resolution=480)
        mock_get_extras.return_value = [sd_trailer]

        from download.pipeline import _check_plex_trailer

        result = await _check_plex_trailer(mock_media_plex, mock_profile_plex)

        assert result is False
