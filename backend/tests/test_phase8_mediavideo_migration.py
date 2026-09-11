"""Phase 8 MediaVideo migration test — plans/phase-08-tmdb.md decision 5.

Builds a pre-Phase-8 database (the v0.11.3 release fixture), gives some
media a `youtube_trailer_id` and some none, runs `alembic upgrade head`,
and asserts the ids moved into the candidates table.

The resolver reads only the table from Phase 8 on, so an id that stayed
behind in the column is an id that Trailarr would stop using.

Every migrated row is a SEARCH row. The column does not record where its
id came from — Radarr reports one, Sonarr reports none because its
metadata comes from TVDB, and a finished download overwrites the column
with the video it took — so the migration does not guess. The sync marks
the ids the Arr reports, which is the only source that knows.
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
    # A Sonarr series with a stored id. Sonarr reports no trailer id, so
    # this one is a video Trailarr found itself and wrote back after the
    # download — it must not be labelled as coming from the Arr.
    db.execute(
        "INSERT INTO connection VALUES"
        " ('Fixture Sonarr','SONARR','http://localhost:8989','k',2,"
        "  '2026-08-21 00:00:00','',NULL,1)"
    )
    db.execute(
        "INSERT INTO media (connection_id, arr_id, is_movie, title, year,"
        " language, runtime, youtube_trailer_id, folder_path, txdb_id, id,"
        " added_at, updated_at, monitor, arr_monitored, clean_title, studio,"
        " media_exists, media_filename, title_slug, season_count)"
        " VALUES (2, 900, 0, 'Fixture Series', 2024, 'en', 30,"
        " 'seriesFoundId', '/nonexistent/fixture/Series', 'fx-900', 900,"
        " '2026-08-21 00:00:00', '2026-08-21 00:00:00', 1, 1, '', '', 0,"
        " '', '', 0)"
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

    # The media that had an id, and the Sonarr series.
    assert len(rows) == 2, f"expected two rows, got {rows}"

    # The Sonarr series: the id is Trailarr's own, not the Arr's.
    series = [r for r in rows if r[0] == 900][0]
    assert series[1] == "seriesFoundId"
    assert series[2] == "SEARCH", (
        "Sonarr reports no trailer id, so a stored one came from a search"
    )
    # And it stays a SEARCH row, because no sync will ever report it: the
    # promotion below happens only for an id the Arr really sends.

    rows = [r for r in rows if r[0] != 900]
    media_id, video_id, source, video_type, season, sequence = rows[0]
    assert media_id == 1
    assert video_id == "dQw4w9WgXcQ"
    # The enum column stores the NAME of the member, not its value.
    # SEARCH, not ARR: only a sync can say where an id came from.
    assert source == "SEARCH"
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
