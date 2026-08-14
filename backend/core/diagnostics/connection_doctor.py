"""Connection Doctor — Milestone A of the Onboarding & Diagnostics track.

Checks that Trailarr can actually see and write to the media folders a
connection reports, and proposes the concrete fix when it cannot:

1. Reachability — can the Arr/Plex API be queried for its folders?
2. Path visibility — does each reported root folder exist and list from
   inside Trailarr (after path mappings)? Silently-empty network mounts
   are flagged, not passed (see `is_disk_available`).
3. Mapping suggester — for an invisible root, diff the reported path
   against the folders visible to Trailarr and suggest a PathMapping.
4. Permissions — create and delete a `.trailarr-write-test` file in one
   accessible folder; on failure report the uid/gid mismatch and the
   PUID/PGID fix.

Probes are read-only except the write-test file. Media files are never
touched. Reports are kept in memory only — a check re-runs in well under
a second, so nothing needs to survive a restart.

NOTE (phase-07 move map): this package moves to `services/diagnostics/`
in the backend reorganization.
"""

import os
import re
from types import SimpleNamespace

from app_logger import ModuleLogger
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.connection import ConnectionRead
from core.base.utils.path_utils import (
    apply_path_mappings,
    is_subpath,
    reverse_path_mappings,
)
from core.diagnostics.models import (
    DoctorReport,
    ProbeResult,
    ProbeStatus,
    SuggestedMapping,
)
from core.files_handler import is_disk_available

logger = ModuleLogger("ConnectionDoctor")

DOCS_BASE = "https://nandyalu.github.io/trailarr/"
DOCS_PATH_MAPPINGS = (
    DOCS_BASE + "getting-started/01-first-things/radarr-sonarr-volumes/"
)
DOCS_PUID_PGID = (
    DOCS_BASE + "getting-started/01-first-things/environment-variables/"
)
DOCS_NETWORK_DRIVES = (
    DOCS_BASE + "getting-started/01-first-things/network-drives/"
)

# Windows drive letter (C:\ or C:/) or UNC share (\\server) prefix
_WINDOWS_ABS_RE = re.compile(r"^(?:[A-Za-z]:[/\\]|\\\\)")

# Top-level directories that can never hold a media library. Everything
# else under / is a candidate base for the mapping suggester.
_SYSTEM_DIRS = frozenset({
    "bin", "boot", "dev", "etc", "init", "lib", "lib32", "lib64",
    "libx32", "lost+found", "proc", "root", "run", "sbin", "snap",
    "sys", "tmp", "usr", "var",
})

_MAX_MEDIA_SAMPLES = 5
_MAX_BASES = 200

# Last report per connection id — in-memory only.
_reports: dict[int, DoctorReport] = {}


def get_report(connection_id: int) -> DoctorReport | None:
    """Return the last report for a connection, or None if never run."""
    return _reports.get(connection_id)


def get_all_reports() -> list[DoctorReport]:
    """Return the last report of every checked connection."""
    return list(_reports.values())


def forget_report(connection_id: int) -> None:
    """Drop the stored report of a deleted connection."""
    _reports.pop(connection_id, None)


