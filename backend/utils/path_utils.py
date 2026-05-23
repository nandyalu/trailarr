"""Shared path-handling utilities used by all connection managers.

Single source of truth for:
- Cross-platform subpath checking (is_subpath)
- Path-mapping application with mixed-separator support (apply_path_mappings)
- Reverse path-mapping (reverse_path_mappings)
- Trailing-slash normalisation for DB storage (normalize_trailing_slash)
"""

import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Sequence

# Matches a Windows path prefix: either a drive letter (C:\ or C:/) or a UNC
# share prefix (\\server).  Forward-slash UNC (//server) is intentionally
# excluded — PurePosixPath already handles it correctly on all platforms.
# Used to choose between PureWindowsPath and PurePosixPath for cross-platform
# comparisons regardless of the host OS.
_WINDOWS_ABS_RE = re.compile(r"^(?:[A-Za-z]:[/\\]|\\\\)")


def is_subpath(parent: str, child: str) -> bool:
    """Return True iff *child* is equal to or under *parent*, respecting directory boundaries.

    Works on Linux, macOS, and Windows hosts for any combination of path
    styles.  Uses PureWindowsPath when either path looks like a Windows
    absolute path (``C:\\...`` or ``C:/...``) so that backslash separators
    are recognised correctly on POSIX hosts.

    Unlike a raw ``startswith`` check, this never gives false positives for
    sibling directories (e.g. ``/data/media`` does NOT match
    ``/data/media-backup``).
    """
    parent_n = parent.rstrip("/\\")
    child_n = child.rstrip("/\\")
    if _WINDOWS_ABS_RE.match(parent_n) or _WINDOWS_ABS_RE.match(child_n):
        try:
            PureWindowsPath(child_n).relative_to(PureWindowsPath(parent_n))
            return True
        except ValueError:
            return False
    try:
        PurePosixPath(child_n).relative_to(PurePosixPath(parent_n))
        return True
    except ValueError:
        return False


def _remap(path: str, path_from: str, path_to: str) -> str:
    """Replace the *path_from* prefix in *path* with *path_to*.

    Uses ``pathlib.relative_to`` instead of string replace so that mixed
    separators (e.g. ``path_from`` stored with ``\\`` but *path* arriving
    with ``/``) are handled correctly.  Always returns forward slashes.
    """
    _from = path_from.rstrip("/\\")
    _to = path_to.rstrip("/\\")
    child_n = path.rstrip("/\\")
    if _WINDOWS_ABS_RE.match(_from) or _WINDOWS_ABS_RE.match(child_n):
        rel = str(PureWindowsPath(child_n).relative_to(PureWindowsPath(_from)))
    else:
        rel = str(PurePosixPath(child_n).relative_to(PurePosixPath(_from)))
    rel = rel.replace("\\", "/")
    result = _to + ("/" + rel if rel != "." else "")
    return result.replace("\\", "/")


def apply_path_mappings(path: str, mappings: Sequence[Any]) -> str:
    """Find the first matching mapping and remap *path* through it.

    Each item in *mappings* must expose ``.path_from`` and ``.path_to``
    string attributes.  Always returns forward slashes, even when no mapping
    matches (backslashes in an unmatched path are normalised on return).
    """
    if not path:
        return path
    for pm in mappings:
        if is_subpath(pm.path_from, path):
            return _remap(path, pm.path_from, pm.path_to)
    return path.replace("\\", "/")


def reverse_path_mappings(path: str, mappings: Sequence[Any]) -> str:
    """Inverse of apply_path_mappings: remap from the *path_to* side back to *path_from*.

    Used when converting a Trailarr-internal path back to the remote
    (Plex/Arr) side, e.g. to send a targeted scan request to Plex.
    Returns *path* unchanged (no backslash normalisation) when no mapping
    matches, preserving whatever the caller passed in.
    """
    if not path:
        return path
    for pm in mappings:
        if is_subpath(pm.path_to, path):
            return _remap(path, pm.path_to, pm.path_from)
    return path


def normalize_trailing_slash(path: str) -> str:
    """Ensure *path* ends with the correct separator for its type.

    - Windows absolute paths that already use backslashes (``C:\\...``) get a
      trailing backslash appended.
    - All other paths (Linux, macOS, or Windows paths that use forward
      slashes) get a trailing forward slash.

    A trailing separator that is already present is preserved as-is (no
    doubling).  An empty string is returned unchanged.
    """
    if not path:
        return path
    if path.endswith("/") or path.endswith("\\"):
        return path
    if "\\" in path and _WINDOWS_ABS_RE.match(path):
        return path + "\\"
    return path + "/"
