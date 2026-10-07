"""Phase 9 migration test — plans/phase-09-video-types.md decision 9 (H9).

Starts from the v0.13.0 release fixture (the last schema with
`media.youtube_trailer_id`), runs `alembic upgrade head`, and asserts:

- Backfill: an id that was only in the column becomes a SEARCH row of type
  trailer; an id that already has a row makes no duplicate.
- Saved filters: a view filter `youtube_trailer_id IS_NOT_EMPTY` becomes
  `has_videos EQUALS true`, `IS_EMPTY` becomes `has_videos EQUALS false`,
  any other condition is deleted, and a profile filter on the field is
  deleted (`has_videos` is view-only).
- The column is gone.
- Every change is logged with the filter name.
- The Phase 9 duration cap: the profile with `max_duration = 5000` ends at
  1200, and every profile still loads through the manager.
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURE = (
    Path(__file__).parent / "fixtures" / "dbs" / "v0_13_0_media_videos.sql"
)

LOAD_PROFILES_SCRIPT = """
import json
import database.manager.trailerprofile as manager
profiles = manager.get_trailerprofiles()
print("PROFILES:" + json.dumps({p.id: p.max_duration for p in profiles}))
"""


def _env(data_dir: Path) -> dict:
    return {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
    }


def _run(cmd: list[str], data_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=BACKEND_DIR,
        env=_env(data_dir),
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.fixture(scope="module")
def upgraded(tmp_path_factory):
    """The fixture database after `alembic upgrade head`, plus the log."""
    data_dir = tmp_path_factory.mktemp("appdata")
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"

    db = sqlite3.connect(db_path)
    db.executescript(FIXTURE.read_text())
    # The fixture state the test relies on.
    assert db.execute(
        "SELECT youtube_trailer_id FROM media WHERE id = 1"
    ).fetchone() == ("orphan00001",)
    assert (
        db.execute(
            "SELECT COUNT(*) FROM mediavideo WHERE media_id = 1"
        ).fetchone()[0]
        == 0
    )
    db.commit()
    db.close()

    result = _run(["uv", "run", "alembic", "upgrade", "head"], data_dir)
    assert result.returncode == 0, result.stderr[-2000:]
    return data_dir, db_path, result.stderr + result.stdout


def _filters(db, customfilter_id: int) -> list[tuple]:
    return list(
        db.execute(
            'SELECT filter_by, filter_condition, filter_value FROM "filter"'
            " WHERE customfilter_id = ? ORDER BY id",
            (customfilter_id,),
        )
    )


def test_the_column_is_gone(upgraded):
    _, db_path, _ = upgraded
    db = sqlite3.connect(db_path)
    columns = [row[1] for row in db.execute("PRAGMA table_info(media)")]
    db.close()
    assert "youtube_trailer_id" not in columns
    # The rest of the row survived the batch rebuild.
    assert {"title", "folder_path", "last_videos_refresh"} <= set(columns)


def test_an_orphan_id_becomes_a_search_row(upgraded):
    _, db_path, _ = upgraded
    db = sqlite3.connect(db_path)
    rows = list(
        db.execute(
            "SELECT video_id, source, video_type, season, sequence, language"
            " FROM mediavideo WHERE media_id = 1"
        )
    )
    db.close()
    assert rows == [("orphan00001", "SEARCH", "trailer", None, 0, None)]


def test_an_id_with_a_row_makes_no_duplicate(upgraded):
    _, db_path, _ = upgraded
    db = sqlite3.connect(db_path)
    rows = list(
        db.execute(
            "SELECT video_id, source FROM mediavideo WHERE media_id = 2"
            " ORDER BY id"
        )
    )
    none = db.execute(
        "SELECT COUNT(*) FROM mediavideo WHERE media_id = 3"
    ).fetchone()[0]
    db.close()
    # The TMDB row keeps its source: the column's id was already known.
    assert rows == [
        ("uservid0002", "USER"),
        ("tmdbvid0002", "TMDB"),
        ("tmdbfeat002", "TMDB"),
    ]
    # Media 3 had no id in the column; its two rows stay as they were.
    assert none == 2


def test_view_filters_become_has_videos(upgraded):
    _, db_path, _ = upgraded
    db = sqlite3.connect(db_path)
    has = _filters(db, 3)
    has_not = _filters(db, 4)
    db.close()
    assert has == [("has_videos", "EQUALS", "true")]
    assert has_not == [("has_videos", "EQUALS", "false")]


def test_an_unmappable_view_filter_is_deleted(upgraded):
    _, db_path, _ = upgraded
    db = sqlite3.connect(db_path)
    specific = _filters(db, 5)
    # The custom filter itself stays; it now matches everything.
    kept = db.execute(
        "SELECT filter_name FROM customfilter WHERE id = 5"
    ).fetchone()
    db.close()
    assert specific == []
    assert kept == ("One specific video",)


def test_a_profile_filter_on_the_field_is_deleted(upgraded):
    """`has_videos` is view-only: a profile cannot filter on the known
    videos, so its condition is removed and the other conditions stay."""
    _, db_path, _ = upgraded
    db = sqlite3.connect(db_path)
    long_trailers = _filters(db, 2)
    italian = _filters(db, 1)
    remaining = db.execute(
        "SELECT COUNT(*) FROM \"filter\" WHERE filter_by = 'youtube_trailer_id'"
    ).fetchone()[0]
    db.close()
    assert long_trailers == [("is_movie", "EQUALS", "true")]
    assert italian == [("is_movie", "EQUALS", "true")]
    assert remaining == 0


def test_every_change_is_logged_with_the_filter_name(upgraded):
    _, _, log_output = upgraded
    assert "Has a YouTube id" in log_output
    assert "has_videos EQUALS true" in log_output
    assert "No YouTube id" in log_output
    assert "has_videos EQUALS false" in log_output
    assert "One specific video" in log_output
    assert "Long Trailers" in log_output
    # The backfill says how many ids it moved.
    assert "moved 1 YouTube ids" in log_output


def test_the_duration_cap_and_every_profile_loads(upgraded):
    """Decision 10: a stored `max_duration = 5000` ends at 1200, and the
    profile list still loads through the manager (the model validates the
    range, so a value above the cap would fail here, not in the UI)."""
    data_dir, db_path, _ = upgraded
    result = _run(["uv", "run", "python", "-c", LOAD_PROFILES_SCRIPT], data_dir)
    assert result.returncode == 0, result.stderr[-2000:]
    line = next(
        line for line in result.stdout.splitlines() if line.startswith("PROFILES:")
    )
    profiles = json.loads(line[len("PROFILES:") :])
    assert profiles == {"1": 600, "2": 1200}