async def run_doctor(connection_id: int) -> DoctorReport:
    """Run all probes for a connection and store the report."""
    connection = connection_manager.read(connection_id)
    report = DoctorReport(
        connection_id=connection_id, connection_name=connection.name
    )

    # 1. Reachability: ask the application for its folders
    roots, reach_probe = await _fetch_roots(connection)
    report.probes.append(reach_probe)

    # 2. Path visibility per reported root (+ mapping suggestions).
    # The filesystem walk for suggester bases runs once per report.
    samples = _arr_side_media_samples(connection)
    bases = _visible_bases(connection)
    checked_dirs: list[str] = []
    for root in roots:
        probe, mapped_dir = _probe_root(root, connection, samples, bases)
        report.probes.append(probe)
        if mapped_dir:
            checked_dirs.append(mapped_dir)

    # 2b. No roots reported and none stored — nothing to check
    if not roots and reach_probe.status == ProbeStatus.OK:
        report.probes.append(
            ProbeResult(
                kind="path_visibility",
                name="Folders",
                status=ProbeStatus.SKIPPED,
                detail=(
                    "The connection reports no root folders yet."
                    " Add media in the application, then run the check"
                    " again."
                ),
            )
        )

    # 3. Permissions in the first visible folder
    report.probes.append(_probe_permissions(checked_dirs))

    report.finalize()
    _reports[connection_id] = report
    logger.info(
        f"Doctor for '{connection.name}' [{connection_id}]:"
        f" {report.status}"
        f" ({sum(1 for p in report.probes if p.status == ProbeStatus.ERROR)}"
        f" error(s))"
    )
    return report


# ---------------------------------------------------------------------------
# Probe implementations
# ---------------------------------------------------------------------------


async def _fetch_roots(
    connection: ConnectionRead,
) -> tuple[list[str], ProbeResult]:
    """Fetch the reported root/library folders from the application."""
    try:
        roots = await connection_manager.get_rootfolders(connection)
    except Exception as e:
        return [], ProbeResult(
            kind="reachability",
            name="API reachability",
            status=ProbeStatus.ERROR,
            detail=(
                f"Could not get the folder list from {connection.name}:"
                f" {e}"
            ),
            remediation=(
                "Check that the URL and API key are correct and that"
                " Trailarr can reach the server."
            ),
        )
    return roots, ProbeResult(
        kind="reachability",
        name="API reachability",
        status=ProbeStatus.OK,
        detail=(
            f"{connection.name} answered and reports"
            f" {len(roots)} folder(s)."
        ),
    )


def _probe_root(
    root: str,
    connection: ConnectionRead,
    samples: list[str],
    bases: list[str],
) -> tuple[ProbeResult, str | None]:
    """Check one reported root folder. Returns (probe, mapped_dir).

    mapped_dir is the Trailarr-side directory when it is accessible,
    for use by the permission probe.
    """
    name = f"Folder: {root}"
    mapped = apply_path_mappings(root, connection.path_mappings)

    # A5: Windows-style path on a POSIX host can never exist directly
    if _WINDOWS_ABS_RE.match(mapped) and os.name != "nt":
        suggestion = _suggest_mapping(root, samples, bases)
        return ProbeResult(
            kind="path_style",
            name=name,
            status=ProbeStatus.ERROR,
            detail=(
                f"{connection.name} reports a Windows path, but Trailarr"
                " runs on a non-Windows system. The application likely"
                " runs on a remote Windows machine."
            ),
            remediation=(
                "Add a path mapping from the Windows path to the folder"
                f" where Trailarr sees the same files (for example"
                f" '{root}' → '/media/movies')."
            ),
            docs_url=DOCS_PATH_MAPPINGS,
            suggested_mapping=suggestion,
        ), None

    if os.path.isdir(mapped):
        try:
            entry_count = sum(1 for _ in os.scandir(mapped))
        except OSError as e:
            return ProbeResult(
                kind="path_visibility",
                name=name,
                status=ProbeStatus.ERROR,
                detail=f"'{mapped}' exists but cannot be listed: {e}",
                remediation=(
                    "Check the mount and the folder permissions for the"
                    " user Trailarr runs as."
                ),
                docs_url=DOCS_PUID_PGID,
            ), None
        # A2: an empty folder that passes isdir can be a dead soft-mount
        if entry_count == 0:
            available = is_disk_available(os.path.join(mapped, "probe"))
            return ProbeResult(
                kind="path_visibility",
                name=name,
                status=ProbeStatus.WARNING,
                detail=(
                    f"'{mapped}' is reachable but empty."
                    " If this library is not empty, the mount behind it"
                    " may be down."
                    + (
                        ""
                        if available
                        else " The storage behind it looks unavailable."
                    )
                ),
                remediation=(
                    "Check the network share or drive that provides"
                    " this folder, then run the check again."
                ),
                docs_url=DOCS_NETWORK_DRIVES,
            ), mapped
        detail = f"'{root}' is visible ({entry_count} entries)."
        if mapped != root:
            detail = (
                f"'{root}' maps to '{mapped}' and is visible"
                f" ({entry_count} entries)."
            )
        return ProbeResult(
            kind="path_visibility",
            name=name,
            status=ProbeStatus.OK,
            detail=detail,
        ), mapped

    # Not visible: suggest a mapping from what IS visible
    suggestion = _suggest_mapping(root, samples, bases)
    remediation = (
        "Map this path to the folder where Trailarr sees the same"
        " files, on the connection's Path Mappings."
    )
    if suggestion:
        confidence = (
            f" {suggestion.corroborations} probed path(s) confirm it."
            if suggestion.corroborations > 1
            else " The match is based on the folder name only — check"
            " the contents before you apply it."
        )
        remediation = (
            f"Suggested mapping: '{suggestion.path_from}' →"
            f" '{suggestion.path_to}'.{confidence}"
        )
    return ProbeResult(
        kind="path_visibility",
        name=name,
        status=ProbeStatus.ERROR,
        detail=(
            f"{connection.name} reports '{root}', but that path is not"
            " visible to Trailarr"
            + (f" (checked as '{mapped}')" if mapped != root else "")
            + "."
        ),
        remediation=remediation,
        docs_url=DOCS_PATH_MAPPINGS,
        suggested_mapping=suggestion,
    ), None


