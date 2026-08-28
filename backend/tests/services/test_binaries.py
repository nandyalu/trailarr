"""Tests for startup binary path validation (yt-dlp/ffmpeg/ffprobe)."""

import os
from unittest.mock import patch

from services.binaries import (
    _ensure_js_runtime,
    _resolve_binary,
    validate_binary_paths,
)


class TestResolveBinary:
    def test_configured_path_valid_keeps_env_unchanged(self, monkeypatch):
        monkeypatch.delenv("YTDLP_PATH", raising=False)
        with patch("services.binaries.shutil.which", return_value="/usr/bin/yt-dlp"):
            _resolve_binary("yt-dlp", "YTDLP_PATH", "/usr/bin/yt-dlp")
        assert "YTDLP_PATH" not in os.environ

    def test_missing_path_falls_back_to_system_path(self, monkeypatch):
        monkeypatch.delenv("YTDLP_PATH", raising=False)

        def fake_which(cmd):
            # Configured path does not exist; bare name resolves on PATH
            return "/usr/bin/yt-dlp" if cmd == "yt-dlp" else None

        with patch("services.binaries.shutil.which", side_effect=fake_which):
            _resolve_binary("yt-dlp", "YTDLP_PATH", "/usr/local/bin/yt-dlp")
        assert os.environ["YTDLP_PATH"] == "/usr/bin/yt-dlp"

    def test_missing_everywhere_logs_error_and_keeps_env(self, monkeypatch):
        monkeypatch.delenv("YTDLP_PATH", raising=False)
        with (
            patch("services.binaries.shutil.which", return_value=None),
            patch("services.binaries.logger.error") as mock_error,
        ):
            _resolve_binary("yt-dlp", "YTDLP_PATH", "/usr/local/bin/yt-dlp")
        assert "YTDLP_PATH" not in os.environ
        assert mock_error.called
        message = mock_error.call_args[0][0]
        assert "YTDLP_PATH" in message
        assert "/usr/local/bin/yt-dlp" in message


class TestValidateBinaryPaths:
    def test_checks_all_three_tools_and_js_runtime(self):
        with (
            patch("services.binaries._resolve_binary") as mock_resolve,
            patch("services.binaries._ensure_js_runtime") as mock_js,
        ):
            validate_binary_paths()
        tools = [call.args[0] for call in mock_resolve.call_args_list]
        assert tools == ["yt-dlp", "ffmpeg", "ffprobe"]
        assert mock_js.called


class TestEnsureJsRuntime:
    def test_deno_on_path_is_noop(self, monkeypatch):
        monkeypatch.setenv("PATH", "/usr/bin")
        with patch(
            "services.binaries.shutil.which", return_value="/usr/bin/deno"
        ):
            _ensure_js_runtime()
        assert os.environ["PATH"] == "/usr/bin"

    def test_deno_path_setting_is_added_to_path(self, monkeypatch):
        monkeypatch.setenv("PATH", "/usr/bin")
        monkeypatch.setenv("DENO_PATH", "/opt/trailarr/bin/deno")

        def fake_which(cmd):
            # Not on PATH by name; the configured absolute path resolves
            if cmd == "/opt/trailarr/bin/deno":
                return "/opt/trailarr/bin/deno"
            return None

        with patch("services.binaries.shutil.which", side_effect=fake_which):
            _ensure_js_runtime()
        assert os.environ["PATH"].startswith(
            "/opt/trailarr/bin" + os.pathsep
        )

    def test_no_runtime_anywhere_logs_warning(self, monkeypatch):
        monkeypatch.setenv("PATH", "/usr/bin")
        monkeypatch.delenv("DENO_PATH", raising=False)
        with (
            patch("services.binaries.shutil.which", return_value=None),
            patch("services.binaries.logger.warning") as mock_warn,
        ):
            _ensure_js_runtime()
        assert mock_warn.called
        assert "DENO_PATH" in mock_warn.call_args[0][0]
        assert os.environ["PATH"] == "/usr/bin"
