"""Unit tests for core/base/utils/path_utils.py.

Tests every exported function (is_subpath, apply_path_mappings,
reverse_path_mappings, normalize_trailing_slash) across all OS path-style
combinations: Linux, macOS, Windows-backslash, Windows-forward-slash, and
mixed separators.

PlexConnectionManager integration tests live in
tests/core/plex/test_path_mapping.py.
"""

from types import SimpleNamespace

from core.base.utils.path_utils import (
    apply_path_mappings,
    is_subpath,
    normalize_trailing_slash,
    reverse_path_mappings,
)


def _pm(path_from: str, path_to: str) -> SimpleNamespace:
    """Minimal PathMapping-like object for testing."""
    return SimpleNamespace(path_from=path_from, path_to=path_to)


# ---------------------------------------------------------------------------
# is_subpath
# ---------------------------------------------------------------------------

class TestIsSubpath:

    # --- POSIX (Linux / macOS) ---

    def test_posix_exact_match(self):
        assert is_subpath("/movies", "/movies") is True

    def test_posix_child_under_parent(self):
        assert is_subpath("/movies", "/movies/Film (2020)") is True

    def test_posix_deeply_nested_child(self):
        assert is_subpath("/data/media", "/data/media/Movies/Film (2020)/extras") is True

    def test_posix_false_positive_boundary(self):
        # /data/media must NOT match /data/media-backup — classic prefix bug
        assert is_subpath("/data/media", "/data/media-backup/Film") is False

    def test_posix_sibling_directory(self):
        assert is_subpath("/movies", "/series/Show") is False

    def test_posix_parent_longer_than_child(self):
        assert is_subpath("/movies/subdir", "/movies") is False

    def test_posix_trailing_slash_on_parent(self):
        assert is_subpath("/movies/", "/movies/Film") is True

    def test_posix_trailing_slash_on_child(self):
        assert is_subpath("/movies", "/movies/Film/") is True

    def test_posix_both_trailing_slashes(self):
        assert is_subpath("/movies/", "/movies/") is True

    def test_posix_macos_volumes_path(self):
        assert is_subpath("/Volumes/Plex/Movies", "/Volumes/Plex/Movies/Film (2020)") is True

    def test_posix_macos_false_positive_boundary(self):
        assert is_subpath("/Volumes/Plex/Movies", "/Volumes/Plex/Movies-Archive/Film") is False

    # --- Windows (backslash) ---

    def test_windows_exact_match_backslash(self):
        assert is_subpath("C:\\Movies", "C:\\Movies") is True

    def test_windows_child_under_parent_backslash(self):
        assert is_subpath("C:\\Movies", "C:\\Movies\\Film (2020)") is True

    def test_windows_deeply_nested(self):
        assert is_subpath("D:\\Media", "D:\\Media\\Movies\\Film (2020)\\extras") is True

    def test_windows_trailing_backslash_on_parent(self):
        assert is_subpath("C:\\Movies\\", "C:\\Movies\\Film") is True

    def test_windows_trailing_backslash_on_child(self):
        assert is_subpath("C:\\Movies", "C:\\Movies\\Film\\") is True

    def test_windows_false_positive_boundary_backslash(self):
        assert is_subpath("C:\\Movies", "C:\\Movies-Backup\\Film") is False

    def test_windows_different_drive(self):
        assert is_subpath("C:\\Movies", "D:\\Movies\\Film") is False

    # --- Windows (forward slash) ---

    def test_windows_child_under_parent_forward_slash(self):
        assert is_subpath("C:/Movies", "C:/Movies/Film (2020)") is True

    def test_windows_false_positive_boundary_forward_slash(self):
        assert is_subpath("C:/Movies", "C:/Movies-Backup/Film") is False

    # --- Windows mixed separators ---

    def test_windows_mixed_parent_backslash_child_forward(self):
        # path_from stored with backslash, incoming path uses forward slashes
        assert is_subpath("C:\\Movies", "C:/Movies/Film (2020)") is True

    def test_windows_mixed_parent_forward_child_backslash(self):
        assert is_subpath("C:/Movies", "C:\\Movies\\Film (2020)") is True

    def test_windows_mixed_false_positive_boundary(self):
        assert is_subpath("C:\\Movies", "C:/Movies-Backup/Film") is False

    # --- Windows UNC (\\server\share) ---

    def test_unc_exact_match(self):
        assert is_subpath("\\\\NAS\\media", "\\\\NAS\\media") is True

    def test_unc_child_under_share(self):
        assert is_subpath("\\\\NAS\\media", "\\\\NAS\\media\\Film") is True

    def test_unc_deeply_nested(self):
        assert is_subpath("\\\\NAS\\media\\movies", "\\\\NAS\\media\\movies\\Action\\Film") is True

    def test_unc_trailing_backslash_on_parent(self):
        assert is_subpath("\\\\NAS\\media\\", "\\\\NAS\\media\\Film") is True

    def test_unc_false_positive_boundary(self):
        assert is_subpath("\\\\NAS\\media", "\\\\NAS\\media-backup\\Film") is False

    def test_unc_different_server(self):
        assert is_subpath("\\\\NAS1\\media", "\\\\NAS2\\media\\Film") is False

    def test_unc_different_share(self):
        assert is_subpath("\\\\NAS\\media", "\\\\NAS\\backup\\Film") is False

    def test_unc_mixed_with_drive_letter(self):
        # UNC and drive-letter Windows paths don't cross-match
        assert is_subpath("C:\\Movies", "\\\\NAS\\Movies\\Film") is False

    # --- Forward-slash UNC (//server/share) — handled by PurePosixPath ---

    def test_fwd_unc_child_under_share(self):
        assert is_subpath("//NAS/media", "//NAS/media/Film") is True

    def test_fwd_unc_false_positive_boundary(self):
        assert is_subpath("//NAS/media", "//NAS/media-backup/Film") is False

    # --- Cross-OS: must NOT match ---

    def test_posix_parent_windows_child(self):
        assert is_subpath("/movies", "C:\\movies\\Film") is False

    def test_windows_parent_posix_child(self):
        assert is_subpath("C:\\Movies", "/Movies/Film") is False

    def test_posix_parent_windows_unc(self):
        assert is_subpath("/media", "C:\\media\\Film") is False

    def test_posix_parent_unc_child(self):
        assert is_subpath("/media", "\\\\NAS\\media\\Film") is False


