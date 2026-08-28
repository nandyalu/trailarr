"""Release-fixture upgrade gauntlet — plans/README.md "Upgrade-safety rules"
rule 4.

Every fixture in tests/fixtures/dbs/ is a database snapshot from a released
version (as a SQL dump). For each one this test: restores it into a fresh
APP_DATA_DIR, runs the FULL alembic chain to head, runs ALL startup passes,
and asserts the core invariants. This is what proves version-skipping
upgrades stay safe, release after release — add one fixture per release.

Runs in subprocesses so each fixture gets a truly isolated APP_DATA_DIR
(the in-process engine is bound to the test session's data dir).
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURES = sorted(
    (Path(__file__).parent / "fixtures" / "dbs").glob("*.sql")
)

# Media row count per fixture. Every fixture seeds 3 movies; the ones that
# also carry Plex state add rows on top.
EXPECTED_MEDIA = {
    "v0_11_1_plex_linked": 5,
}
DEFAULT_MEDIA_COUNT = 3

PASS_SCRIPT = """
import asyncio, json
from tasks.startup_passes import run_startup_passes, downloads_ready
import database.manager.connection as connection_manager
import database.manager.media as media_manager

asyncio.run(run_startup_passes())
media_count = sum(1 for _ in media_manager.read_all_generator())

# Library-root guard: a media row whose folder IS a library root (bad data
# from before v0.11.2) must never be returned for a path under that root.
roots = {
    pm.path_to.rstrip("/\\\\")
    for conn in connection_manager.read_all()
    for pm in conn.path_mappings
    if pm.path_to
}
root_rows = [
    m
    for m in media_manager.read_all()
    if m.folder_path and m.folder_path.rstrip("/\\\\") in roots
]
captured = []
for row in root_rows:
    probe = row.folder_path.rstrip("/\\\\") + "/Gauntlet Probe Show (2024)"
    found = media_manager.read_by_folder_path(probe)
    if found is not None and found.id == row.id:
        captured.append(row.id)

print("GAUNTLET:" + json.dumps({
    "ready": downloads_ready(),
    "media": media_count,
    "root_rows": [m.id for m in root_rows],
    "captured": captured,
}))
"""


def _run(cmd: list[str], env: dict, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.stem)
def test_upgrade_gauntlet(fixture: Path, tmp_path: Path):
    assert FIXTURES, "no gauntlet fixtures found"
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)

    # Restore the release snapshot
    db = sqlite3.connect(data_dir / "trailarr.db")
    db.executescript(fixture.read_text())
    db.close()

    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
    }

    # 1. The full migration chain applies cleanly
    result = _run(["uv", "run", "alembic", "upgrade", "head"], env, 120)
    assert result.returncode == 0, (
        f"migration failed for {fixture.stem}:\n{result.stderr[-2000:]}"
    )

    # 1b. Phase 5 invariants: legacy columns are gone and no saved filter
    # references them anymore
    db = sqlite3.connect(data_dir / "trailarr.db")
    media_cols = {r[1] for r in db.execute("PRAGMA table_info(media)")}
    profile_cols = {
        r[1] for r in db.execute("PRAGMA table_info(trailerprofile)")
    }
    legacy_filters = db.execute(
        "SELECT COUNT(*) FROM filter"
        " WHERE filter_by IN ('trailer_exists', 'status')"
    ).fetchone()[0]
    db.close()
    assert "trailer_exists" not in media_cols, media_cols
    assert "status" not in media_cols, media_cols
    assert "stop_monitoring" not in profile_cols, profile_cols
    assert legacy_filters == 0, f"{legacy_filters} legacy filter rows left"

    # 2. All startup passes run to completion and unlock downloads
    result = _run(["uv", "run", "python", "-c", PASS_SCRIPT], env, 300)
    assert result.returncode == 0, (
        f"startup passes failed for {fixture.stem}:\n{result.stderr[-2000:]}"
    )
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("GAUNTLET:")
    ]
    assert lines, f"no gauntlet payload in output:\n{result.stdout[-2000:]}"
    payload = json.loads(lines[-1][len("GAUNTLET:"):])

    # Core invariants: download engine unlocked and no media lost
    assert payload["ready"] is True, payload
    expected = EXPECTED_MEDIA.get(fixture.stem, DEFAULT_MEDIA_COUNT)
    assert payload["media"] == expected, payload

    # A row whose folder is a library root never captures media under it
    assert payload["captured"] == [], payload
