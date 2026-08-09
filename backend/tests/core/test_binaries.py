"""Tests for startup binary path validation (yt-dlp/ffmpeg/ffprobe)."""

import os
from unittest.mock import patch

from core.binaries import _resolve_binary, validate_binary_paths


class TestResolveBinary:
    def test_configured_path_valid_keeps_env_unchanged(self, monkeypatch):
        monkeypatch.delenv("YTDLP_PATH", raising=False)
        with patch("core.binaries.shutil.which", return_value="/usr/bin/yt-dlp"):
            _resolve_binary("yt-dlp", "YTDLP_PATH", "/usr/bin/yt-dlp")
        assert "YTDLP_PATH" not in os.environ

    def test_missing_path_falls_back_to_system_path(self, monkeypatch):
        monkeypatch.delenv("YTDLP_PATH", raising=False)

        def fake_which(cmd):
            # Configured path does not exist; bare name resolves on PATH
            return "/usr/bin/yt-dlp" if cmd == "yt-dlp" else None

        with patch("core.binaries.shutil.which", side_effect=fake_which):
            _resolve_binary("yt-dlp", "YTDLP_PATH", "/usr/local/bin/yt-dlp")
        assert os.environ["YTDLP_PATH"] == "/usr/bin/yt-dlp"

    def test_missing_everywhere_logs_error_and_keeps_env(self, monkeypatch):
        monkeypatch.delenv("YTDLP_PATH", raising=False)
        with (
            patch("core.binaries.shutil.which", return_value=None),
            patch("core.binaries.logger.error") as mock_error,
        ):
            _resolve_binary("yt-dlp", "YTDLP_PATH", "/usr/local/bin/yt-dlp")
        assert "YTDLP_PATH" not in os.environ
        assert mock_error.called
        message = mock_error.call_args[0][0]
        assert "YTDLP_PATH" in message
        assert "/usr/local/bin/yt-dlp" in message


class TestValidateBinaryPaths:
    def test_checks_all_three_tools(self):
        with patch("core.binaries._resolve_binary") as mock_resolve:
            validate_binary_paths()
        tools = [call.args[0] for call in mock_resolve.call_args_list]
        assert tools == ["yt-dlp", "ffmpeg", "ffprobe"]
