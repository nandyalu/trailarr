"""Phase 5 CustomFilter data-migration test — plans/phase-05-drop-columns.md
wargame W1.

Builds a pre-Phase-5 database (the v0.10.2 release fixture), injects filter
rows covering every meaningful FilterCondition x {trailer_exists, status}
combination across profile (TRAILER) and view (HOME/MOVIES) filter types,
runs `alembic upgrade head`, and asserts the exact transformation table
that the v0.11.0 release notes document:

- TRAILER filters on either field: deleted.
- View trailer_exists filters: rewritten to has_downloads, value kept.
- View `status EQUALS downloaded|missing|monitored`: mapped.
- Any other view status filter: deleted.
- Unrelated filters: untouched. Emptied custom filters: kept.
"""

import os
import sqlite3
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "dbs" / "v0_10_2_monitor_intent.sql"
)

# (id, customfilter_id, filter_by, filter_condition, filter_value)
SEED_FILTERS = [
    # Profile (TRAILER, cf 1 'Movie Trailers') — all deleted
    (101, 1, "trailer_exists", "EQUALS", "false"),
    (102, 1, "trailer_exists", "EQUALS", "true"),
    (103, 1, "status", "EQUALS", "downloaded"),
    # View (cf 3 'W1 Movies View', MOVIES) — trailer_exists rewrites
    (111, 3, "trailer_exists", "EQUALS", "false"),
    (112, 3, "trailer_exists", "EQUALS", "true"),
    # View (cf 3) — status mappings
    (113, 3, "status", "EQUALS", "downloaded"),
    (114, 3, "status", "EQUALS", "missing"),
    (115, 3, "status", "EQUALS", "monitored"),
    # View (cf 3) — unmappable status filters, deleted
    (116, 3, "status", "EQUALS", "downloading"),
    (117, 3, "status", "NOT_EQUALS", "downloaded"),
    (118, 3, "status", "CONTAINS", "down"),
    (119, 3, "status", "STARTS_WITH", "mon"),
    (120, 3, "status", "ENDS_WITH", "ing"),
    (121, 3, "status", "IS_EMPTY", "-"),
    (122, 3, "status", "IS_NOT_EMPTY", "-"),
    # View (cf 3) — unrelated filter, untouched
    (123, 3, "is_movie", "EQUALS", "true"),
    # View (cf 4 'W1 Emptied View', HOME) — only unmappable rows; the
    # custom filter survives with zero conditions
    (131, 4, "status", "EQUALS", "downloading"),
]


def test_phase5_filter_migration(tmp_path: Path):
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"

    db = sqlite3.connect(db_path)
    db.executescript(BASE_FIXTURE.read_text())
    db.execute(
        "INSERT INTO customfilter (id, filter_name, filter_type)"
        " VALUES (3, 'W1 Movies View', 'MOVIES')"
    )
    db.execute(
        "INSERT INTO customfilter (id, filter_name, filter_type)"
        " VALUES (4, 'W1 Emptied View', 'HOME')"
    )
    for fid, cf_id, by, cond, value in SEED_FILTERS:
        db.execute(
            "INSERT INTO filter"
            " (id, customfilter_id, filter_by, filter_condition,"
            " filter_value) VALUES (?, ?, ?, ?, ?)",
            (fid, cf_id, by, cond, value),
        )
    db.commit()
    db.close()

    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
    }
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]

    db = sqlite3.connect(db_path)
    rows = {
        row[0]: row[1:]
        for row in db.execute(
            "SELECT id, filter_by, filter_condition, filter_value"
            " FROM filter"
        )
    }

    # Profile filters on the removed fields are gone
    for fid in (101, 102, 103):
        assert fid not in rows, f"TRAILER filter {fid} should be deleted"

    # View trailer_exists filters became has_downloads, value preserved
    assert rows[111] == ("has_downloads", "EQUALS", "false")
    assert rows[112] == ("has_downloads", "EQUALS", "true")

    # View status EQUALS mappings
    assert rows[113] == ("has_downloads", "EQUALS", "true")
    assert rows[114] == ("has_downloads", "EQUALS", "false")
    assert rows[115] == ("monitor", "EQUALS", "true")

    # Unmappable view status filters are gone
    for fid in (116, 117, 118, 119, 120, 121, 122, 131):
        assert fid not in rows, f"status filter {fid} should be deleted"

    # Unrelated filters untouched
    assert rows[123] == ("is_movie", "EQUALS", "true")

    # No filter references the removed fields anymore
    leftover = db.execute(
        "SELECT COUNT(*) FROM filter"
        " WHERE filter_by IN ('trailer_exists', 'status')"
    ).fetchone()[0]
    assert leftover == 0

    # The emptied custom filter survives (matches-all), the others too
    names = {
        row[0] for row in db.execute("SELECT filter_name FROM customfilter")
    }
    assert {"W1 Movies View", "W1 Emptied View"} <= names
    db.close()

    # Transformations are logged with the filter name (release-note promise)
    log_output = result.stderr + result.stdout
    assert "W1 Movies View" in log_output
