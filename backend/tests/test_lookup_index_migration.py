"""The index migrations of v0.14.2 (#732, #733).

Builds a v0.13.1 database from its release fixture, runs `alembic upgrade
head`, and checks that the four lookup indexes exist and that ANALYZE
wrote the first statistics of the query planner. Three indexes come from
#732. The index on `download.path` (#733) comes in the next revision.
"""

import os
import sqlite3
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "dbs" / "v0_13_1_hacky_extras.sql"
)
INDEXES = {
    "ix_download_media_id",
    "ix_download_path",
    "ix_filefolderinfo_media_id",
    "ix_filefolderinfo_parent_id",
}


def _alembic(data_dir: Path, *args: str):
    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
    }
    return subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _index_names(db_path: Path) -> set[str]:
    db = sqlite3.connect(db_path)
    try:
        return {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
    finally:
        db.close()


def test_the_upgrade_adds_the_indexes_and_the_statistics(tmp_path: Path):
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"
    db = sqlite3.connect(db_path)
    db.executescript(BASE_FIXTURE.read_text())
    db.commit()
    db.close()
    assert not INDEXES & _index_names(db_path)

    result = _alembic(data_dir, "upgrade", "head")
    assert result.returncode == 0, result.stderr[-2000:]

    assert INDEXES <= _index_names(db_path)
    db = sqlite3.connect(db_path)
    try:
        count = db.execute("SELECT COUNT(*) FROM sqlite_stat1").fetchone()[0]
    finally:
        db.close()
    assert count > 0

    # The revision before the indexes of v0.14.2.
    result = _alembic(data_dir, "downgrade", "d4e6f1a7b3c5")
    assert result.returncode == 0, result.stderr[-2000:]
    assert not INDEXES & _index_names(db_path)