def _probe_permissions(checked_dirs: list[str]) -> ProbeResult:
    """Create and delete a test file in the first accessible folder."""
    if not checked_dirs:
        return ProbeResult(
            kind="permissions",
            name="Write permissions",
            status=ProbeStatus.SKIPPED,
            detail=(
                "No accessible folder to test. Fix the folder"
                " visibility first."
            ),
        )
    folder = checked_dirs[0]
    test_file = os.path.join(folder, ".trailarr-write-test")
    try:
        with open(test_file, "w"):
            pass
        os.remove(test_file)
    except PermissionError:
        return ProbeResult(
            kind="permissions",
            name="Write permissions",
            status=ProbeStatus.ERROR,
            detail=_permission_detail(folder),
            remediation=(
                "Set PUID/PGID (or the folder's owner/permissions) so"
                " the Trailarr user can write to your media folders."
            ),
            docs_url=DOCS_PUID_PGID,
        )
    except OSError as e:
        return ProbeResult(
            kind="permissions",
            name="Write permissions",
            status=ProbeStatus.ERROR,
            detail=f"Cannot write to '{folder}': {e}",
            remediation=(
                "Check that the storage is not read-only and that the"
                " Trailarr user can write to it."
            ),
            docs_url=DOCS_PUID_PGID,
        )
    return ProbeResult(
        kind="permissions",
        name="Write permissions",
        status=ProbeStatus.OK,
        detail=f"Trailarr can create and delete files in '{folder}'.",
    )


def _permission_detail(folder: str) -> str:
    """Name the exact uid/gid mismatch (issue #17, solved at the source)."""
    detail = f"Permission denied when writing to '{folder}'."
    try:
        st = os.stat(folder)
        detail += (
            f" The folder is owned by uid={st.st_uid} gid={st.st_gid}"
            f" with mode {oct(st.st_mode & 0o777)}."
        )
        if hasattr(os, "getuid"):
            detail += (
                f" Trailarr runs as uid={os.getuid()} gid={os.getgid()}."
            )
    except OSError:
        pass
    return detail


# ---------------------------------------------------------------------------
# Mapping suggester
# ---------------------------------------------------------------------------


