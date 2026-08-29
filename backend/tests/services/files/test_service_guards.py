"""Tests for the path and file-type guards in services/files/service.py.

These decide whether the API opens a path that came from the caller. Before
Phase 7 Stage B they lived in api/v1/files.py and had no tests of their own
— every test that touched them patched them to True to get past them.
"""

import pytest

from services.files import service as files_service


class TestIsPathSafe:

    @pytest.mark.parametrize(
        "path",
        [
            "/etc/passwd",
            "/etc/shadow",
            "/bin/sh",
            "/usr/lib/python3/os.py",
            "/var/log/syslog",
            "/boot/grub/grub.cfg",
            "/sbin/init",
            "/lib/x86_64-linux-gnu/libc.so.6",
            "/app/backend/main.py",
        ],
    )
    def test_system_paths_are_refused(self, path):
        assert files_service.is_path_safe(path) is False

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/media",
            "/media/movies",
        ],
    )
    def test_shallow_paths_are_refused(self, path):
        """A real media file is always at least three levels deep."""
        assert files_service.is_path_safe(path) is False

    @pytest.mark.parametrize(
        "path",
        [
            "/media/movies/Film (2025)/film.mkv",
            "/mnt/data/media/Show/S01E01.mkv",
            "/data/media/movies/Film/trailer.mp4",
        ],
    )
    def test_real_media_paths_are_allowed(self, path):
        assert files_service.is_path_safe(path) is True

    def test_traversal_back_into_a_system_folder_is_refused(self):
        """The path is normalized first, so .. cannot walk into /etc."""
        assert (
            files_service.is_path_safe("/media/movies/../../etc/passwd")
            is False
        )

    def test_a_relative_path_is_judged_by_where_it_resolves_to(self, tmp_path, monkeypatch):
        """A relative path is resolved against the working directory first.

        The same string is therefore safe or unsafe depending on where the
        process runs. In Docker the working directory is /app, which is on
        the refused list. This test records that behavior rather than
        asserting a fixed answer, because the guard has always worked this
        way and Phase 7 only moved it.
        """
        monkeypatch.chdir(tmp_path)
        deep = tmp_path / "a" / "b"
        deep.mkdir(parents=True)
        monkeypatch.chdir(deep)
        assert files_service.is_path_safe("clip.mkv") is True

        # Resolved under an unsafe root, the same shape is refused
        assert files_service.is_path_safe("/app/clip.mkv") is False


class TestFileTypeGuards:

    @pytest.mark.parametrize(
        "path", ["a/b/c/x.mkv", "a/b/c/x.mp4", "a/b/c/x.avi", "a/b/c/x.webm"]
    )
    def test_video_types_are_accepted(self, path):
        assert files_service.is_video_file(path) is True

    @pytest.mark.parametrize(
        "path", ["a/b/c/x.txt", "a/b/c/x.exe", "a/b/c/x", "a/b/c/x.mkv.part"]
    )
    def test_other_types_are_not_videos(self, path):
        assert files_service.is_video_file(path) is False

    @pytest.mark.parametrize(
        "path",
        [
            "a/b/c/x.txt",
            "a/b/c/x.srt",
            "a/b/c/x.log",
            "a/b/c/x.json",
            "a/b/c/x.py",
            "a/b/c/x.sh",
        ],
    )
    def test_readable_text_types_are_accepted(self, path):
        assert files_service.is_readable_text_file(path) is True

    @pytest.mark.parametrize("path", ["a/b/c/x.mkv", "a/b/c/x.env", "a/b/c/x"])
    def test_other_types_are_not_readable(self, path):
        assert files_service.is_readable_text_file(path) is False


class TestReadVideoChunk:

    @pytest.fixture
    def video(self, tmp_path):
        f = tmp_path / "clip.mp4"
        f.write_bytes(bytes(range(256)) * 10)  # 2560 bytes
        return f

    def test_a_bounded_range_reads_exactly_that_span(self, video):
        data, headers = files_service.read_video_chunk(str(video), "bytes=0-99")
        assert len(data) == 99
        assert headers["Content-Range"] == "bytes 0-98/2560"
        assert headers["Accept-Ranges"] == "bytes"

    def test_an_open_range_reads_a_chunk(self, video):
        """No end means CHUNK_SIZE, capped at the end of the file."""
        data, headers = files_service.read_video_chunk(str(video), "bytes=0-")
        assert len(data) == 2560
        assert headers["Content-Range"] == "bytes 0-2559/2560"

    def test_a_range_past_the_end_stops_at_the_end(self, video):
        data, headers = files_service.read_video_chunk(
            str(video), "bytes=2000-999999"
        )
        assert len(data) == 560
        assert headers["Content-Range"] == "bytes 2000-2559/2560"

    def test_reading_from_an_offset_starts_there(self, video):
        data, _ = files_service.read_video_chunk(str(video), "bytes=256-511")
        assert data == bytes(range(256))[0:255]
