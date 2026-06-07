"""Tests for core/files/media_scanner.py — trailer detection edge cases."""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from core.base.database.models.filefolderinfo import (
    FileFolderInfoCreate,
    FileFolderType,
)
from core.files.media_scanner import MediaScanner

MB = 1024 * 1024
_NOW = datetime.now(timezone.utc)
QUICK_MAX = MediaScanner.TRAILER_QUICK_MAX_SIZE_BYTES  # 200 MB
MAX_DURATION = MediaScanner.TRAILER_MAX_DURATION_SECONDS  # 600 s


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _file(
    name: str,
    size: int = 0,
    path: str = "",
    is_trailer: bool = False,
) -> FileFolderInfoCreate:
    return FileFolderInfoCreate(
        type=FileFolderType.FILE,
        name=name,
        size=size,
        path=path or f"/media/{name}",
        modified=_NOW,
        is_trailer=is_trailer,
        media_id=1,
    )


def _folder(
    name: str,
    children: list[FileFolderInfoCreate] | None = None,
    path: str = "",
) -> FileFolderInfoCreate:
    return FileFolderInfoCreate(
        type=FileFolderType.FOLDER,
        name=name,
        size=0,
        path=path or f"/media/{name}",
        modified=_NOW,
        children=children or [],
        media_id=1,
    )


def _video_info(duration_seconds: int) -> MagicMock:
    info = MagicMock()
    info.duration_seconds = duration_seconds
    return info


@pytest.fixture
def scanner():
    with patch(
        "core.files.media_scanner.trailerprofile.get_trailer_folders",
        return_value=set(),
    ):
        yield MediaScanner()


# ---------------------------------------------------------------------------
# _check_large_name_trailer
# ---------------------------------------------------------------------------


class TestCheckLargeNameTrailer:
    """Boundary tests for ffprobe-based large-file verification."""

    @pytest.mark.asyncio
    async def test_ffprobe_returns_none(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=None,
        ):
            assert await scanner._check_large_name_trailer("/m/movie-trailer.mkv") is False

    @pytest.mark.asyncio
    async def test_ffprobe_duration_zero(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(0),
        ):
            assert await scanner._check_large_name_trailer("/m/movie-trailer.mkv") is False

    @pytest.mark.asyncio
    async def test_ffprobe_negative_duration(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(-1),
        ):
            assert await scanner._check_large_name_trailer("/m/movie-trailer.mkv") is False

    @pytest.mark.asyncio
    async def test_duration_within_limit(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(MAX_DURATION - 1),
        ):
            assert await scanner._check_large_name_trailer("/m/movie-trailer.mkv") is True

    @pytest.mark.asyncio
    async def test_duration_exactly_at_limit(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(MAX_DURATION),
        ):
            assert await scanner._check_large_name_trailer("/m/movie-trailer.mkv") is True

    @pytest.mark.asyncio
    async def test_duration_one_second_over_limit(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(MAX_DURATION + 1),
        ):
            assert await scanner._check_large_name_trailer("/m/movie-trailer.mkv") is False


# ---------------------------------------------------------------------------
# is_trailer_file
# ---------------------------------------------------------------------------


class TestIsTrailerFilePathGuards:
    """Extension and path validity guards."""

    @pytest.mark.asyncio
    async def test_empty_path_returns_false(self, scanner):
        assert await scanner.is_trailer_file("") is False

    @pytest.mark.asyncio
    async def test_subtitle_extension_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/movie-trailer.srt") is False

    @pytest.mark.asyncio
    async def test_nfo_extension_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/movie-trailer.nfo") is False

    @pytest.mark.asyncio
    async def test_no_extension_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/movie-trailer") is False