# ---------------------------------------------------------------------------
# normalize_trailing_slash
# ---------------------------------------------------------------------------

class TestNormalizeTrailingSlash:

    # --- Empty ---

    def test_empty_string_unchanged(self):
        assert normalize_trailing_slash("") == ""

    # --- POSIX (Linux / macOS) ---

    def test_linux_adds_forward_slash(self):
        assert normalize_trailing_slash("/data/movies") == "/data/movies/"

    def test_linux_already_has_slash(self):
        assert normalize_trailing_slash("/data/movies/") == "/data/movies/"

    def test_macos_adds_forward_slash(self):
        assert normalize_trailing_slash("/Volumes/Media/Movies") == "/Volumes/Media/Movies/"

    def test_macos_already_has_slash(self):
        assert normalize_trailing_slash("/Volumes/Media/Movies/") == "/Volumes/Media/Movies/"

    def test_posix_root(self):
        assert normalize_trailing_slash("/") == "/"

    # --- Windows (backslash style) ---

    def test_windows_backslash_adds_backslash(self):
        assert normalize_trailing_slash("C:\\Movies") == "C:\\Movies\\"

    def test_windows_backslash_already_has_backslash(self):
        assert normalize_trailing_slash("C:\\Movies\\") == "C:\\Movies\\"

    def test_windows_backslash_nested_adds_backslash(self):
        assert normalize_trailing_slash("C:\\Movies\\Films") == "C:\\Movies\\Films\\"

    def test_windows_backslash_nested_already_has_backslash(self):
        assert normalize_trailing_slash("C:\\Movies\\Films\\") == "C:\\Movies\\Films\\"

    def test_windows_drive_root_already_correct(self):
        assert normalize_trailing_slash("C:\\") == "C:\\"

    # --- Windows UNC (\\server\share) ---

    def test_unc_adds_backslash(self):
        assert normalize_trailing_slash("\\\\NAS\\media") == "\\\\NAS\\media\\"

    def test_unc_already_has_backslash(self):
        assert normalize_trailing_slash("\\\\NAS\\media\\") == "\\\\NAS\\media\\"

    def test_unc_nested_adds_backslash(self):
        assert normalize_trailing_slash("\\\\NAS\\media\\movies") == "\\\\NAS\\media\\movies\\"

    # --- Forward-slash UNC (//server/share) — gets forward slash ---

    def test_fwd_unc_adds_forward_slash(self):
        # No backslash in path → gets forward slash (consistent with existing style)
        assert normalize_trailing_slash("//NAS/media") == "//NAS/media/"

    def test_fwd_unc_already_has_slash(self):
        assert normalize_trailing_slash("//NAS/media/") == "//NAS/media/"

    # --- Windows (forward-slash style) ---

    def test_windows_forward_slash_adds_forward_slash(self):
        # No backslash in path → gets forward slash, not backslash
        assert normalize_trailing_slash("C:/Movies") == "C:/Movies/"

    def test_windows_forward_slash_already_has_slash(self):
        assert normalize_trailing_slash("C:/Movies/") == "C:/Movies/"

    def test_windows_forward_slash_nested(self):
        assert normalize_trailing_slash("C:/Movies/Films") == "C:/Movies/Films/"


