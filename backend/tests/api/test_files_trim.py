"""Tests for the trim_video endpoint in api/v1/files.py."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from api.v1.files import trim_video

SAFE_INPUT = "/media/movies/Inception (2010)/Inception-trailer.mkv"
SAFE_OUTPUT = "/media/movies/Inception (2010)/Inception-trailer-trimmed.mkv"


class TestTrimVideoPathSafety:

    def test_unsafe_output_path_is_refused_before_ffmpeg_runs(self):
        with patch("api.v1.files.video_analysis.trim_video") as trim:
            with pytest.raises(HTTPException) as exc:
                trim_video(SAFE_INPUT, "/etc/passwd", 0, 10)
        assert exc.value.status_code == 400
        trim.assert_not_called()

    def test_unsafe_input_path_is_refused_before_ffmpeg_runs(self):
        with patch("api.v1.files.video_analysis.trim_video") as trim:
            with pytest.raises(HTTPException) as exc:
                trim_video("/etc/passwd", SAFE_OUTPUT, 0, 10)
        assert exc.value.status_code == 400
        trim.assert_not_called()

    def test_safe_paths_reach_ffmpeg(self):
        with patch(
            "api.v1.files.video_analysis.trim_video", return_value=True
        ) as trim:
            result = trim_video(SAFE_INPUT, SAFE_OUTPUT, 0, 10)
        assert result == "Video trimmed successfully."
        trim.assert_called_once_with(SAFE_INPUT, SAFE_OUTPUT, 0, 10)