class TestIsTrailerFileEpisodeGuard:
    """TV episode pattern must block trailer detection regardless of context."""

    @pytest.mark.asyncio
    async def test_uppercase_episode_pattern_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/Show - S01E01 - trailer.mkv") is False

    @pytest.mark.asyncio
    async def test_lowercase_episode_pattern_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/show - s02e03 - episode.mkv") is False

    @pytest.mark.asyncio
    async def test_episode_in_trailer_folder_returns_false(self, scanner):
        # Episode guard fires before folder-placement check.
        assert await scanner.is_trailer_file("/m/Movie/Trailers/show - S01E01.mkv") is False


class TestIsTrailerFileFolderAuthoritative:
    """Files inside a trailer folder are trailers regardless of name or size."""

    @pytest.mark.asyncio
    async def test_any_video_in_trailers_folder_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/Trailers/movie.mkv", 50 * MB) is True

    @pytest.mark.asyncio
    async def test_large_video_in_trailers_folder_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/Trailers/movie.mkv", 300 * MB) is True

    @pytest.mark.asyncio
    async def test_trailer_singular_folder_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/Trailer/movie.mkv", 5 * MB) is True

    @pytest.mark.asyncio
    async def test_lowercase_trailers_folder_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/trailers/movie.mkv", 5 * MB) is True

    @pytest.mark.asyncio
    async def test_mp4_in_trailers_folder_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/Trailers/movie.mp4", 80 * MB) is True

    @pytest.mark.asyncio
    async def test_custom_profile_folder_returns_true(self):
        with patch(
            "core.files.media_scanner.trailerprofile.get_trailer_folders",
            return_value={"extras"},
        ):
            s = MediaScanner()
        assert await s.is_trailer_file("/m/Movie/extras/movie.mkv", 50 * MB) is True

    @pytest.mark.asyncio
    async def test_unknown_folder_without_trailer_in_name_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/Featurettes/movie.mkv", 50 * MB) is False


