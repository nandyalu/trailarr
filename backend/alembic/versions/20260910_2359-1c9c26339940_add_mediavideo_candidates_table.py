"""Add MediaVideo candidates table

Revision ID: 1c9c26339940
Revises: b30b7b2fd9b4
Create Date: 2026-09-10 23:59:41.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


revision: str = "1c9c26339940"
down_revision: Union[str, None] = "b30b7b2fd9b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    op.create_table(
        "mediavideo",
        sa.Column("video_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "USER", "TMDB", "ARR", "SEARCH",
                name="videosource",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("video_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("official", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media.id"],
            name=op.f("fk_mediavideo_media_id_media"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("mediavideo_pkc")),
        sa.UniqueConstraint(
            "media_id", "video_id", name="uq_mediavideo_media_video"
        ),
    )
    with op.batch_alter_table("mediavideo", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_mediavideo_media_id"), ["media_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_mediavideo_season"), ["season"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_mediavideo_source"), ["source"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_mediavideo_video_type"), ["video_type"], unique=False
        )

    # The resolver takes the next candidate when one fails, so an attempt
    # records the candidate that it used.
    with op.batch_alter_table("downloadattempt", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_video_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
            )
        )

    # Move the ids that Radarr and Sonarr gave into the table. The column
    # media.youtube_trailer_id stays until the Phase 9 cleanup, but from
    # here the resolver reads only the table, so the ids have to be in it.
    # The enum column keeps the NAME of the member, so the value is 'ARR'.
    result = op.get_bind().execute(
        sa.text(
            "INSERT INTO mediavideo"
            " (media_id, video_id, source, season, video_type, sequence,"
            "  language, name, official, published_at, added_at, updated_at)"
            " SELECT id, youtube_trailer_id, 'ARR', NULL, 'trailer', 0,"
            "        NULL, '', 0, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP"
            " FROM media"
            " WHERE youtube_trailer_id IS NOT NULL"
            "   AND TRIM(youtube_trailer_id) != ''"
        )
    )
    logger.info(
        f"Trailarr moved {result.rowcount} YouTube ids from Radarr and Sonarr"
        " into the video candidates table."
    )

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("downloadattempt", schema=None) as batch_op:
        batch_op.drop_column("last_video_id")

    with op.batch_alter_table("mediavideo", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mediavideo_video_type"))
        batch_op.drop_index(batch_op.f("ix_mediavideo_source"))
        batch_op.drop_index(batch_op.f("ix_mediavideo_season"))
        batch_op.drop_index(batch_op.f("ix_mediavideo_media_id"))
    op.drop_table("mediavideo")

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")
