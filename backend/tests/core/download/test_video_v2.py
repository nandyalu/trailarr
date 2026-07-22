"""Tests for yt-dlp download options and partial-file cleanup (#626)."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from core.base.database.models.customfilter import CustomFilterRead, FilterType
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.video_v2 import (
    _cleanup_partial_downloads,
    _download_with_ytdlp,
    _get_ytdl_options,
    cleanup_stale_temp_downloads,
)
from exceptions import DownloadFailedError


@pytest.fixture
def trailer_profile():
    cf = CustomFilterRead(
        id=1,
        filter_name="Test CF",
        filter_type=FilterType.TRAILER,
        filters=[],
    )
    return TrailerProfileRead(
        id=1,
        customfilter=cf,
        customfilter_id=cf.id,
        video_format="h264",
        audio_format="aac",
        subtitles_format="srt",
        file_format="mkv",
        video_resolution=1080,
        audio_volume_level=100,
        subtitles_enabled=True,
        subtitles_language="en",
        embed_metadata=True,
        ytdlp_extra_options="",
    )


class TestLiveContentExcludedFromDownload:
    def test_match_filter_excludes_live_content(self, trailer_profile):
        options = _get_ytdl_options(trailer_profile)
        idx = options.index("--match-filter")
        assert options[idx + 1] == "!is_live & !is_upcoming"


class TestCleanupPartialDownloads:
    def test_removes_partial_and_intermediate_files(self, tmp_path):
        (tmp_path / "temp_311-trailer.mkv.part").write_bytes(b"x" * 10)
        (tmp_path / "temp_311-trailer.f616.mp4.part").write_bytes(b"x")
        (tmp_path / "temp_311-trailer.mkv").write_bytes(b"x")
        # A different media item's file must be untouched
        other = tmp_path / "temp_312-trailer.mkv.part"
        other.write_bytes(b"x")

        _cleanup_partial_downloads(tmp_path / "temp_311-trailer.mkv")

        assert not (tmp_path / "temp_311-trailer.mkv.part").exists()
        assert not (tmp_path / "temp_311-trailer.f616.mp4.part").exists()
        assert not (tmp_path / "temp_311-trailer.mkv").exists()
        assert other.exists()

    def test_prefix_does_not_match_longer_media_id(self, tmp_path):
        # Cleaning media 31 must not remove media 311's files
        keep = tmp_path / "temp_311-trailer.mkv.part"
        keep.write_bytes(b"x")

        _cleanup_partial_downloads(tmp_path / "temp_31-trailer.mkv")

        assert keep.exists()

    def test_handles_ext_template_output_path(self, tmp_path):
        part = tmp_path / "temp_311-trailer.webm.part"
        part.write_bytes(b"x")

        _cleanup_partial_downloads(tmp_path / "temp_311-trailer.%(ext)s")

        assert not part.exists()

    def test_missing_directory_is_noop(self, tmp_path):
        _cleanup_partial_downloads(tmp_path / "nope" / "temp_1-trailer.mkv")


class TestDownloadFailureCleanup:
    def test_timeout_removes_partial_file(self, tmp_path, trailer_profile):
        out_file = tmp_path / "temp_311-trailer.mkv"
        part = tmp_path / "temp_311-trailer.mkv.part"
        part.write_bytes(b"x" * 100)

        with patch(
            "core.download.video_v2.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="yt-dlp", timeout=900),
        ):
            with pytest.raises(DownloadFailedError, match="timed out"):
                _download_with_ytdlp(
                    "https://youtu.be/abc", str(out_file), trailer_profile
                )

        assert not part.exists()

    def test_filtered_live_video_raises_clear_error(
        self, tmp_path, trailer_profile
    ):
        # yt-dlp exits 0 when --match-filter skips the video; no file exists
        result = MagicMock()
        result.returncode = 0
        result.stdout = (
            "[youtube] abc: does not pass filter (!is_live & !is_upcoming),"
            " skipping .."
        )
        result.stderr = ""
        out_file = tmp_path / "temp_311-trailer.mkv"

        with patch(
            "core.download.video_v2.subprocess.run", return_value=result
        ):
            with pytest.raises(
                DownloadFailedError, match="livestream/premiere"
            ):
                _download_with_ytdlp(
                    "https://youtu.be/abc", str(out_file), trailer_profile
                )

    def test_failed_exit_code_removes_partial_file(
        self, tmp_path, trailer_profile
    ):
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "some error"
        out_file = tmp_path / "temp_311-trailer.mkv"
        part = tmp_path / "temp_311-trailer.mkv.part"
        part.write_bytes(b"x")

        with patch(
            "core.download.video_v2.subprocess.run", return_value=result
        ):
            with pytest.raises(DownloadFailedError, match="exit code 1"):
                _download_with_ytdlp(
                    "https://youtu.be/abc", str(out_file), trailer_profile
                )

        assert not part.exists()


class TestCleanupStaleTempDownloads:
    def test_removes_stale_files_and_keeps_directories(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(
            "core.download.video_v2.tempfile.gettempdir",
            lambda: str(tmp_path),
        )
        trailarr_dir = tmp_path / "trailarr"
        trailarr_dir.mkdir()
        stale = trailarr_dir / "temp_311-trailer.mkv.part"
        stale.write_bytes(b"x" * 1024)
        subdir = trailarr_dir / "somedir"
        subdir.mkdir()

        cleanup_stale_temp_downloads()

        assert not stale.exists()
        assert subdir.exists()

    def test_missing_temp_dir_is_noop(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "core.download.video_v2.tempfile.gettempdir",
            lambda: str(tmp_path / "nope"),
        )
        cleanup_stale_temp_downloads()
