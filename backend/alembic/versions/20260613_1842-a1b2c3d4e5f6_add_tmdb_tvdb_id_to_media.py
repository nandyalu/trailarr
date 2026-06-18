"""Add tmdb_id and tvdb_id to media

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-13 18:42:05.182382

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
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tmdb_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("tvdb_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_media_tmdb_id", ["tmdb_id"])
        batch_op.create_index("ix_media_tvdb_id", ["tvdb_id"])

    # Backfill: copy txdb_id → tmdb_id for movies, tvdb_id for series,
    # only when txdb_id is a valid positive integer (skips plex-* and empty values).
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE media SET tmdb_id = CAST(txdb_id AS INTEGER) "
            "WHERE is_movie = 1 AND CAST(txdb_id AS INTEGER) > 0"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE media SET tvdb_id = CAST(txdb_id AS INTEGER) "
            "WHERE is_movie = 0 AND CAST(txdb_id AS INTEGER) > 0"
        )
    )
    logger.info(
        "Added 'tmdb_id' and 'tvdb_id' columns to media table and backfilled"
        " from txdb_id"
    )


def downgrade() -> None:
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_index("ix_media_tvdb_id")
        batch_op.drop_index("ix_media_tmdb_id")
        batch_op.drop_column("tvdb_id")
        batch_op.drop_column("tmdb_id")
