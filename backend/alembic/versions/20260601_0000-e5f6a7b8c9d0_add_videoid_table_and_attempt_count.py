"""Add videoid table and attempt_count to mediatrailerstatus

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-01 00:00:00.000000

Changes:
1. Create the `videoid` table — multi-source YouTube ID store per media item
   (sources: arr, tmdb, user). Replaces the per-row youtube_id cache on
   mediatrailerstatus and the single youtube_trailer_id on media.
   No data backfill: the Arr sync task and TMDB refresh task will populate
   records on their first run.

2. Add `attempt_count` column to `mediatrailerstatus` — tracks how many times
   a download slot has been attempted, used by get_work_items() to determine
   when a FAILED slot is exhausted (attempt_count >= profile.retry_count).
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create videoid table
    op.create_table(
        "videoid",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("youtube_id", sa.String(), nullable=False),
        sa.Column("video_type", sa.String(), nullable=False, server_default="trailer"),
        sa.Column("source", sa.String(), nullable=False, server_default="user"),
        sa.Column("language", sa.String(), nullable=False, server_default=""),
        sa.Column("season", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="videoid_pkc"),
    )
    op.create_index("ix_videoid_media_id", "videoid", ["media_id"])

    # 2. Add attempt_count to mediatrailerstatus
    op.add_column(
        "mediatrailerstatus",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("mediatrailerstatus", "attempt_count")
    op.drop_index("ix_videoid_media_id", table_name="videoid")
    op.drop_table("videoid")
