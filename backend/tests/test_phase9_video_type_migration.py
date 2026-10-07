"""Phase 9 video type migration test — plans/phase-09-video-types.md
decisions 2 and 10, wargames W1 and W6.

Builds a pre-Phase-9 database (the v0.11.3 release fixture), seeds
downloads with and without a profile in extras folders, a profile with a
`max_duration` of 5000, and fresh TMDB lists, runs `alembic upgrade
head`, and asserts:

- a download with no profile takes the type of its name;
- a download that a profile owns stays a trailer (W1: the profile is a
  trailer profile, and the two must agree, or the profile downloads
  again);
- `max_duration` above 1200 is clamped to 1200;
- every `last_videos_refresh` is NULL (W6: the lists hold trailers only).
"""

import os
import sqlite3
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "dbs" / "v0_11_3_download_filters.sql"
)


# The last revision before this phase (v0.13.1).
PRE_PHASE_9 = "65e07a32e5d9"


def _upgrade(data_dir: Path, target: str = "head"):
    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
    }
    return subprocess.run(
        ["uv", "run", "alembic", "upgrade", target],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _insert_download(db, row_id: int, media_id: int, path: str, profile_id: int):
    db.execute(
        "INSERT INTO download (path, file_name, file_hash, size, resolution,"
        " file_format, video_format, audio_format, audio_language,"
        " subtitle_format, subtitle_language, duration, youtube_id,"
        " youtube_channel, file_exists, profile_id, added_at, updated_at,"
        " id, media_id) VALUES (?, ?, '', 1, 1080, 'mkv', 'h264', 'aac',"
        " NULL, NULL, NULL, 120, 'unknown0000', 'unknownchannel', 1, ?,"
        " '2026-10-01 00:00:00', '2026-10-01 00:00:00', ?, ?)",
        (path, Path(path).name, profile_id, row_id, media_id),
    )


def test_the_video_type_lands_on_profiles_and_downloads(tmp_path: Path):
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    db_path = data_dir / "trailarr.db"

    db = sqlite3.connect(db_path)
    db.executescript(BASE_FIXTURE.read_text())
    db.commit()
    db.close()
    # Bring the fixture to the schema of v0.13.1 first, so the seed can
    # use the columns that Phase 8 added.
    result = _upgrade(data_dir, PRE_PHASE_9)
    assert result.returncode == 0, result.stderr

    db = sqlite3.connect(db_path)
    profile_id = db.execute("SELECT id FROM trailerprofile LIMIT 1").fetchone()[0]
    # Unattributed files in extras folders: the name says what they are.
    _insert_download(db, 101, 1, "/nonexistent/m1/Featurettes/making-of.mkv", 0)
    _insert_download(db, 102, 1, "/nonexistent/m1/Trailers/m1-teaser.mkv", 0)
    _insert_download(db, 103, 2, "/nonexistent/m2/m2-behindthescenes.mkv", 0)
    _insert_download(db, 104, 2, "/nonexistent/m2/Trailers/m2.mkv", 0)
    # A file that a (trailer) profile owns, in a Featurettes folder: W1.
    _insert_download(
        db, 105, 3, "/nonexistent/m3/Featurettes/owned.mkv", profile_id
    )
    db.execute(
        "UPDATE trailerprofile SET max_duration = 5000 WHERE id = ?",
        (profile_id,),
    )
    db.execute("UPDATE media SET last_videos_refresh = '2026-10-06 00:00:00'")
    db.commit()
    db.close()

    result = _upgrade(data_dir)
    assert result.returncode == 0, result.stderr

    db = sqlite3.connect(db_path)
    types = dict(
        db.execute("SELECT id, video_type FROM download WHERE id >= 101").fetchall()
    )
    assert types == {
        101: "featurette",
        102: "teaser",
        103: "behind_the_scenes",
        104: "trailer",
        105: "trailer",
    }
    # The rows of the fixture itself are trailers.
    assert db.execute(
        "SELECT COUNT(*) FROM download WHERE id < 101 AND video_type != 'trailer'"
    ).fetchone()[0] == 0
    assert db.execute(
        "SELECT COUNT(*) FROM trailerprofile WHERE video_type != 'trailer'"
    ).fetchone()[0] == 0
    assert db.execute(
        "SELECT max_duration FROM trailerprofile WHERE id = ?", (profile_id,)
    ).fetchone()[0] == 1200
    assert db.execute(
        "SELECT COUNT(*) FROM media WHERE last_videos_refresh IS NOT NULL"
    ).fetchone()[0] == 0
    db.close()
