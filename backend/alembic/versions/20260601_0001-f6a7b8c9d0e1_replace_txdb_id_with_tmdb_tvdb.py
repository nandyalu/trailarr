"""Replace txdb_id with tmdb_id and tvdb_id on Media

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-01 00:01:00.000000

txdb_id was a single field holding either a TMDB ID (for movies via Radarr)
or a TVDB ID (for series via Sonarr). This caused TMDB API calls for series
to silently use the wrong ID type. Splitting into tmdb_id + tvdb_id lets the
TMDB service use the correct identifier for all media types.

Backfill: movies get tmdb_id = txdb_id; series get tvdb_id = txdb_id.
Synthetic plex- prefixed values are skipped (no real external identifier).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from app_logger import ModuleLogger

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Add new columns ────────────────────────────────────────────────────
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "tmdb_id", sa.String(), server_default="", nullable=False
            )
        )
        batch_op.add_column(
            sa.Column(
                "tvdb_id", sa.String(), server_default="", nullable=False
            )
        )
    logger.info("Added 'tmdb_id' and 'tvdb_id' columns to media table")

    # ── 2. Backfill from txdb_id ──────────────────────────────────────────────
    result = conn.execute(
        sa.text(
            "UPDATE media SET tmdb_id = txdb_id WHERE is_movie = 1 AND txdb_id"
            " NOT LIKE 'plex-%'"
        )
    )
    logger.info(f"Backfilled tmdb_id for {result.rowcount} movie row(s)")

    result = conn.execute(
        sa.text(
            "UPDATE media SET tvdb_id = txdb_id WHERE is_movie = 0 AND txdb_id"
            " NOT LIKE 'plex-%'"
        )
    )
    logger.info(f"Backfilled tvdb_id for {result.rowcount} series row(s)")

    # ── 3. Drop txdb_id column and its index ──────────────────────────────────
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_index("ix_media_txdb_id")
        batch_op.drop_column("txdb_id")
    logger.info("Dropped 'txdb_id' column and index from media table")

    # ── 4. Create new indexes ─────────────────────────────────────────────────
    op.create_index("ix_media_tmdb_id", "media", ["tmdb_id"])
    op.create_index("ix_media_tvdb_id", "media", ["tvdb_id"])
    logger.info("Created indexes on 'tmdb_id' and 'tvdb_id'")

    # ── 5. Migrate filter rows that reference txdb_id ─────────────────────────
    # Custom filters store the field name as a plain string in filter.filter_by.
    # Remap to tmdb_id (best-effort; series-only profiles using tvdb_id will
    # need to be manually updated to filter_by='tvdb_id').
    result = conn.execute(
        sa.text(
            "UPDATE \"filter\" SET filter_by = 'tmdb_id' WHERE filter_by ="
            " 'txdb_id'"
        )
    )
    if result.rowcount:
        logger.info(
            f"Remapped {result.rowcount} filter row(s) from txdb_id → tmdb_id"
            " (series-specific filters may need to be updated to tvdb_id)"
        )

    # ── 6. Migrate template strings in trailerprofile ─────────────────────────
    # search_query and custom_folder can contain {txdb_id} placeholders.
    result = conn.execute(
        sa.text(
            "UPDATE trailerprofile SET search_query = REPLACE(search_query,"
            " '{txdb_id}', '{tmdb_id}') WHERE search_query LIKE '%{txdb_id}%'"
        )
    )
    if result.rowcount:
        logger.info(
            f"Updated {result.rowcount} trailerprofile search_query string(s)"
            " from {{txdb_id}} → {{tmdb_id}}"
        )

    result = conn.execute(
        sa.text(
            "UPDATE trailerprofile SET custom_folder = REPLACE(custom_folder,"
            " '{txdb_id}', '{tmdb_id}') WHERE custom_folder LIKE '%{txdb_id}%'"
        )
    )
    if result.rowcount:
        logger.info(
            f"Updated {result.rowcount} trailerprofile custom_folder string(s)"
            " from {{txdb_id}} → {{tmdb_id}}"
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Restore filter rows and template strings
    conn.execute(
        sa.text(
            "UPDATE \"filter\" SET filter_by = 'txdb_id' WHERE filter_by ="
            " 'tmdb_id'"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE trailerprofile SET search_query = REPLACE(search_query,"
            " '{tmdb_id}', '{txdb_id}') WHERE search_query LIKE '%{tmdb_id}%'"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE trailerprofile SET custom_folder = REPLACE(custom_folder,"
            " '{tmdb_id}', '{txdb_id}') WHERE custom_folder LIKE '%{tmdb_id}%'"
        )
    )

    op.drop_index("ix_media_tvdb_id", table_name="media")
    op.drop_index("ix_media_tmdb_id", table_name="media")

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "txdb_id", sa.String(), server_default="", nullable=False
            )
        )

    # Restore txdb_id from whichever field is non-empty
    conn.execute(
        sa.text(
            "UPDATE media SET txdb_id = tmdb_id WHERE is_movie = 0 AND tmdb_id"
            " != ''"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE media SET txdb_id = tvdb_id WHERE is_movie = 1 AND tvdb_id"
            " != ''"
        )
    )

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("tvdb_id")
        batch_op.drop_column("tmdb_id")

    op.create_index("ix_media_txdb_id", "media", ["txdb_id"])
    logger.info(
        "Downgrade complete: restored txdb_id, dropped tmdb_id and tvdb_id"
    )
