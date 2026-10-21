import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from services.trailers.video_analysis import (
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

    @patch("services.trailers.video_analysis.get_media_info")
    def test_valid_trailer(self, mock_get_media_info, mock_video_info_valid):
        """Returns True for valid trailer with audio, video, and valid duration."""
        mock_get_media_info.return_value = mock_video_info_valid

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is True
        mock_get_media_info.assert_called_once_with("/path/to/trailer.mp4")

    @patch("services.trailers.video_analysis.get_media_info")
    def test_empty_trailer_path(self, mock_get_media_info):
        """Returns None for empty trailer path."""
        result = verify_trailer_streams("")

        assert result is None
        mock_get_media_info.assert_not_called()

    @patch("services.trailers.video_analysis.get_media_info")
    def test_none_trailer_path(self, mock_get_media_info):
        """Returns None for None trailer path."""
        result = verify_trailer_streams(None)  # type: ignore

        assert result is None
        mock_get_media_info.assert_not_called()

    @patch("services.trailers.video_analysis.get_media_info")
    def test_media_info_not_found(self, mock_get_media_info):
        """Returns None when media info cannot be retrieved."""
        mock_get_media_info.return_value = None

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is None
        mock_get_media_info.assert_called_once_with("/path/to/trailer.mp4")

    @patch("services.trailers.video_analysis.get_media_info")
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

    @patch("services.trailers.video_analysis.get_media_info")
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

    @patch("services.trailers.video_analysis.get_media_info")
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

    @patch("services.trailers.video_analysis.get_media_info")
    def test_no_streams(self, mock_get_media_info, mock_video_info_no_streams):
        """Returns False when trailer has no streams."""
        mock_get_media_info.return_value = mock_video_info_no_streams

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is False

    @patch("services.trailers.video_analysis.get_media_info")
    def test_missing_audio_stream(
        self, mock_get_media_info, mock_video_info_no_audio
    ):
        """Returns False when trailer lacks audio stream."""
        mock_get_media_info.return_value = mock_video_info_no_audio

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is False

    @patch("services.trailers.video_analysis.get_media_info")
    def test_missing_video_stream(
        self, mock_get_media_info, mock_video_info_no_video
    ):
        """Returns False when trailer lacks video stream."""
        mock_get_media_info.return_value = mock_video_info_no_video

        result = verify_trailer_streams("/path/to/trailer.mp4")

        assert result is False

    @patch("services.trailers.video_analysis.get_media_info")
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

    @patch("services.trailers.video_analysis.get_media_info")
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

    @patch("services.trailers.video_analysis.get_media_info")
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


class TestSubprocessGuards:
    """ffprobe and ffmpeg run with a timeout and honour a job stop."""

    def test_get_media_info_runs_ffprobe_with_a_timeout(self):
        import subprocess

        from services.trailers.video_analysis import (
            FFPROBE_TIMEOUT,
            get_media_info,
        )

        with patch(
            "services.trailers.video_analysis.quiv.run_subprocess"
        ) as run:
            run.return_value.returncode = 1
            run.return_value.stderr = "no such file"
            assert get_media_info("/path/to/missing.mp4") is None

        assert run.call_args.kwargs["timeout"] == FFPROBE_TIMEOUT
        assert run.call_args.kwargs["stdout"] == subprocess.PIPE

    def test_get_media_info_timeout_returns_none_and_logs(self):
        import subprocess

        from services.trailers.video_analysis import get_media_info

        with (
            patch(
                "services.trailers.video_analysis.quiv.run_subprocess",
                side_effect=subprocess.TimeoutExpired("ffprobe", 60),
            ),
            patch("services.trailers.video_analysis.logger") as logger,
        ):
            assert get_media_info("/path/to/slow.mp4") is None

        logger.error.assert_called_once_with(
            "Trailarr stopped ffprobe for 'slow.mp4' after 60 seconds."
        )

    def test_get_media_info_lets_a_job_cancel_propagate(self):
        import quiv

        from services.trailers.video_analysis import get_media_info

        with patch(
            "services.trailers.video_analysis.quiv.run_subprocess",
            side_effect=quiv.JobCancelledError("ffprobe was stopped"),
        ):
            with pytest.raises(quiv.JobCancelledError):
                get_media_info("/path/to/trailer.mp4")

    def test_silence_detection_timeout_returns_no_silence(self):
        import subprocess

        from services.trailers.video_analysis import (
            FFMPEG_TIMEOUT,
            get_silence_timestamps,
        )

        with (
            patch(
                "services.trailers.video_analysis.quiv.run_subprocess",
                side_effect=subprocess.TimeoutExpired("ffmpeg", 600),
            ) as run,
            patch("services.trailers.video_analysis.logger") as logger,
        ):
            assert get_silence_timestamps("/path/to/slow.mp4") == (
                None,
                None,
            )

        assert run.call_args.kwargs["timeout"] == FFMPEG_TIMEOUT
        logger.error.assert_called_once_with(
            "Trailarr stopped the silence detection for 'slow.mp4' after"
            " 600 seconds."
        )

    def test_silence_detection_lets_a_job_cancel_propagate(self):
        import quiv

        from services.trailers.video_analysis import get_silence_timestamps

        with patch(
            "services.trailers.video_analysis.quiv.run_subprocess",
            side_effect=quiv.JobCancelledError("ffmpeg was stopped"),
        ):
            with pytest.raises(quiv.JobCancelledError):
                get_silence_timestamps("/path/to/trailer.mp4")

    def test_trim_video_lets_a_job_cancel_propagate_and_removes_output(
        self, tmp_path
    ):
        import quiv

        from services.trailers.video_analysis import trim_video

        output = tmp_path / "trimmed.mp4"
        output.write_bytes(b"partial")

        with patch(
            "services.trailers.video_analysis.quiv.run_subprocess",
            side_effect=quiv.JobCancelledError("ffmpeg was stopped"),
        ):
            # Not the generic Exception that trim_video wraps errors in.
            with pytest.raises(quiv.JobCancelledError):
                trim_video("/path/to/in.mp4", str(output), 0, 10)

        assert not output.exists()

    def test_trim_video_timeout_raises_and_removes_output(self, tmp_path):
        import subprocess

        from services.trailers.video_analysis import trim_video

        output = tmp_path / "trimmed.mp4"
        output.write_bytes(b"partial")

        with patch(
            "services.trailers.video_analysis.quiv.run_subprocess",
            side_effect=subprocess.TimeoutExpired("ffmpeg", 600),
        ):
            with pytest.raises(Exception, match="stopped ffmpeg for 'in.mp4'"):
                trim_video("/path/to/in.mp4", str(output), 0, 10)

        assert not output.exists()

    def test_remove_silence_lets_a_job_cancel_propagate(self):
        import quiv

        from services.trailers.video_analysis import remove_silence_at_end

        with (
            patch(
                "services.trailers.video_analysis.get_silence_timestamps",
                return_value=(100.0, 110.0),
            ),
            patch(
                "services.trailers.video_analysis.trim_video",
                side_effect=quiv.JobCancelledError("ffmpeg was stopped"),
            ),
        ):
            with pytest.raises(quiv.JobCancelledError):
                remove_silence_at_end("/path/to/trailer.mp4")
