"""The retention policy for database backups.

Trailarr copies the database before it runs migrations, on every start. The
copy is what `database/version_guard.py` tells a user to restore after a
downgrade, so the backups matter — but nothing deleted them except a cap of 30
files. A 45 MB database therefore bounded at 1.35 GB, and a user found 1.5 GB
of backups (issue #681).

Retention now has two limits. Trailarr keeps the newest `BACKUP_KEEP_COUNT`
backups, and deletes any backup older than `BACKUP_KEEP_DAYS` days. Both limits
apply: a backup must satisfy both to stay. The count limit bounds a user who
restarts often. The age limit removes the stale files of a user who restarts
rarely, whose 30 old backups could sit on the disk for years.

Four paths make backups — the Docker start script, the direct-install start
script, the CLI updater and the development launcher. This module is the one
place that decides what to delete, so the four cannot drift apart. The Docker
script runs it as a command; the others import `prune_backups`.

It uses the standard library only, and imports nothing from `backend/`. It runs
before the application starts, and before the virtual environment is certain.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

DEFAULT_KEEP_COUNT = 10
DEFAULT_KEEP_DAYS = 30

#: Database copies that the start scripts write.
BACKUP_GLOB = "trailarr_*.db"
#: Folders that the CLI updater writes, one for each version it installs.
UPDATE_DIR_GLOB = "update_*"


def _positive_int(name: str, default: int) -> int:
    """Read a whole number from the environment, or return the default.

    A value below 1 would delete the backup that was just taken, which the
    migration-failure path restores from, so 1 is the floor.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def keep_count() -> int:
    """How many backups to keep, from BACKUP_KEEP_COUNT."""
    return _positive_int("BACKUP_KEEP_COUNT", DEFAULT_KEEP_COUNT)


def keep_days() -> int:
    """How many days to keep a backup, from BACKUP_KEEP_DAYS."""
    return _positive_int("BACKUP_KEEP_DAYS", DEFAULT_KEEP_DAYS)


def _entries(backups_dir: Path) -> list[Path]:
    """Every backup in the folder, newest first."""
    found = list(backups_dir.glob(BACKUP_GLOB))
    found += [p for p in backups_dir.glob(UPDATE_DIR_GLOB) if p.is_dir()]
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def _size_of(path: Path) -> int:
    if path.is_dir():
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return path.stat().st_size


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def prune_backups(
    backups_dir: Path | str,
    count: int | None = None,
    days: int | None = None,
) -> tuple[list[Path], int]:
    """Delete the backups that fall outside both limits.

    A backup stays only if it is among the newest `count` AND is younger than
    `days` days. The backup taken by the current run is the newest and is zero
    days old, so no run can delete the copy it may have to restore from.

    Args:
        backups_dir: The folder that holds the backups.
        count: How many to keep. Reads BACKUP_KEEP_COUNT when not given.
        days: How many days to keep one. Reads BACKUP_KEEP_DAYS when not given.

    Returns:
        The backups that were deleted, and the bytes they used.
    """
    folder = Path(backups_dir)
    if not folder.is_dir():
        return [], 0

    count = keep_count() if count is None else max(1, count)
    days = keep_days() if days is None else max(1, days)
    cutoff = time.time() - (days * 86400)

    deleted: list[Path] = []
    freed = 0
    for position, path in enumerate(_entries(folder)):
        try:
            too_many = position >= count
            too_old = path.stat().st_mtime < cutoff
            if not (too_many or too_old):
                continue
            freed += _size_of(path)
            _remove(path)
            deleted.append(path)
        except OSError:
            # A backup that cannot be read or deleted is left alone. Retention
            # must never stop the application from starting.
            continue
    return deleted, freed


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def main(argv: list[str]) -> int:
    """Prune the folder given on the command line, and say what was done."""
    if len(argv) != 2:
        print("usage: backup_retention.py <backups-dir>", file=sys.stderr)
        return 2

    folder = Path(argv[1])
    count, days = keep_count(), keep_days()
    deleted, freed = prune_backups(folder, count, days)
    if deleted:
        print(
            f"Deleted {len(deleted)} backup(s), {human_size(freed)} freed. "
            f"Trailarr keeps {count} backups, for {days} days."
        )
    else:
        kept = len(_entries(folder))
        print(
            f"Kept all {kept} backup(s). "
            f"Trailarr keeps {count} backups, for {days} days."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
