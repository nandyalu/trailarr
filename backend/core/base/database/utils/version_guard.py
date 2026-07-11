"""Downgrade guard — refuse to start against a database from a NEWER app
version (plans/README.md → "Upgrade-safety rules" #5).

Migrations only ever move forward; running an older app against a
newer-schema database fails in confusing ways (unknown columns, missing
tables). Detect it up front and exit with a clear message instead.
"""

import sys
from pathlib import Path

from sqlalchemy import text

from app_logger import ModuleLogger
from core.base.database.utils.engine import engine

logger = ModuleLogger("VersionGuard")

_ALEMBIC_VERSIONS_DIR = (
    Path(__file__).resolve().parents[4] / "alembic" / "versions"
)


def _known_revisions() -> set[str]:
    """Revision ids this app version knows about, parsed from the migration
    files (no alembic runtime needed)."""
    revisions: set[str] = set()
    for f in _ALEMBIC_VERSIONS_DIR.glob("*.py"):
        for line in f.read_text().splitlines():
            stripped = line.strip().replace('"', "'")
            if stripped.startswith("revision: str = '"):
                revisions.add(stripped.split("'")[1])
                break
    return revisions


def _db_revision() -> str | None:
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).first()
            return row[0] if row else None
    except Exception:
        # Fresh database (no alembic_version table yet) — nothing to guard
        return None


def ensure_db_not_from_newer_version() -> None:
    """Exit with a clear message if the database was migrated by a newer
    app version than the one currently running."""
    db_rev = _db_revision()
    if db_rev is None:
        return
    known = _known_revisions()
    if not known or db_rev in known:
        return
    logger.error(
        f"This database was migrated by a NEWER version of Trailarr"
        f" (revision '{db_rev}' is unknown to this build). Running an older"
        " version against it is not supported. To downgrade: restore the"
        " matching pre-upgrade backup from the 'backups' folder in your"
        " config directory — see the Backup & Restore docs page. To stay on"
        " the newer version, update the image/install instead."
    )
    sys.exit(1)
