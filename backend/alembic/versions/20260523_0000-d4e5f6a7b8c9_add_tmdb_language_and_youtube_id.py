"""MediaTrailerStatus / Download / TrailerProfile additions

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-05-23 00:00:00.000000

Combines three originally-separate migrations:

1. Fix orphaned NULL-profile PENDING rows (was b2c3d4e5f6a7)
   The previous migration (a1b2c3d4e5f6) created PENDING rows with
   profile_id=NULL for all undownloaded media. Those rows are permanently
   orphaned because get_pending_rows() requires profile_id IS NOT NULL.
   Replaces them with proper profile-linked rows.

2. Add video_type to Download (was c3d4e5f6a7b8)
   Backfills 'trailer' for rows whose file_name/path indicates a trailer;
   everything else defaults to 'other'.

3. Add tmdb_language to TrailerProfile and youtube_id to MediaTrailerStatus
   (was d4e5f6a7b8c9)
   tmdb_language: ISO 639-1 code for TMDB video lookups; empty = en-US default.
   youtube_id: TMDB-sourced YouTube key cached per status row so the download
   task can skip redundant live TMDB calls.
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from app_logger import ModuleLogger

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()

    # ── 1. Fix orphaned NULL-profile PENDING rows ──────────────────────────────

    result = conn.execute(sa.text("""
        DELETE FROM mediatrailerstatus
        WHERE profile_id IS NULL AND status = 'pending'
    """))
    logger.info(f"Deleted {result.rowcount} orphaned NULL-profile PENDING rows")

    result = conn.execute(sa.text("""
        INSERT INTO mediatrailerstatus
            (media_id, profile_id, season, sequence, status, source, created_at, updated_at)
        SELECT
            m.id,
            tp.id,
            0, 1, 'pending', 'app', :now, :now
        FROM media m
        CROSS JOIN trailerprofile tp
        WHERE tp.enabled = 1
          AND m.is_movie = tp.for_movies
          AND m.downloaded_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM mediatrailerstatus mts2
              WHERE mts2.media_id = m.id AND mts2.profile_id = tp.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM mediatrailerstatus mts3
              WHERE mts3.media_id = m.id AND mts3.status = 'downloaded'
          )
    """), {"now": now})
    logger.info(f"Created {result.rowcount} profile-linked PENDING rows for undownloaded media")

    result = conn.execute(sa.text("""
        INSERT INTO mediatrailerstatus
            (media_id, profile_id, season, sequence, status, source, created_at, updated_at)
        WITH RECURSIVE seasons(n) AS (
            SELECT 1
            UNION ALL
            SELECT n + 1 FROM seasons WHERE n < 50
        )
        SELECT
            m.id,
            tp.id,
            s.n,
            1, 'pending', 'app', :now, :now
        FROM media m
        CROSS JOIN trailerprofile tp
        JOIN seasons s ON s.n <= m.season_count
        WHERE tp.enabled = 1
          AND tp.for_movies = 0
          AND tp.download_season_videos = 1
          AND m.is_movie = 0
          AND m.season_count > 0
          AND m.downloaded_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM mediatrailerstatus mts2
              WHERE mts2.media_id = m.id
                AND mts2.profile_id = tp.id
                AND mts2.season = s.n
          )
          AND NOT EXISTS (
              SELECT 1 FROM mediatrailerstatus mts3
              WHERE mts3.media_id = m.id AND mts3.status = 'downloaded'
          )
    """), {"now": now})
    logger.info(f"Created {result.rowcount} per-season PENDING rows for series media")

    # ── 2. Add video_type to download ──────────────────────────────────────────

    with op.batch_alter_table("download", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("video_type", sa.String(), server_default="other", nullable=False)
        )
    logger.info("Added 'video_type' column to download table")

    result = conn.execute(sa.text("""
        UPDATE download
        SET video_type = 'trailer'
        WHERE LOWER(file_name) LIKE '%trailer%'
           OR LOWER(path) LIKE '%/trailers/%'
    """))
    logger.info(f"Backfilled 'trailer' video_type for {result.rowcount} existing download rows")

    # ── 3. Add tmdb_language to trailerprofile, youtube_id to mediatrailerstatus

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("tmdb_language", sa.String(), server_default="", nullable=False)
        )
    logger.info("Added 'tmdb_language' column to trailerprofile table")

    with op.batch_alter_table("mediatrailerstatus", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("youtube_id", sa.String(), nullable=True)
        )
    logger.info("Added 'youtube_id' column to mediatrailerstatus table")


def downgrade() -> None:
    conn = op.get_bind()

    with op.batch_alter_table("mediatrailerstatus", schema=None) as batch_op:
        batch_op.drop_column("youtube_id")
    logger.info("Dropped 'youtube_id' column from mediatrailerstatus table")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("tmdb_language")
    logger.info("Dropped 'tmdb_language' column from trailerprofile table")

    with op.batch_alter_table("download", schema=None) as batch_op:
        batch_op.drop_column("video_type")
    logger.info("Dropped 'video_type' column from download table")

    conn.execute(sa.text("""
        DELETE FROM mediatrailerstatus
        WHERE profile_id IS NOT NULL AND status = 'pending' AND source = 'app'
    """))
    logger.info("Downgrade: removed profile-linked pending rows created by this migration")
