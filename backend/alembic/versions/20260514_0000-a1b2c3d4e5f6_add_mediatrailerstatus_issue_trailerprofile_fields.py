"""Add MediaTrailerStatus and Issue tables, add for_movies/download_season_videos/max_count/video_type to TrailerProfile, drop trailer_exists and status from media

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # --- Create mediatrailerstatus table ---
    op.create_table(
        "mediatrailerstatus",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("season", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sequence", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(), nullable=False, server_default="app"),
        sa.Column("linked_download_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id"], ["media.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["trailerprofile.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["linked_download_id"], ["download.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "media_id", "profile_id", "season", "sequence",
            name="uq_mediatrailerstatus_media_profile_season_sequence",
        ),
    )
    op.create_index("ix_mediatrailerstatus_media_id", "mediatrailerstatus", ["media_id"])
    op.create_index("ix_mediatrailerstatus_profile_id", "mediatrailerstatus", ["profile_id"])
    logger.info("Created 'mediatrailerstatus' table")

    # --- Create issue table ---
    op.create_table(
        "issue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_issue_entity",
        "issue",
        ["issue_type", "entity_type", "entity_id"],
        unique=True,
    )
    logger.info("Created 'issue' table")

    # --- Add new columns to trailerprofile ---
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "video_type",
                sa.String(),
                server_default="trailer",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "for_movies",
                sa.Boolean(),
                server_default="1",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "download_season_videos",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "max_count",
                sa.Integer(),
                server_default="1",
                nullable=False,
            )
        )
    logger.info(
        "Added 'video_type', 'for_movies', 'download_season_videos', 'max_count'"
        " columns to trailerprofile table"
    )

    # --- Drop trailer_exists and status from media ---
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("trailer_exists")
        batch_op.drop_column("status")
    logger.info("Dropped 'trailer_exists' and 'status' columns from media table")

    # --- Backfill MediaTrailerStatus for existing DOWNLOADED media ---
    # For media that had downloaded_at set, create a single DOWNLOADED row
    # with profile_id=NULL (manually placed / unattributed).
    conn = op.get_bind()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        sa.text(
            """
            INSERT INTO mediatrailerstatus
                (media_id, profile_id, season, sequence, status, source,
                 linked_download_id, created_at, updated_at)
            SELECT
                m.id, NULL, 0, 1, 'downloaded', 'manual',
                NULL, :now, :now
            FROM media m
            WHERE m.downloaded_at IS NOT NULL
            """
        ),
        {"now": now},
    )
    logger.info("Backfilled MediaTrailerStatus rows for existing downloaded media")

    # --- Backfill MediaTrailerStatus for monitored media without downloads ---
    conn.execute(
        sa.text(
            """
            INSERT INTO mediatrailerstatus
                (media_id, profile_id, season, sequence, status, source,
                 linked_download_id, created_at, updated_at)
            SELECT
                m.id, NULL, 0, 1, 'pending', 'app',
                NULL, :now, :now
            FROM media m
            WHERE m.monitor = 1
              AND m.downloaded_at IS NULL
            """
        ),
        {"now": now},
    )
    logger.info("Backfilled pending MediaTrailerStatus rows for monitored media")


def downgrade() -> None:
    # Re-add status and trailer_exists columns to media
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "trailer_exists",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(),
                server_default="missing",
                nullable=False,
            )
        )

    # Drop new trailerprofile columns
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("max_count")
        batch_op.drop_column("download_season_videos")
        batch_op.drop_column("for_movies")
        batch_op.drop_column("video_type")

    # Drop new tables
    op.drop_table("issue")
    op.drop_table("mediatrailerstatus")
    logger.info("Downgrade complete: dropped issue, mediatrailerstatus tables and reverted media/trailerprofile columns")
