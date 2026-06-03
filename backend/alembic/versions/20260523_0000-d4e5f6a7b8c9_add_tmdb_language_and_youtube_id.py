"""MediaTrailerStatus / Download / TrailerProfile additions

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-05-23 00:00:00.000000

Combines two additions:

1. Add video_type to Download (was c3d4e5f6a7b8)
   Backfills 'trailer' for rows whose file_name/path indicates a trailer;
   everything else defaults to 'other'.

2. Add tmdb_language to TrailerProfile and youtube_id to MediaTrailerStatus
   (was d4e5f6a7b8c9)
   tmdb_language: ISO 639-1 code for TMDB video lookups; empty = en-US default.
   youtube_id: TMDB-sourced YouTube key cached per status row (kept for
   transition; VideoId table is the authoritative store going forward).

Also cleans up any stale NULL-profile PENDING rows that may exist from older
migration runs.
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

    # ── Cleanup: keep only DOWNLOADED rows ───────────────────────────────────────
    # No production users have the new MediaTrailerStatus code yet, so any
    # non-DOWNLOADED rows are stale artefacts from earlier dev iterations.
    # The dynamic get_work_items() will recreate PENDING rows at runtime.

    result = conn.execute(sa.text("""
        DELETE FROM mediatrailerstatus
        WHERE status != 'downloaded'
    """))
    if result.rowcount:
        logger.info(f"Deleted {result.rowcount} non-DOWNLOADED MediaTrailerStatus row(s)")

    # ── 1. Add video_type to download ─────────────────────────────────────────────

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

    # ── 2. Add tmdb_language to trailerprofile, youtube_id to mediatrailerstatus ──

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
