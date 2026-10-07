"""Phase 9 wargame W1: the hacky extras profile — the mass-download risk.

The fixture `v0_13_1_hacky_extras.sql` holds what many libraries had
before v0.14.0: a trailer profile "Movie Featurettes" with `featurette`
in its search query and include words, a `Featurettes` folder, a
`max_duration` above the new cap, `Always Search` on, and two files it
downloaded, attributed to it. Media C also has a `Behind The Scenes`
file that no profile owns.

After the upgrade and the startup passes:

- the profile is still a trailer profile, and its files are still
  labelled `trailer`, so the profile is SATISFIED and nothing downloads;
- the unattributed Behind The Scenes file took its type from its folder,
  and the trailer profiles did not claim it (W4);
- the duration cap was clamped;
- the nudge named the profile.

Then the person follows the docs: turns `Always Search` off and sets
the Video Type to `featurette`. The downloads move with the profile, and
the profile is STILL satisfied. Zero unexpected downloads either way.
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "dbs" / "v0_13_1_hacky_extras.sql"

HACKY_PROFILE_ID = 3

CHECK_SCRIPT = """
import asyncio, json
from tasks.startup_passes import run_startup_passes
from services.trailers.trailers.pending import compute_library_pending
import database.manager.trailerprofile as profile_manager

asyncio.run(run_startup_passes())

def pending_pairs():
    summary = compute_library_pending(limit=1000, offset=0)
    return sorted((i.media_id, i.profile_id) for i in summary.items)

before = pending_pairs()
# The person follows "Switch an extras profile" in the docs.
profile_manager.update_trailerprofile_setting(3, "always_search", False)
profile_manager.update_trailerprofile_setting(3, "video_type", "featurette")
after = pending_pairs()
print("HACKY:" + json.dumps({"before": before, "after": after}))
"""


def _run(cmd: list[str], env: dict, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=timeout
    )


def test_a_hacky_extras_profile_downloads_nothing_new(tmp_path: Path):
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"
    db = sqlite3.connect(db_path)
    db.executescript(FIXTURE.read_text())
    db.commit()
    db.close()
    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
        "LOG_LEVEL": "Info",
    }

    result = _run(["uv", "run", "alembic", "upgrade", "head"], env, 180)
    assert result.returncode == 0, result.stderr[-2000:]

    db = sqlite3.connect(db_path)
    profile = db.execute(
        "SELECT video_type, max_duration, always_search FROM trailerprofile"
        " WHERE id = ?",
        (HACKY_PROFILE_ID,),
    ).fetchone()
    assert profile == ("trailer", 1200, 1), profile
    owned = db.execute(
        "SELECT video_type FROM download WHERE profile_id = ?",
        (HACKY_PROFILE_ID,),
    ).fetchall()
    assert owned == [("trailer",), ("trailer",)], owned
    assert db.execute(
        "SELECT video_type FROM download WHERE id = 13"
    ).fetchone() == ("behind_the_scenes",)
    db.close()

    result = _run(["uv", "run", "python", "-c", CHECK_SCRIPT], env, 300)
    assert result.returncode == 0, result.stderr[-3000:]
    payload = json.loads(
        [l for l in result.stdout.splitlines() if l.startswith("HACKY:")][-1][6:]
    )
    # Media A and B: the hacky profile is satisfied by its own files. Media
    # C has no featurette, so the profile is pending there, as it was
    # before the upgrade. Movie Trailers (profile 1) is pending for every
    # movie, as it was before: the fixture has no trailer files. Nothing
    # NEW is pending because of the upgrade.
    assert (1, HACKY_PROFILE_ID) not in payload["before"], payload
    assert (2, HACKY_PROFILE_ID) not in payload["before"], payload
    # After the switch to `featurette`, the same holds: the files moved
    # with the profile.
    assert (1, HACKY_PROFILE_ID) not in payload["after"], payload
    assert (2, HACKY_PROFILE_ID) not in payload["after"], payload
    assert payload["after"] == payload["before"], payload
    # The nudge named the profile, once.
    assert "'Movie Featurettes'" in result.stderr + result.stdout, (
        result.stderr[-2000:]
    )

    db = sqlite3.connect(db_path)
    assert db.execute(
        "SELECT video_type FROM trailerprofile WHERE id = ?", (HACKY_PROFILE_ID,)
    ).fetchone() == ("featurette",)
    relabelled = db.execute(
        "SELECT video_type FROM download WHERE profile_id = ?",
        (HACKY_PROFILE_ID,),
    ).fetchall()
    assert relabelled == [("featurette",), ("featurette",)], relabelled
    # W4: no trailer profile claimed the Behind The Scenes file.
    assert db.execute(
        "SELECT profile_id FROM download WHERE id = 13"
    ).fetchone() == (0,)
    db.close()
