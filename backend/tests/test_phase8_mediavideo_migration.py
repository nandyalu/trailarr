"""Phase 8 MediaVideo migration test — plans/phase-08-tmdb.md decision 5.

Builds a pre-Phase-8 database (the v0.11.3 release fixture), gives some
media a `youtube_trailer_id` and some none, runs `alembic upgrade head`,
and asserts that the ids moved into the candidates table as ARR rows and
that nothing else did.

The resolver reads only the table from Phase 8 on, so an id that stayed
behind in the column is an id that Trailarr would stop using.
"""

import os
import sqlite3
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "dbs" / "v0_11_3_download_filters.sql"
)

# media id -> the youtube_trailer_id it holds before the migration
SEED_IDS = {
    1: "dQw4w9WgXcQ",  # a normal id, moves
    2: "",  # empty string, does not move
    3: None,  # NULL, does not move
}


def _upgrade(data_dir: Path):
    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
    }
    return subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_arr_ids_move_into_the_candidates_table(tmp_path: Path):
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"

    db = sqlite3.connect(db_path)
    db.executescript(BASE_FIXTURE.read_text())
    for media_id, yt_id in SEED_IDS.items():
        db.execute(
            "UPDATE media SET youtube_trailer_id = ? WHERE id = ?",
            (yt_id, media_id),
        )
    db.commit()
    db.close()

    result = _upgrade(data_dir)
    assert result.returncode == 0, result.stderr[-2000:]

    db = sqlite3.connect(db_path)
    rows = list(
        db.execute(
            "SELECT media_id, video_id, source, video_type, season, sequence"
            " FROM mediavideo ORDER BY media_id"
        )
    )

    # Only the media that had an id gets a row.
    assert len(rows) == 1, f"expected one ARR row, got {rows}"
    media_id, video_id, source, video_type, season, sequence = rows[0]
    assert media_id == 1
    assert video_id == "dQw4w9WgXcQ"
    # The enum column stores the NAME of the member, not its value.
    assert source == "ARR"
    assert video_type == "trailer"
    assert season is None
    assert sequence == 0

    # The column keeps its value; Phase 9 removes it (H9).
    kept = db.execute(
        "SELECT youtube_trailer_id FROM media WHERE id = 1"
    ).fetchone()[0]
    assert kept == "dQw4w9WgXcQ"
    db.close()


def test_the_migration_is_safe_to_run_on_a_library_with_no_ids(tmp_path: Path):
    """Every id is empty or NULL: the table is created and stays empty."""
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"

    db = sqlite3.connect(db_path)
    db.executescript(BASE_FIXTURE.read_text())
    db.execute("UPDATE media SET youtube_trailer_id = NULL")
    db.commit()
    db.close()

    result = _upgrade(data_dir)
    assert result.returncode == 0, result.stderr[-2000:]

    db = sqlite3.connect(db_path)
    assert db.execute("SELECT COUNT(*) FROM mediavideo").fetchone()[0] == 0
    # The attempt table gained the column the resolver needs.
    columns = [r[1] for r in db.execute("PRAGMA table_info(downloadattempt)")]
    assert "last_video_id" in columns
    db.close()
