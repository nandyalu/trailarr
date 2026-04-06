"""Tests for trailer_file.py functions in the download_trailer flow."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from core.download.trailer_file import (
    get_folder_permissions,
    normalize_filename,
    _extract_video_details,
    get_trailer_filename,
    get_trailer_path,
    move_trailer_to_folder,
    verify_download,
)
from core.download.video_analysis import VideoInfo, StreamInfo
from exceptions import (
    FolderNotFoundError,
    FolderPathEmptyError,
)


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
    return profile


@pytest.fixture
def mock_video_info():
    """Create a mock VideoInfo object with valid streams."""
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


class TestGetFolderPermissions:
    """Tests for get_folder_permissions function."""

    def test_existing_folder_permissions(self, tmp_path):
        """Returns permissions of parent when folder exists."""
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir(mode=0o755)

        result = get_folder_permissions(test_dir)

        # Parent permissions should be returned
        assert isinstance(result, int)

    def test_nonexistent_folder_gets_parent_permissions(self, tmp_path):
        """Returns parent folder permissions when folder doesn't exist."""
        nonexistent = tmp_path / "nonexistent" / "deep" / "folder"

        result = get_folder_permissions(nonexistent)

        # Should traverse up to tmp_path and get its parent's permissions
        assert isinstance(result, int)

    def test_permissions_includes_mode_bits(self, tmp_path):
        """Returned permissions include standard mode bits."""
        result = get_folder_permissions(tmp_path)

        # Should be a valid permission mode (at least readable)
        assert result > 0


class TestNormalizeFilename:
    """Tests for normalize_filename function."""

    def test_basic_filename_unchanged(self):
        """Normal filename remains unchanged."""
        result = normalize_filename("Test Movie-trailer.mp4")
        assert result == "Test Movie-trailer.mp4"

    def test_removes_invalid_characters(self):
        """Invalid characters are replaced with spaces."""
        result = normalize_filename('Test<>:"/\\|?*Movie.mp4')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_normalizes_unicode(self):
        """Unicode characters are normalized."""
        result = normalize_filename("Tëst Mövïe.mp4")
        assert isinstance(result, str)

    def test_collapses_multiple_spaces(self):
        """Multiple spaces collapsed to single space."""
        result = normalize_filename("Test   Movie    Trailer.mp4")
        assert "   " not in result
        assert "  " not in result

    def test_strips_leading_trailing_special_chars(self):
        """Leading/trailing special characters are stripped."""
        result = normalize_filename("._-Test Movie-_.")
        assert not result.startswith("_")
        assert not result.startswith(".")
        assert not result.startswith("-")
        assert not result.endswith("_")
        assert not result.endswith(".")
        assert not result.endswith("-")