class TestIsTrailerFileNameQuickPath:
    """'trailer' in filename, size below quick threshold — no ffprobe needed."""

    @pytest.mark.asyncio
    async def test_no_size_given_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv") is True

    @pytest.mark.asyncio
    async def test_size_zero_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", 0) is True

    @pytest.mark.asyncio
    async def test_small_size_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", 50 * MB) is True

    @pytest.mark.asyncio
    async def test_just_below_threshold_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", QUICK_MAX - 1) is True

    @pytest.mark.asyncio
    async def test_trailer_uppercase_in_name_returns_true(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/Movie-TRAILER.mkv", 50 * MB) is True

    @pytest.mark.asyncio
    async def test_no_trailer_word_in_name_returns_false(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie.mkv", 50 * MB) is False

    @pytest.mark.asyncio
    async def test_mkv_extension_accepted(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", 10 * MB) is True

    @pytest.mark.asyncio
    async def test_mp4_extension_accepted(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mp4", 10 * MB) is True

    @pytest.mark.asyncio
    async def test_avi_extension_accepted(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.avi", 10 * MB) is True

    @pytest.mark.asyncio
    async def test_webm_extension_accepted(self, scanner):
        assert await scanner.is_trailer_file("/m/Movie/movie-trailer.webm", 10 * MB) is True


class TestIsTrailerFileLargeWithFfprobe:
    """Files at or above QUICK_MAX threshold require ffprobe confirmation."""

    @pytest.mark.asyncio
    async def test_exactly_at_threshold_short_duration_returns_true(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(120),
        ):
            assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", QUICK_MAX) is True

    @pytest.mark.asyncio
    async def test_at_threshold_duration_at_limit_returns_true(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(MAX_DURATION),
        ):
            assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", QUICK_MAX) is True

    @pytest.mark.asyncio
    async def test_at_threshold_duration_over_limit_returns_false(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(MAX_DURATION + 1),
        ):
            assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", QUICK_MAX) is False

    @pytest.mark.asyncio
    async def test_well_above_threshold_short_duration_returns_true(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(90),
        ):
            assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", 500 * MB) is True

    @pytest.mark.asyncio
    async def test_ffprobe_returns_none_returns_false(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=None,
        ):
            assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", QUICK_MAX) is False

    @pytest.mark.asyncio
    async def test_ffprobe_duration_zero_returns_false(self, scanner):
        with patch(
            "core.files.media_scanner.video_analysis.get_media_info",
            return_value=_video_info(0),
        ):
            assert await scanner.is_trailer_file("/m/Movie/movie-trailer.mkv", QUICK_MAX) is False


# ---------------------------------------------------------------------------
# _has_media_file
# ---------------------------------------------------------------------------


class TestHasMediaFile:
    MEDIA_MIN = MediaScanner.MEDIA_FILE_MIN_SIZE_BYTES  # 100 MB

    def test_empty_folder_returns_false(self, scanner):
        assert scanner._has_media_file(_folder("Movie")) is False

    def test_video_below_100mb_returns_false(self, scanner):
        f = _folder("Movie", children=[_file("movie.mkv", self.MEDIA_MIN - 1)])
        assert scanner._has_media_file(f) is False

    def test_video_exactly_100mb_returns_true(self, scanner):
        f = _folder("Movie", children=[_file("movie.mkv", self.MEDIA_MIN)])
        assert scanner._has_media_file(f) is True

    def test_video_above_100mb_returns_true(self, scanner):
        f = _folder("Movie", children=[_file("movie.mkv", 2000 * MB)])
        assert scanner._has_media_file(f) is True

    def test_non_video_large_file_returns_false(self, scanner):
        f = _folder("Movie", children=[_file("movie.nfo", 500 * MB)])
        assert scanner._has_media_file(f) is False

    def test_nested_large_video_returns_true(self, scanner):
        episode = _file("episode.mkv", 500 * MB)
        season = _folder("Season 1", children=[episode])
        show = _folder("Show", children=[season])
        assert scanner._has_media_file(show) is True

    def test_nested_small_video_only_returns_false(self, scanner):
        episode = _file("episode.mkv", 50 * MB)
        season = _folder("Season 1", children=[episode])
        show = _folder("Show", children=[season])
        assert scanner._has_media_file(show) is False

    def test_mix_small_and_large_returns_true(self, scanner):
        small = _file("sample.mkv", 10 * MB)
        large = _file("movie.mkv", 200 * MB)
        f = _folder("Movie", children=[small, large])
        assert scanner._has_media_file(f) is True


# ---------------------------------------------------------------------------
# get_trailer_paths
# ---------------------------------------------------------------------------


class TestGetTrailerPaths:

    def test_no_trailers_returns_empty_set(self, scanner):
        f = _folder("Movie", children=[_file("movie.mkv", 200 * MB)])
        assert scanner.get_trailer_paths(f) == set()

    def test_single_trailer_returns_its_path(self, scanner):
        t = _file("movie-trailer.mkv", path="/m/Movie/movie-trailer.mkv", is_trailer=True)
        f = _folder("Movie", children=[t])
        assert scanner.get_trailer_paths(f) == {"/m/Movie/movie-trailer.mkv"}

    def test_nested_trailer_in_subfolder_is_found(self, scanner):
        t = _file("trailer.mkv", path="/m/Movie/Trailers/trailer.mkv", is_trailer=True)
        sub = _folder("Trailers", children=[t])
        f = _folder("Movie", children=[sub])
        assert scanner.get_trailer_paths(f) == {"/m/Movie/Trailers/trailer.mkv"}

    def test_mix_returns_only_trailer_paths(self, scanner):
        main = _file("movie.mkv", 200 * MB, path="/m/Movie/movie.mkv")
        t = _file("movie-trailer.mkv", path="/m/Movie/movie-trailer.mkv", is_trailer=True)
        f = _folder("Movie", children=[main, t])
        assert scanner.get_trailer_paths(f) == {"/m/Movie/movie-trailer.mkv"}

    def test_multiple_trailers_all_returned(self, scanner):
        t1 = _file("t1.mkv", path="/m/Movie/Trailers/t1.mkv", is_trailer=True)
        t2 = _file("t2.mkv", path="/m/Movie/Trailers/t2.mkv", is_trailer=True)
        sub = _folder("Trailers", children=[t1, t2])
        f = _folder("Movie", children=[sub])
        assert scanner.get_trailer_paths(f) == {
            "/m/Movie/Trailers/t1.mkv",
            "/m/Movie/Trailers/t2.mkv",
        }

    def test_non_trailer_file_in_trailer_folder_excluded(self, scanner):
        non_trailer = _file("movie.mkv", path="/m/Movie/Trailers/movie.mkv", is_trailer=False)
        sub = _folder("Trailers", children=[non_trailer])
        f = _folder("Movie", children=[sub])
        assert scanner.get_trailer_paths(f) == set()


# ---------------------------------------------------------------------------
# check_media_exists
# ---------------------------------------------------------------------------


class TestCheckMediaExists:

    @pytest.mark.asyncio
    async def test_none_folder_info_no_path_returns_false(self, scanner):
        assert await scanner.check_media_exists(None) is False

    @pytest.mark.asyncio
    async def test_folder_info_with_large_video_returns_true(self, scanner):
        f = _folder("Movie", children=[_file("movie.mkv", 200 * MB)])
        assert await scanner.check_media_exists(f) is True

    @pytest.mark.asyncio
    async def test_folder_info_with_only_small_video_returns_false(self, scanner):
        f = _folder("Movie", children=[_file("movie.mkv", 50 * MB)])
        assert await scanner.check_media_exists(f) is False

    @pytest.mark.asyncio
    async def test_nonexistent_folder_path_returns_false(self, scanner):
        assert await scanner.check_media_exists(None, "/nonexistent/path/xyz") is False

    @pytest.mark.asyncio
    async def test_real_folder_with_large_sparse_video_returns_true(self, scanner, tmp_path):
        movie_dir = tmp_path / "Movie (2025)"
        movie_dir.mkdir()
        movie_file = movie_dir / "Movie (2025).mkv"
        movie_file.touch()
        os.truncate(str(movie_file), 100 * MB)  # sparse file, no ffprobe triggered

        result = await scanner.check_media_exists(None, str(movie_dir))
        assert result is True

    @pytest.mark.asyncio
    async def test_real_folder_with_small_video_only_returns_false(self, scanner, tmp_path):
        movie_dir = tmp_path / "Movie (2025)"
        movie_dir.mkdir()
        (movie_dir / "sample.mkv").write_bytes(b"x" * (1 * MB))

        result = await scanner.check_media_exists(None, str(movie_dir))
        assert result is False


# ---------------------------------------------------------------------------
# get_trailer_folders
# ---------------------------------------------------------------------------


class TestGetTrailerFolders:

    def test_always_includes_trailer_and_trailers(self):
        with patch(
            "core.files.media_scanner.trailerprofile.get_trailer_folders",
            return_value=set(),
        ):
            folders = MediaScanner.get_trailer_folders()
        assert "trailer" in folders
        assert "trailers" in folders

    def test_includes_custom_profile_folders(self):
        with patch(
            "core.files.media_scanner.trailerprofile.get_trailer_folders",
            return_value={"Extras", "Behind the Scenes"},
        ):
            folders = MediaScanner.get_trailer_folders()
        assert "extras" in folders
        assert "behind the scenes" in folders

    def test_all_folders_are_lowercased(self):
        with patch(
            "core.files.media_scanner.trailerprofile.get_trailer_folders",
            return_value={"FEATURETTES"},
        ):
            folders = MediaScanner.get_trailer_folders()
        assert "featurettes" in folders
        assert "FEATURETTES" not in folders

    def test_whitespace_stripped_from_folder_names(self):
        with patch(
            "core.files.media_scanner.trailerprofile.get_trailer_folders",
            return_value={"  extras  "},
        ):
            folders = MediaScanner.get_trailer_folders()
        assert "extras" in folders