# ---------------------------------------------------------------------------
# apply_path_mappings
# ---------------------------------------------------------------------------

class TestApplyPathMappings:

    # --- Linux Plex → Linux Trailarr ---

    def test_linux_to_linux_basic(self):
        result = apply_path_mappings("/plex/movies/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/local/movies/Film"

    def test_linux_to_linux_nested(self):
        result = apply_path_mappings("/plex/movies/Action/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/local/movies/Action/Film"

    def test_linux_to_linux_exact_match(self):
        result = apply_path_mappings("/plex/movies", [_pm("/plex/movies", "/local/movies")])
        assert result == "/local/movies"

    def test_linux_to_linux_trailing_slash_in_mapping(self):
        result = apply_path_mappings("/plex/movies/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/local/movies/Film"

    def test_linux_no_false_positive_boundary(self):
        result = apply_path_mappings("/plex/movies-backup/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/plex/movies-backup/Film"

    # --- macOS Plex → Linux Trailarr ---

    def test_macos_to_linux(self):
        result = apply_path_mappings(
            "/Volumes/Plex/Movies/Film (2020)",
            [_pm("/Volumes/Plex/Movies/", "/local/movies/")],
        )
        assert result == "/local/movies/Film (2020)"

    def test_macos_no_false_positive_boundary(self):
        result = apply_path_mappings(
            "/Volumes/Plex/Movies-Archive/Film",
            [_pm("/Volumes/Plex/Movies/", "/local/movies/")],
        )
        assert result == "/Volumes/Plex/Movies-Archive/Film"

    # --- Windows Plex → Linux Trailarr ---

    def test_windows_backslash_to_linux(self):
        result = apply_path_mappings("C:\\Movies\\Film", [_pm("C:\\Movies\\", "/local/movies/")])
        assert result == "/local/movies/Film"

    def test_windows_forward_slash_to_linux(self):
        result = apply_path_mappings("C:/Movies/Film", [_pm("C:/Movies/", "/local/movies/")])
        assert result == "/local/movies/Film"

    def test_windows_mixed_path_from_backslash_path_forward(self):
        """path_from stored with backslash; incoming path uses forward slashes."""
        result = apply_path_mappings("C:/Movies/Film", [_pm("C:\\Movies\\", "/local/movies/")])
        assert result == "/local/movies/Film"

    def test_windows_mixed_path_from_forward_path_backslash(self):
        """path_from stored with forward slash; incoming path uses backslashes."""
        result = apply_path_mappings("C:\\Movies\\Film", [_pm("C:/Movies/", "/local/movies/")])
        assert result == "/local/movies/Film"

    def test_windows_no_false_positive_boundary(self):
        result = apply_path_mappings("C:\\Movies-Backup\\Film", [_pm("C:\\Movies\\", "/local/movies/")])
        # no match → backslashes normalised, path unchanged otherwise
        assert result == "C:/Movies-Backup/Film"

    # --- Windows Plex → Windows Trailarr ---

    def test_windows_to_windows(self):
        result = apply_path_mappings("C:\\Plex\\Film", [_pm("C:\\Plex\\", "D:\\Local\\")])
        assert result == "D:/Local/Film"

    def test_windows_different_drives(self):
        result = apply_path_mappings("E:\\Media\\Film", [_pm("E:\\Media\\", "F:\\Storage\\")])
        assert result == "F:/Storage/Film"

    # --- Linux Plex → Windows Trailarr ---

    def test_linux_to_windows(self):
        result = apply_path_mappings("/plex/movies/Film", [_pm("/plex/movies/", "D:\\Local\\Movies\\")])
        assert result == "D:/Local/Movies/Film"

    # --- Multiple mappings ---

    def test_first_matching_mapping_wins(self):
        mappings = [
            _pm("/plex/movies/", "/first/"),
            _pm("/plex/movies/", "/second/"),
        ]
        result = apply_path_mappings("/plex/movies/Film", mappings)
        assert result == "/first/Film"

    def test_second_mapping_used_when_first_does_not_match(self):
        mappings = [
            _pm("/plex/series/", "/local/series/"),
            _pm("/plex/movies/", "/local/movies/"),
        ]
        result = apply_path_mappings("/plex/movies/Film", mappings)
        assert result == "/local/movies/Film"

    # --- Edge cases ---

    def test_empty_path_returns_empty(self):
        assert apply_path_mappings("", [_pm("/plex/", "/local/")]) == ""

    def test_no_mappings_returns_normalised(self):
        # No mappings → backslashes normalised, path otherwise unchanged
        assert apply_path_mappings("C:\\Movies\\Film", []) == "C:/Movies/Film"

    def test_no_matching_mapping_normalises_backslashes(self):
        result = apply_path_mappings("C:\\Movies\\Film", [_pm("/plex/", "/local/")])
        assert result == "C:/Movies/Film"

    def test_posix_unmatched_path_unchanged(self):
        result = apply_path_mappings("/other/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/other/Film"

    # --- Windows UNC path_from ---

    def test_unc_to_linux(self):
        """Radarr on Windows uses UNC share; Trailarr maps it to a Linux path."""
        result = apply_path_mappings(
            "\\\\NAS\\media\\movies\\Film",
            [_pm("\\\\NAS\\media\\movies\\", "/local/movies/")],
        )
        assert result == "/local/movies/Film"

    def test_unc_to_unc(self):
        """UNC-to-UNC mapping; result normalised to forward slashes."""
        result = apply_path_mappings(
            "\\\\NAS1\\media\\Film",
            [_pm("\\\\NAS1\\media\\", "\\\\NAS2\\backup\\")],
        )
        assert result == "//NAS2/backup/Film"

    def test_unc_no_false_positive_boundary(self):
        result = apply_path_mappings(
            "\\\\NAS\\media-backup\\Film",
            [_pm("\\\\NAS\\media\\", "/local/movies/")],
        )
        # no match → backslashes normalised
        assert result == "//NAS/media-backup/Film"

    def test_linux_to_unc_path_to(self):
        """path_to is a UNC path; incoming path is Linux from Radarr on NAS."""
        result = apply_path_mappings(
            "/media/movies/Film",
            [_pm("/media/movies/", "\\\\NAS\\backup\\movies\\")],
        )
        assert result == "//NAS/backup/movies/Film"

    # --- Forward-slash UNC path_from ---

    def test_fwd_unc_to_linux(self):
        result = apply_path_mappings(
            "//NAS/media/movies/Film",
            [_pm("//NAS/media/movies/", "/local/movies/")],
        )
        assert result == "/local/movies/Film"


# ---------------------------------------------------------------------------
# reverse_path_mappings
# ---------------------------------------------------------------------------

class TestReversePathMappings:

    # --- Basic reversal ---

    def test_linux_to_linux_reverse(self):
        result = reverse_path_mappings("/local/movies/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/plex/movies/Film"

    def test_linux_to_linux_nested_reverse(self):
        result = reverse_path_mappings(
            "/local/movies/Action/Film",
            [_pm("/plex/movies/", "/local/movies/")],
        )
        assert result == "/plex/movies/Action/Film"

    def test_exact_match_reverse(self):
        result = reverse_path_mappings("/local/movies", [_pm("/plex/movies", "/local/movies")])
        assert result == "/plex/movies"

    # --- No match ---

    def test_no_match_returns_path_unchanged(self):
        result = reverse_path_mappings("/other/Film", [_pm("/plex/movies/", "/local/movies/")])
        assert result == "/other/Film"

    def test_no_mappings_returns_unchanged(self):
        result = reverse_path_mappings("/local/movies/Film", [])
        assert result == "/local/movies/Film"

    # --- Edge cases ---

    def test_empty_path_returns_empty(self):
        assert reverse_path_mappings("", [_pm("/plex/", "/local/")]) == ""

    # --- Windows path_from ---

    def test_windows_path_from_reverse(self):
        """Trailarr-internal (Linux) path reversed back to a Windows Plex path."""
        result = reverse_path_mappings(
            "/local/movies/Film",
            [_pm("C:\\Plex\\Movies\\", "/local/movies/")],
        )
        # _remap uses relative_to on POSIX side, result normalised to forward slashes
        assert result == "C:/Plex/Movies/Film"

    def test_first_matching_mapping_wins_reverse(self):
        mappings = [
            _pm("/first/", "/local/movies/"),
            _pm("/second/", "/local/movies/"),
        ]
        result = reverse_path_mappings("/local/movies/Film", mappings)
        assert result == "/first/Film"

    def test_unc_path_from_reverse(self):
        """Trailarr-internal path reversed back to a UNC Plex/Arr path."""
        result = reverse_path_mappings(
            "/local/movies/Film",
            [_pm("\\\\NAS\\media\\movies\\", "/local/movies/")],
        )
        assert result == "//NAS/media/movies/Film"
