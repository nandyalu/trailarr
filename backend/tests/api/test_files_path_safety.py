"""Tests for the path guard on the file endpoints.

`_is_path_safe` decides whether the API will open a path that arrived in a
request. It had no tests: every test that reached it patched it to True to
get out of the way.

It also refused every path on Windows, because it counted '/' characters
and a Windows path has none. A direct install on Windows could list a
folder but could not play, rename or delete a trailer.
"""

from pathlib import PureWindowsPath
from unittest.mock import patch

import pytest

from api.v1.files import _is_path_safe


class TestRealMediaPathsAreAllowed:

    @pytest.mark.parametrize(
        "path",
        [
            "/media/movies/Film (2025)/film.mkv",
            "/mnt/data/media/Show/S01E01.mkv",
            "/data/media/movies/Film/trailer.mp4",
            "/config/logs/trailarr.log",
        ],
    )
    def test_linux_media_paths(self, path):
        assert _is_path_safe(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "/variable/media/movies/film.mkv",
            "/etcetera/media/movies/film.mkv",
            "/usr-data/media/movies/film.mkv",
            "/libraries/media/movies/film.mkv",
        ],
    )
    def test_a_folder_that_merely_starts_with_a_system_name(self, path):
        """/variable is not /var. The check compares whole folder names."""
        assert _is_path_safe(path) is True


class TestSystemPathsAreRefused:

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
    def test_linux_system_paths(self, path):
        assert _is_path_safe(path) is False

    @pytest.mark.parametrize("path", ["/", "/media", "/media/movies"])
    def test_paths_too_shallow_to_be_a_media_file(self, path):
        assert _is_path_safe(path) is False

    def test_traversal_back_into_a_system_folder(self):
        """'..' is resolved before the path is checked."""
        assert _is_path_safe("/media/movies/../../etc/passwd") is False

    def test_deep_traversal_back_into_a_system_folder(self):
        assert (
            _is_path_safe("/media/movies/Film/../../../../etc/shadow") is False
        )

    def test_a_relative_path_is_refused(self):
        """It would be resolved against the working directory, which the
        caller does not choose."""
        assert _is_path_safe("relative/path/file.mkv") is False

    def test_an_empty_path_is_refused(self):
        assert _is_path_safe("") is False


class TestWindows:
    """The bug this fix is for.

    PurePath follows the platform it runs on, so these tests force the
    Windows flavour to check the rules the way a Windows install would.
    """

    @staticmethod
    def _as_windows(path: str) -> bool:
        with patch("api.v1.files.PurePath", PureWindowsPath):
            with patch("api.v1.files.os.path.normpath", lambda p: p):
                return _is_path_safe(path)

    @pytest.mark.parametrize(
        "path",
        [
            r"C:\Media\Movies\Film (2025)\film.mkv",
            r"D:\Library\Shows\Show\S01E01.mkv",
            r"C:\Users\kr\Videos\Film\film.mkv",
        ],
    )
    def test_a_real_windows_media_path_is_allowed(self, path):
        assert self._as_windows(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            r"C:\Windows\System32\config\SAM",
            r"C:\Program Files\Trailarr\app.exe",
            r"C:\ProgramData\secret\file.txt",
            r"D:\Windows\System32\drivers\etc\hosts",
        ],
    )
    def test_windows_system_paths_are_refused(self, path):
        assert self._as_windows(path) is False

    @pytest.mark.parametrize("path", [r"C:\\", r"C:\Media", r"C:\Media\film.mkv"])
    def test_windows_paths_too_shallow_are_refused(self, path):
        assert self._as_windows(path) is False
