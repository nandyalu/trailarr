"""Integration tests for PlexConnectionManager path-mapping methods.

Covers all OS combinations (Linux/macOS/Windows) for path_from, path_to,
and media folder paths, since Plex and Trailarr can run on different hosts
with different path styles.

Unit tests for the underlying path utilities (is_subpath, apply_path_mappings,
reverse_path_mappings, normalize_trailing_slash) live in
tests/core/base/utils/test_path_utils.py.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.plex.connection_manager import PlexConnectionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pm(path_from: str, path_to: str, pm_id: int = 1, section_key: str | None = None):
    """Create a minimal PathMapping-like object."""
    return SimpleNamespace(
        id=pm_id,
        path_from=path_from,
        path_to=path_to,
        plex_section_key=section_key,
    )


def _section(folders: list[str], key: str = "1", title: str = "Movies"):
    """Create a minimal PlexLibrarySection-like object."""
    return SimpleNamespace(key=key, title=title, folders=folders)


def _manager(path_mappings: list, all_path_mappings: list | None = None):
    """Create a PlexConnectionManager-like namespace for method testing."""
    return SimpleNamespace(
        path_mappings=path_mappings,
        all_path_mappings=all_path_mappings if all_path_mappings is not None else path_mappings,
    )


# ---------------------------------------------------------------------------
# _apply_path_mapping
# ---------------------------------------------------------------------------

class TestApplyPathMapping:
    """Tests for PlexConnectionManager._apply_path_mapping.

    path_from = Plex-side path, path_to = Trailarr-side path.
    The method converts a Plex path into the local Trailarr path.
    """

    # --- Linux Plex → Linux Trailarr ---

    def test_linux_to_linux(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies/Film (2020)")
        assert result == "/local/movies/Film (2020)"

    def test_linux_to_linux_nested(self):
        mgr = _manager([_pm("/mnt/plex", "/data")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies/Film/extras")
        assert result == "/data/movies/Film/extras"

    def test_linux_to_linux_exact_root(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies")
        assert result == "/local/movies"

    def test_linux_to_linux_trailing_slash_in_path_from(self):
        mgr = _manager([_pm("/mnt/plex/movies/", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies/Film")
        assert result == "/local/movies/Film"

    def test_linux_to_linux_no_false_positive(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies-backup/Film")
        # Path doesn't match the mapping — returned as-is
        assert result == "/mnt/plex/movies-backup/Film"

    # --- macOS Plex → Linux Trailarr (common Docker scenario) ---

    def test_macos_to_linux(self):
        mgr = _manager([_pm("/Volumes/Plex/Movies", "/data/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/Volumes/Plex/Movies/Film (2020)")
        assert result == "/data/movies/Film (2020)"

    def test_macos_to_linux_no_false_positive(self):
        mgr = _manager([_pm("/Volumes/Plex/Movies", "/data/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/Volumes/Plex/Movies-Archive/Film")
        assert result == "/Volumes/Plex/Movies-Archive/Film"

    # --- Windows Plex → Linux Trailarr (most common cross-OS scenario) ---

    def test_windows_backslash_to_linux(self):
        mgr = _manager([_pm("C:\\Plex\\Movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "C:\\Plex\\Movies\\Film (2020)")
        assert result == "/local/movies/Film (2020)"

    def test_windows_forward_slash_to_linux(self):
        mgr = _manager([_pm("C:/Plex/Movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "C:/Plex/Movies/Film (2020)")
        assert result == "/local/movies/Film (2020)"

    def test_windows_mixed_slash_to_linux(self):
        mgr = _manager([_pm("C:\\Plex\\Movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "C:/Plex/Movies/Film (2020)")
        assert result == "/local/movies/Film (2020)"

    def test_windows_to_linux_no_false_positive(self):
        mgr = _manager([_pm("C:\\Movies", "/local/movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "C:\\Movies-Backup\\Film")
        # no mapping matches → path returned unchanged except backslashes are normalised
        assert result == "C:/Movies-Backup/Film"

    # --- Windows Plex → Windows Trailarr ---

    def test_windows_to_windows(self):
        mgr = _manager([_pm("C:\\Plex\\Movies", "D:\\Local\\Movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "C:\\Plex\\Movies\\Film (2020)")
        # Backslashes in path_to get normalised to forward slashes
        assert result == "D:/Local/Movies/Film (2020)"

    def test_windows_to_windows_different_drive(self):
        mgr = _manager([_pm("E:\\Media\\Movies", "F:\\Storage\\Movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "E:\\Media\\Movies\\Film")
        assert result == "F:/Storage/Movies/Film"

    # --- Linux Plex → Windows Trailarr ---

    def test_linux_to_windows(self):
        mgr = _manager([_pm("/mnt/plex/movies", "D:\\Local\\Movies")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies/Film (2020)")
        assert result == "D:/Local/Movies/Film (2020)"

    # --- Edge cases ---

    def test_empty_path(self):
        mgr = _manager([_pm("/movies", "/local")])
        assert PlexConnectionManager._apply_path_mapping(mgr, "") == ""

    def test_no_mappings(self):
        mgr = _manager([])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/movies/Film")
        assert result == "/movies/Film"

    def test_no_matching_mapping(self):
        mgr = _manager([_pm("/mnt/plex", "/local")])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/data/other/Film")
        assert result == "/data/other/Film"

    def test_first_matching_mapping_wins(self):
        mgr = _manager([
            _pm("/mnt/plex/movies", "/local/movies", pm_id=1),
            _pm("/mnt/plex", "/local", pm_id=2),
        ])
        result = PlexConnectionManager._apply_path_mapping(mgr, "/mnt/plex/movies/Film")
        # First mapping should match and win
        assert result == "/local/movies/Film"

    def test_backslashes_normalised_even_without_mapping(self):
        mgr = _manager([])
        result = PlexConnectionManager._apply_path_mapping(mgr, "some\\path\\with\\backslashes")
        assert result == "some/path/with/backslashes"

    def test_identity_mapping_excluded_no_double_substitution(self):
        # Identity mappings (path_from == path_to) must not be in path_mappings
        # (the constructor filters them), so test that the manager has no substitution.
        mgr = _manager(path_mappings=[])  # identity excluded
        result = PlexConnectionManager._apply_path_mapping(mgr, "/movies/Film")
        assert result == "/movies/Film"


# ---------------------------------------------------------------------------
# _reverse_path_mapping
# ---------------------------------------------------------------------------

class TestReversePathMapping:
    """Tests for PlexConnectionManager._reverse_path_mapping.

    This is the inverse of _apply_path_mapping: converts a Trailarr path
    back to the Plex-side path (used when triggering targeted Plex scans).
    """

    # --- Linux Trailarr → Linux Plex ---

    def test_linux_to_linux_reverse(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/local/movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/local/movies/Film (2020)")
        assert result == "/mnt/plex/movies/Film (2020)"

    def test_linux_to_linux_reverse_exact_root(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/local/movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/local/movies")
        assert result == "/mnt/plex/movies"

    def test_linux_to_linux_reverse_no_false_positive(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/local/movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/local/movies-extra/Film")
        assert result == "/local/movies-extra/Film"

    # --- Linux Trailarr → Windows Plex ---

    def test_linux_to_windows_reverse(self):
        mgr = _manager([_pm("C:\\Plex\\Movies", "/local/movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/local/movies/Film (2020)")
        assert result == "C:/Plex/Movies/Film (2020)"

    # --- Windows Trailarr → Windows Plex ---

    def test_windows_to_windows_reverse(self):
        mgr = _manager([_pm("C:\\Plex\\Movies", "D:\\Local\\Movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "D:\\Local\\Movies\\Film")
        assert result == "C:/Plex/Movies/Film"

    def test_windows_forward_slash_to_windows_reverse(self):
        mgr = _manager([_pm("C:/Plex/Movies", "D:/Local/Movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "D:/Local/Movies/Film")
        assert result == "C:/Plex/Movies/Film"

    # --- macOS Trailarr → Linux Plex ---

    def test_linux_plex_to_macos_trailarr_reverse(self):
        mgr = _manager([_pm("/mnt/plex/movies", "/Volumes/Local/Movies")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/Volumes/Local/Movies/Film")
        assert result == "/mnt/plex/movies/Film"

    # --- Edge cases ---

    def test_empty_path(self):
        mgr = _manager([_pm("/mnt/plex", "/local")])
        assert PlexConnectionManager._reverse_path_mapping(mgr, "") == ""

    def test_no_mappings(self):
        mgr = _manager([])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/local/movies/Film")
        assert result == "/local/movies/Film"

    def test_no_matching_mapping(self):
        mgr = _manager([_pm("/mnt/plex", "/local")])
        result = PlexConnectionManager._reverse_path_mapping(mgr, "/other/path/Film")
        assert result == "/other/path/Film"


# ---------------------------------------------------------------------------
# _is_in_configured_library
# ---------------------------------------------------------------------------

class TestIsInConfiguredLibrary:
    """Tests for PlexConnectionManager._is_in_configured_library.

    Uses all_path_mappings (includes identity) to decide if a Plex item
    folder falls under any configured library.
    """

    def test_linux_match(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/mnt/plex/movies/Film") is True

    def test_linux_no_match(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/mnt/other/Film") is False

    def test_linux_boundary_false_positive(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/mnt/plex/movies-backup/Film") is False

    def test_windows_match_backslash(self):
        mgr = _manager([], all_path_mappings=[_pm("C:\\Plex\\Movies", "/local/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "C:\\Plex\\Movies\\Film") is True

    def test_windows_match_forward_slash(self):
        mgr = _manager([], all_path_mappings=[_pm("C:/Plex/Movies", "/local/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "C:/Plex/Movies/Film") is True

    def test_windows_boundary_false_positive(self):
        mgr = _manager([], all_path_mappings=[_pm("C:\\Movies", "/local")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "C:\\Movies-Backup\\Film") is False

    def test_windows_wrong_drive(self):
        mgr = _manager([], all_path_mappings=[_pm("C:\\Movies", "/local")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "D:\\Movies\\Film") is False

    def test_macos_match(self):
        mgr = _manager([], all_path_mappings=[_pm("/Volumes/Plex/Movies", "/data/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/Volumes/Plex/Movies/Film") is True

    def test_macos_boundary_false_positive(self):
        mgr = _manager([], all_path_mappings=[_pm("/Volumes/Plex/Movies", "/data/movies")])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/Volumes/Plex/Movies-old/Film") is False

    def test_multiple_mappings_one_matches(self):
        mgr = _manager([], all_path_mappings=[
            _pm("/mnt/plex/movies", "/local/movies", pm_id=1),
            _pm("/mnt/plex/shows", "/local/shows", pm_id=2),
        ])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/mnt/plex/shows/Show/S01") is True

    def test_no_mappings(self):
        mgr = _manager([], all_path_mappings=[])
        assert PlexConnectionManager._is_in_configured_library(mgr, "/mnt/plex/movies/Film") is False


# ---------------------------------------------------------------------------
# _section_is_tracked
# ---------------------------------------------------------------------------

class TestSectionIsTracked:
    """Tests for PlexConnectionManager._section_is_tracked.

    Returns True if any of the section's root folders falls under any
    configured path mapping.
    """

    def test_single_folder_matches(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local")])
        section = _section(["/mnt/plex/movies"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is True

    def test_single_folder_no_match(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local")])
        section = _section(["/mnt/other/section"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is False

    def test_multiple_folders_one_matches(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local")])
        section = _section(["/mnt/other/section", "/mnt/plex/movies"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is True

    def test_multiple_folders_none_match(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local")])
        section = _section(["/mnt/other/a", "/mnt/other/b"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is False

    def test_boundary_false_positive_not_tracked(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex/movies", "/local")])
        section = _section(["/mnt/plex/movies-archive"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is False

    def test_windows_folder_matches(self):
        mgr = _manager([], all_path_mappings=[_pm("C:\\Plex\\Movies", "/local")])
        section = _section(["C:\\Plex\\Movies"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is True

    def test_windows_folder_boundary_false_positive(self):
        mgr = _manager([], all_path_mappings=[_pm("C:\\Movies", "/local")])
        section = _section(["C:\\Movies-Backup"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is False

    def test_windows_multiple_folders_one_matches(self):
        mgr = _manager([], all_path_mappings=[_pm("C:\\Plex\\Movies", "/local")])
        section = _section(["D:\\Other\\Movies", "C:\\Plex\\Movies"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is True

    def test_macos_folder_matches(self):
        mgr = _manager([], all_path_mappings=[_pm("/Volumes/Plex/Movies", "/data")])
        section = _section(["/Volumes/Plex/Movies"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is True

    def test_empty_folders_list(self):
        mgr = _manager([], all_path_mappings=[_pm("/mnt/plex", "/local")])
        section = _section([])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is False

    def test_multiple_mappings_second_matches(self):
        mgr = _manager([], all_path_mappings=[
            _pm("/mnt/plex/movies", "/local/movies", pm_id=1),
            _pm("/mnt/plex/shows", "/local/shows", pm_id=2),
        ])
        section = _section(["/mnt/plex/shows"])
        assert PlexConnectionManager._section_is_tracked(mgr, section) is True


# ---------------------------------------------------------------------------
# _persist_section_keys
# ---------------------------------------------------------------------------

class TestPersistSectionKeys:
    """Tests for PlexConnectionManager._persist_section_keys.

    Writes the section key to the DB only when plex_section_key is None.
    """

    def test_writes_section_key_when_none(self):
        pm = _pm("/mnt/plex/movies", "/local", section_key=None)
        mgr = _manager([], all_path_mappings=[pm])
        section = _section(["/mnt/plex/movies/Film"], key="5")

        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            PlexConnectionManager._persist_section_keys(mgr, section)
            mock_update.assert_called_once_with(pm.id, "5")
            assert pm.plex_section_key == "5"

    def test_skips_when_section_key_already_set(self):
        pm = _pm("/mnt/plex/movies", "/local", section_key="3")
        mgr = _manager([], all_path_mappings=[pm])
        section = _section(["/mnt/plex/movies/Film"], key="5")

        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            PlexConnectionManager._persist_section_keys(mgr, section)
            mock_update.assert_not_called()

    def test_skips_unmatched_mapping(self):
        pm = _pm("/mnt/plex/shows", "/local/shows", section_key=None)
        mgr = _manager([], all_path_mappings=[pm])
        section = _section(["/mnt/plex/movies/Film"], key="5")

        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            PlexConnectionManager._persist_section_keys(mgr, section)
            mock_update.assert_not_called()
            assert pm.plex_section_key is None

    def test_windows_path_writes_section_key(self):
        pm = _pm("C:\\Plex\\Movies", "/local", section_key=None)
        mgr = _manager([], all_path_mappings=[pm])
        section = _section(["C:\\Plex\\Movies\\Film"], key="7")

        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            PlexConnectionManager._persist_section_keys(mgr, section)
            mock_update.assert_called_once_with(pm.id, "7")

    def test_boundary_path_does_not_write_section_key(self):
        pm = _pm("/mnt/plex/movies", "/local", section_key=None)
        mgr = _manager([], all_path_mappings=[pm])
        # folder is /mnt/plex/movies-archive — should NOT match
        section = _section(["/mnt/plex/movies-archive/Film"], key="9")

        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            PlexConnectionManager._persist_section_keys(mgr, section)
            mock_update.assert_not_called()

    def test_only_first_matching_folder_triggers_db_write(self):
        pm = _pm("/mnt/plex/movies", "/local", section_key=None)
        mgr = _manager([], all_path_mappings=[pm])
        # Section has two matching folders — DB should only be written once
        section = _section([
            "/mnt/plex/movies/group-a",
            "/mnt/plex/movies/group-b",
        ], key="2")

        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            PlexConnectionManager._persist_section_keys(mgr, section)
            mock_update.assert_called_once_with(pm.id, "2")
