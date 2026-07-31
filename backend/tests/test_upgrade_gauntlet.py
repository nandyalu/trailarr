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

PASS_SCRIPT = """
import asyncio, json
from core.tasks.startup_passes import run_startup_passes, downloads_ready
import core.base.database.manager.media as media_manager

asyncio.run(run_startup_passes())
media_count = sum(1 for _ in media_manager.read_all_generator())
print("GAUNTLET:" + json.dumps({
    "ready": downloads_ready(),
    "media": media_count,
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
    assert payload["media"] == 3, payload
