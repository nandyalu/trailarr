import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from core.download.video_analysis import (
    verify_trailer_streams,
    VideoInfo,
    StreamInfo,
)


@pytest.fixture
def mock_video_info_valid():
    """Valid trailer with audio and video streams within duration limits."""
    return VideoInfo(
        name="test_trailer.mp4",
        file_path="/path/to/test_trailer.mp4",
        format_name="mp4",
        duration_seconds=60,
        duration="0:01:00",
        size=5000000,
        bitrate="1.5 Mbps",
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
        youtube_channel="test_channel",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_video_info_no_audio():
    """Trailer with only video stream."""
    return VideoInfo(
        name="test_trailer.mp4",
        file_path="/path/to/test_trailer.mp4",
        format_name="mp4",
        duration_seconds=60,
        duration="0:01:00",
        size=5000000,
        bitrate="1.5 Mbps",
        streams=[
            StreamInfo(
                index=0,
                codec_type="video",
                codec_name="h264",
                coded_height=1080,
                coded_width=1920,
            ),
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_video_info_no_video():
    """Trailer with only audio stream."""
    return VideoInfo(
        name="test_trailer.mp4",
        file_path="/path/to/test_trailer.mp4",
        format_name="mp4",
        duration_seconds=60,
        duration="0:01:00",
        size=5000000,
        bitrate="1.5 Mbps",
        streams=[
            StreamInfo(
                index=0,
                codec_type="audio",
                codec_name="aac",
                audio_channels=2,
                sample_rate=48000,
            ),
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_video_info_no_streams():
    """Trailer with no streams."""
    return VideoInfo(
        name="test_trailer.mp4",
        file_path="/path/to/test_trailer.mp4",
        format_name="mp4",
        duration_seconds=60,
        duration="0:01:00",
        size=5000000,
        bitrate="1.5 Mbps",
        streams=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestVerifyTrailerStreams:
    """Tests for verify_trailer_streams function."""

    @patch("core.download.video_analysis.get_media_info")
    def test_valid_trailer(self, mock_get_media_info, mock_video_info_valid):
        """Returns True for valid trailer with audio, video, and valid duration."""
        mock_get_media_info.return_value = mock_video_info_valid

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is True
        mock_get_media_info.assert_called_once_with("/path/to/trailer.mp4")

    @patch("core.download.video_analysis.get_media_info")
    def test_empty_trailer_path(self, mock_get_media_info):
        """Returns None for empty trailer path."""
        result = verify_trailer_streams("")

        assert result is None
        mock_get_media_info.assert_not_called()

    @patch("core.download.video_analysis.get_media_info")
    def test_none_trailer_path(self, mock_get_media_info):
        """Returns None for None trailer path."""
        result = verify_trailer_streams(None)  # type: ignore

        assert result is None
        mock_get_media_info.assert_not_called()

    @patch("core.download.video_analysis.get_media_info")
    def test_media_info_not_found(self, mock_get_media_info):
        """Returns None when media info cannot be retrieved."""
        mock_get_media_info.return_value = None

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is None
        mock_get_media_info.assert_called_once_with("/path/to/trailer.mp4")

    @patch("core.download.video_analysis.get_media_info")
    def test_zero_duration(self, mock_get_media_info):
        """Returns None when trailer duration is zero."""
        video_info = VideoInfo(
            name="test_trailer.mp4",
            file_path="/path/to/test_trailer.mp4",
            format_name="mp4",
            duration_seconds=0,
            duration="0:00:00",
            size=5000000,
            bitrate="1.5 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                ),
                StreamInfo(
                    index=1,
                    codec_type="audio",
                    codec_name="aac",
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_get_media_info.return_value = video_info

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is None

    @patch("core.download.video_analysis.get_media_info")
    def test_duration_below_minimum(self, mock_get_media_info):
        """Returns False when trailer duration is below minimum."""
        video_info = VideoInfo(
            name="test_trailer.mp4",
            file_path="/path/to/test_trailer.mp4",
            format_name="mp4",
            duration_seconds=5,
            duration="0:00:05",
            size=5000000,
            bitrate="1.5 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                ),
                StreamInfo(
                    index=1,
                    codec_type="audio",
                    codec_name="aac",
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_get_media_info.return_value = video_info

        result = verify_trailer_streams(
            "/path/to/trailer.mp4", min_duration=10
        )

        assert result is False

    @patch("core.download.video_analysis.get_media_info")
    def test_duration_above_maximum(self, mock_get_media_info):
        """Returns False when trailer duration exceeds maximum."""
        video_info = VideoInfo(
            name="test_trailer.mp4",
            file_path="/path/to/test_trailer.mp4",
            format_name="mp4",
            duration_seconds=1500,
            duration="0:25:00",
            size=5000000,
            bitrate="1.5 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                ),
                StreamInfo(
                    index=1,
                    codec_type="audio",
                    codec_name="aac",
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_get_media_info.return_value = video_info

        result = verify_trailer_streams(
            "/path/to/trailer.mp4", max_duration=1200
        )

        assert result is False

    @patch("core.download.video_analysis.get_media_info")
    def test_no_streams(self, mock_get_media_info, mock_video_info_no_streams):
        """Returns False when trailer has no streams."""
        mock_get_media_info.return_value = mock_video_info_no_streams

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is False

    @patch("core.download.video_analysis.get_media_info")
    def test_missing_audio_stream(
        self, mock_get_media_info, mock_video_info_no_audio
    ):
        """Returns False when trailer lacks audio stream."""
        mock_get_media_info.return_value = mock_video_info_no_audio

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is False

    @patch("core.download.video_analysis.get_media_info")
    def test_missing_video_stream(
        self, mock_get_media_info, mock_video_info_no_video
    ):
        """Returns False when trailer lacks video stream."""
        mock_get_media_info.return_value = mock_video_info_no_video

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is False

    @patch("core.download.video_analysis.get_media_info")
    def test_custom_duration_limits(self, mock_get_media_info):
        """Respects custom min and max duration parameters."""
        video_info = VideoInfo(
            name="test_trailer.mp4",
            file_path="/path/to/test_trailer.mp4",
            format_name="mp4",
            duration_seconds=150,
            duration="0:02:30",
            size=5000000,
            bitrate="1.5 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                ),
                StreamInfo(
                    index=1,
                    codec_type="audio",
                    codec_name="aac",
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_get_media_info.return_value = video_info

        result = verify_trailer_streams(
            "/path/to/trailer.mp4", min_duration=30, max_duration=200
        )

        assert result is True

    @patch("core.download.video_analysis.get_media_info")
    def test_edge_case_duration_at_minimum(self, mock_get_media_info):
        """Returns True when duration equals minimum threshold."""
        video_info = VideoInfo(
            name="test_trailer.mp4",
            file_path="/path/to/test_trailer.mp4",
            format_name="mp4",
            duration_seconds=10,
            duration="0:00:10",
            size=5000000,
            bitrate="1.5 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                ),
                StreamInfo(
                    index=1,
                    codec_type="audio",
                    codec_name="aac",
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_get_media_info.return_value = video_info

        result = verify_trailer_streams(
            "/path/to/trailer.mp4", min_duration=10
        )

        assert result is True

    @patch("core.download.video_analysis.get_media_info")
    def test_edge_case_duration_at_maximum(self, mock_get_media_info):
        """Returns True when duration equals maximum threshold."""
        video_info = VideoInfo(
            name="test_trailer.mp4",
            file_path="/path/to/test_trailer.mp4",
            format_name="mp4",
            duration_seconds=1200,
            duration="0:20:00",
            size=5000000,
            bitrate="1.5 Mbps",
            streams=[
                StreamInfo(
                    index=0,
                    codec_type="video",
                    codec_name="h264",
                ),
                StreamInfo(
                    index=1,
                    codec_type="audio",
                    codec_name="aac",
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_get_media_info.return_value = video_info

        result = verify_trailer_streams(
            "/path/to/trailer.mp4", max_duration=1200
        )

        assert result is True