def _arr_side_media_samples(connection: ConnectionRead) -> list[str]:
    """Up to N stored media folders, translated back to the remote side.

    Used to corroborate a suggested mapping: a mapping that also makes
    known media folders resolve is almost certainly correct.
    """
    try:
        media = media_manager.read_all_by_connection(connection.id)
    except Exception:
        return []
    paths = [m.folder_path for m in media if m.folder_path]
    if len(paths) > _MAX_MEDIA_SAMPLES:
        # Spread the samples instead of taking the first N neighbors
        step = len(paths) // _MAX_MEDIA_SAMPLES
        paths = paths[::step][:_MAX_MEDIA_SAMPLES]
    return [
        reverse_path_mappings(p, connection.path_mappings) for p in paths
    ]


def _visible_bases(connection: ConnectionRead) -> list[str]:
    """Folders visible to Trailarr that could hold a media library.

    Walks the filesystem root plus one level below each candidate
    (Docker mounts commonly live at /media/<name> or /mnt/<share>), and
    always includes the targets of existing path mappings.
    """
    bases: list[str] = []
    try:
        for entry in sorted(os.scandir("/"), key=lambda e: e.name):
            if entry.name in _SYSTEM_DIRS or entry.name.startswith("."):
                continue
            try:
                if entry.is_dir(follow_symlinks=True):
                    bases.append("/" + entry.name)
            except OSError:
                continue
    except OSError:
        pass
    for base in list(bases):
        try:
            children = sorted(os.scandir(base), key=lambda e: e.name)
        except OSError:
            continue
        for entry in children:
            if entry.name.startswith("."):
                continue
            try:
                if entry.is_dir(follow_symlinks=True):
                    bases.append(os.path.join(base, entry.name))
            except OSError:
                continue
            if len(bases) >= _MAX_BASES:
                break
    for pm in connection.path_mappings:
        target = pm.path_to.rstrip("/\\")
        if target and target not in bases:
            bases.append(target)
    return bases[:_MAX_BASES]


def _suggest_mapping(
    root: str,
    samples: list[str],
    bases: list[str],
) -> SuggestedMapping | None:
    """Find the visible folder that likely holds the files behind *root*.

    Splits the remote path at every component and looks for a visible
    base where the remaining tail exists. Every candidate is verified
    against the media samples under the same prefix; the candidate that
    the most samples confirm wins. A shallower prefix wins a tie, since
    it covers sibling folders too.
    """
    parts = [p for p in re.split(r"[/\\]+", root) if p]
    if not parts:
        return None
    is_windows = bool(_WINDOWS_ABS_RE.match(root))
    best: SuggestedMapping | None = None

    for i in range(1, len(parts) + 1):
        prefix_parts, tail = parts[:i], parts[i:]
        if is_windows:
            prefix = "\\".join(prefix_parts) + "\\"
        else:
            prefix = "/" + "/".join(prefix_parts) + "/"
        for base in bases:
            if not tail:
                # Mapping the whole root onto a base needs name evidence:
                # the base folder must carry the root's own name
                # (e.g. '/movies' → '/media/movies').
                if os.path.basename(base).lower() != parts[-1].lower():
                    continue
                target = base
            else:
                target = os.path.join(base, *tail)
            if not os.path.isdir(target):
                continue
            candidate_mapping = SimpleNamespace(
                path_from=prefix, path_to=base + "/"
            )
            corroborations = 1
            for sample in samples:
                if sample.rstrip("/\\") == root.rstrip("/\\"):
                    continue
                if not is_subpath(prefix, sample):
                    continue
                remapped = apply_path_mappings(sample, [candidate_mapping])
                if os.path.isdir(remapped):
                    corroborations += 1
            candidate = SuggestedMapping(
                path_from=prefix,
                path_to=base + "/",
                corroborations=corroborations,
            )
            if best is None or candidate.corroborations > best.corroborations:
                best = candidate
        # A corroborated shallow prefix beats any deeper one — stop early
        if best is not None and best.corroborations > 1:
            break
    return best