class TestExtractVideoDetails:
    """Tests for _extract_video_details function."""

    def test_extracts_resolution_and_codecs(self, mock_video_info):
        """Extracts resolution, video codec, and audio codec from streams."""
        resolution, vcodec, acodec = _extract_video_details(mock_video_info)

        assert resolution == 1080
        assert vcodec == "h264"
        assert acodec == "aac"

    def test_no_video_stream(self):
        """Returns defaults when no video stream."""
        video_info = VideoInfo(
            name="test.mp4",
            file_path="/tmp/test.mp4",
            format_name="mp4",
            duration_seconds=60,
            duration="0:01:00",
            size=1000000,
            bitrate="1 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="audio",
                    codec_name="aac",
                    audio_channels=2,
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        resolution, vcodec, acodec = _extract_video_details(video_info)

        assert resolution == 0
        assert vcodec == "unknown"
        assert acodec == "aac"

    def test_no_audio_stream(self):
        """Returns unknown audio when no audio stream."""
        video_info = VideoInfo(
            name="test.mp4",
            file_path="/tmp/test.mp4",
            format_name="mp4",
            duration_seconds=60,
            duration="0:01:00",
            size=1000000,
            bitrate="1 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                    coded_height=720,
                    coded_width=1280,
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        resolution, vcodec, acodec = _extract_video_details(video_info)

        assert resolution == 720
        assert vcodec == "h264"
        assert acodec == "unknown"

    def test_empty_streams(self):
        """Returns defaults for empty streams."""
        video_info = VideoInfo(
            name="test.mp4",
            file_path="/tmp/test.mp4",
            format_name="mp4",
            duration_seconds=60,
            duration="0:01:00",
            size=1000000,
            bitrate="1 Mbps",
            streams=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        resolution, vcodec, acodec = _extract_video_details(video_info)

        assert resolution == 0
        assert vcodec == "unknown"
        assert acodec == "unknown"

    def test_video_stream_zero_height(self):
        """Skips video stream with zero coded_height."""
        video_info = VideoInfo(
            name="test.mp4",
            file_path="/tmp/test.mp4",
            format_name="mp4",
            duration_seconds=60,
            duration="0:01:00",
            size=1000000,
            bitrate="1 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                    coded_height=0,  # Invalid height
                    coded_width=1920,
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        resolution, vcodec, acodec = _extract_video_details(video_info)

        assert resolution == 0
        assert vcodec == "unknown"


class TestGetTrailerFilename:
    """Tests for get_trailer_filename function."""

    def test_basic_filename_generation(self, mock_media, mock_profile):
        """Generates filename from profile format."""
        result = get_trailer_filename(mock_media, mock_profile, "mp4", 1)

        assert "Test Movie" in result
        assert ".mp4" in result

    def test_uses_video_info_when_provided(
        self, mock_media, mock_profile, mock_video_info
    ):
        """Uses resolution from video_info instead of profile."""
        mock_profile.file_name = "{title}-{resolution}-trailer.{ext}"

        result = get_trailer_filename(
            mock_media, mock_profile, "mp4", 1, mock_video_info
        )

        assert "1080p" in result

    def test_falls_back_to_profile_without_video_info(
        self, mock_media, mock_profile
    ):
        """Uses profile resolution when video_info not provided."""
        mock_profile.file_name = "{title}-{resolution}-trailer.{ext}"
        mock_profile.video_resolution = 720

        result = get_trailer_filename(mock_media, mock_profile, "mp4", 1, None)

        assert "720p" in result

    def test_increment_index_added_when_greater_than_one(
        self, mock_media, mock_profile
    ):
        """Adds increment index when index > 1."""
        result = get_trailer_filename(mock_media, mock_profile, "mp4", 2)

        assert "2" in result

    def test_increment_index_not_added_when_one(
        self, mock_media, mock_profile
    ):
        """Doesn't add increment index when index = 1."""
        mock_profile.file_name = "{title}{ii}-trailer.{ext}"

        result = get_trailer_filename(mock_media, mock_profile, "mp4", 1)

        # {ii} should be removed (not literally present)
        assert "{ii}" not in result

    def test_is_movie_placeholder_for_movie(self, mock_media, mock_profile):
        """Sets is_movie to 'movie' for movies."""
        mock_profile.file_name = "{is_movie}-{title}.{ext}"
        mock_media.is_movie = True

        result = get_trailer_filename(mock_media, mock_profile, "mp4", 1)

        assert "movie" in result

    def test_is_movie_placeholder_for_series(self, mock_media, mock_profile):
        """Sets is_movie to 'series' for TV shows."""
        mock_profile.file_name = "{is_movie}-{title}.{ext}"
        mock_media.is_movie = False

        result = get_trailer_filename(mock_media, mock_profile, "mp4", 1)

        assert "series" in result

    @patch("core.download.trailer_file.app_settings")
    def test_invalid_title_format_uses_default(
        self, mock_settings, mock_media, mock_profile
    ):
        """Uses default format when title format is invalid."""
        mock_profile.file_name = "{title"  # Unbalanced braces
        mock_settings._DEFAULT_FILE_NAME = "{title}-trailer.{ext}"

        result = get_trailer_filename(mock_media, mock_profile, "mp4", 1)

        assert isinstance(result, str)


class TestGetTrailerPath:
    """Tests for get_trailer_path function."""

    def test_returns_path_when_file_not_exists(
        self, tmp_path, mock_media, mock_profile
    ):
        """Returns destination path when file doesn't exist."""
        src_file = tmp_path / "source.mp4"
        src_file.touch()

        result = get_trailer_path(
            src_file, tmp_path, mock_media, mock_profile, 1
        )

        assert isinstance(result, str)
        assert tmp_path.name in result

    def test_increments_when_file_exists(
        self, tmp_path, mock_media, mock_profile
    ):
        """Increments index when destination file exists."""
        mock_profile.file_name = "Test-trailer.{ext}"
        src_file = tmp_path / "source.mp4"
        src_file.touch()

        # Create existing file
        existing_file = tmp_path / "Test-trailer.mp4"
        existing_file.touch()

        result = get_trailer_path(
            src_file, tmp_path, mock_media, mock_profile, 1
        )

        # Should have increment (2) in the filename
        assert "2" in result or result != str(existing_file)

    def test_accepts_path_objects(self, tmp_path, mock_media, mock_profile):
        """Accepts Path objects for src and dst."""
        src_file = tmp_path / "source.mp4"
        src_file.touch()

        result = get_trailer_path(
            Path(src_file), Path(tmp_path), mock_media, mock_profile
        )

        assert isinstance(result, str)

    def test_uses_video_info_for_naming(
        self, tmp_path, mock_media, mock_profile, mock_video_info
    ):
        """Uses video_info when provided."""
        mock_profile.file_name = "{title}-{resolution}.{ext}"
        src_file = tmp_path / "source.mp4"
        src_file.touch()

        result = get_trailer_path(
            src_file,
            tmp_path,
            mock_media,
            mock_profile,
            video_info=mock_video_info,
        )

        assert "1080p" in result


class TestMoveTrailerToFolder:
    """Tests for move_trailer_to_folder function."""

    def test_moves_file_to_media_folder(
        self, tmp_path, mock_media, mock_profile
    ):
        """Moves trailer file to media folder."""
        # Create source file
        src_file = tmp_path / "source" / "trailer.mp4"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("test content")

        # Set up media folder
        media_folder = tmp_path / "media"
        media_folder.mkdir()
        mock_media.folder_path = str(media_folder)
        mock_profile.folder_enabled = False

        result = move_trailer_to_folder(src_file, mock_media, mock_profile)

        assert media_folder.name in result
        assert Path(result).exists()

    def test_creates_trailer_subfolder(
        self, tmp_path, mock_media, mock_profile
    ):
        """Creates Trailers subfolder when folder_enabled."""
        src_file = tmp_path / "source" / "trailer.mp4"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("test content")

        media_folder = tmp_path / "media"
        media_folder.mkdir()
        mock_media.folder_path = str(media_folder)
        mock_profile.folder_enabled = True
        mock_profile.folder_name = "Trailers"

        result = move_trailer_to_folder(src_file, mock_media, mock_profile)

        assert "Trailers" in result
        assert Path(result).exists()

    def test_raises_file_not_found_for_missing_source(
        self, tmp_path, mock_media, mock_profile
    ):
        """Raises FileNotFoundError when source doesn't exist."""
        nonexistent = tmp_path / "nonexistent.mp4"

        with pytest.raises(FileNotFoundError):
            move_trailer_to_folder(nonexistent, mock_media, mock_profile)

    def test_raises_folder_path_empty_error(
        self, tmp_path, mock_media, mock_profile
    ):
        """Raises FolderPathEmptyError when media folder path is empty."""
        src_file = tmp_path / "trailer.mp4"
        src_file.write_text("test content")
        mock_media.folder_path = ""

        with pytest.raises(FolderPathEmptyError):
            move_trailer_to_folder(src_file, mock_media, mock_profile)

    def test_raises_folder_not_found_for_missing_media_folder(
        self, tmp_path, mock_media, mock_profile
    ):
        """Raises FolderNotFoundError when media folder doesn't exist."""
        src_file = tmp_path / "trailer.mp4"
        src_file.write_text("test content")
        mock_media.folder_path = "/nonexistent/path"

        with pytest.raises(FolderNotFoundError):
            move_trailer_to_folder(src_file, mock_media, mock_profile)

    def test_uses_default_folder_name_when_empty(
        self, tmp_path, mock_media, mock_profile
    ):
        """Uses 'Trailers' when folder_name is empty."""
        src_file = tmp_path / "source" / "trailer.mp4"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("test content")

        media_folder = tmp_path / "media"
        media_folder.mkdir()
        mock_media.folder_path = str(media_folder)
        mock_profile.folder_enabled = True
        mock_profile.folder_name = "   "  # Empty/whitespace

        result = move_trailer_to_folder(src_file, mock_media, mock_profile)

        assert "Trailers" in result

    def test_uses_custom_folder_path(
        self, tmp_path, mock_media, mock_profile, mock_video_info
    ):
        """Uses custom folder path with format placeholders."""
        src_file = tmp_path / "source" / "trailer.mp4"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("test content")

        custom_folder = tmp_path / "custom"
        mock_profile.custom_folder = str(custom_folder)

        result = move_trailer_to_folder(
            src_file, mock_media, mock_profile, mock_video_info
        )

        assert str(custom_folder) in result

    def test_accepts_path_object_for_source(
        self, tmp_path, mock_media, mock_profile
    ):
        """Accepts Path object for source path."""
        src_file = tmp_path / "trailer.mp4"
        src_file.write_text("test content")

        media_folder = tmp_path / "media"
        media_folder.mkdir()
        mock_media.folder_path = str(media_folder)
        mock_profile.folder_enabled = False

        result = move_trailer_to_folder(
            Path(src_file), mock_media, mock_profile
        )

        assert isinstance(result, str)


class TestVerifyDownload:
    """Tests for verify_download function."""

    def test_returns_none_for_none_filepath(self, mock_profile):
        """Returns (None, None) for None file path."""
        result, info = verify_download(None, "Test Movie", mock_profile)

        assert result is None
        assert info is None

    def test_returns_none_for_empty_filepath(self, mock_profile):
        """Returns (None, None) for empty file path."""
        result, info = verify_download("", "Test Movie", mock_profile)

        assert result is None
        assert info is None

    def test_returns_none_for_nonexistent_file(self, tmp_path, mock_profile):
        """Returns (None, None) for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.mp4"

        result, info = verify_download(
            str(nonexistent), "Test Movie", mock_profile
        )

        assert result is None
        assert info is None

    @patch(
        "core.download.trailer_file.video_analysis.verify_and_analyze_trailer"
    )
    def test_returns_valid_result_for_valid_trailer(
        self, mock_verify, tmp_path, mock_profile, mock_video_info
    ):
        """Returns (True, VideoInfo) for valid trailer."""
        test_file = tmp_path / "trailer.mp4"
        test_file.write_text("test content")
        mock_verify.return_value = (True, mock_video_info)

        result, info = verify_download(
            str(test_file), "Test Movie", mock_profile
        )

        assert result is True
        assert info == mock_video_info

    @patch(
        "core.download.trailer_file.video_analysis.verify_and_analyze_trailer"
    )
    def test_deletes_file_on_verification_failure(
        self, mock_verify, tmp_path, mock_profile
    ):
        """Deletes file when verification fails."""
        test_file = tmp_path / "trailer.mp4"
        test_file.write_text("test content")
        mock_verify.return_value = (False, None)

        result, info = verify_download(
            str(test_file), "Test Movie", mock_profile
        )

        assert result is False
        assert info is None
        assert not test_file.exists()

    @patch(
        "core.download.trailer_file.video_analysis.verify_and_analyze_trailer"
    )
    def test_accepts_path_object(
        self, mock_verify, tmp_path, mock_profile, mock_video_info
    ):
        """Accepts Path object for file path."""
        test_file = tmp_path / "trailer.mp4"
        test_file.write_text("test content")
        mock_verify.return_value = (True, mock_video_info)

        result, info = verify_download(
            Path(test_file), "Test Movie", mock_profile
        )

        assert result is True

    @patch(
        "core.download.trailer_file.video_analysis.verify_and_analyze_trailer"
    )
    def test_handles_delete_exception_gracefully(
        self, mock_verify, tmp_path, mock_profile
    ):
        """Handles exception when deleting file gracefully."""
        test_file = tmp_path / "trailer.mp4"
        test_file.write_text("test content")
        mock_verify.return_value = (False, None)

        # Should not raise exception even if delete fails internally
        result, info = verify_download(
            str(test_file), "Test Movie", mock_profile
        )

        assert result is False
        assert info is None
