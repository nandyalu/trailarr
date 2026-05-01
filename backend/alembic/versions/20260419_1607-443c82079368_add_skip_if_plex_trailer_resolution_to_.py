"""add plex connection support

Revision ID: 443c82079368
Revises: b3d2f1a4c8e9
Create Date: 2026-04-19 16:07:40.756092

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "443c82079368"
down_revision: Union[str, None] = "b3d2f1a4c8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    # Add plex columns to media table
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "plex_rating_key",
                sqlmodel.sql.sqltypes.AutoString(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "plex_section_key",
                sqlmodel.sql.sqltypes.AutoString(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("plex_connection_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_media_plex_connection_id_connection"),
            "connection",
            ["plex_connection_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.add_column(
            sa.Column("plex_trailer", sa.Boolean(), nullable=True)
        )

    # Add machine_identifier to connection and update event_type enum
    with op.batch_alter_table("connection", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "machine_identifier",
                sqlmodel.sql.sqltypes.AutoString(),
                nullable=True,
            )
        )

    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.alter_column(
            "event_type",
            existing_type=sa.VARCHAR(length=18),
            type_=sa.Enum(
                "MEDIA_ADDED",
                "MONITOR_CHANGED",
                "YOUTUBE_ID_CHANGED",
                "TRAILER_DETECTED",
                "TRAILER_DOWNLOADED",
                "TRAILER_DELETED",
                "DOWNLOAD_SKIPPED",
                "PLEX_LINKED",
                "PLEX_UNLINKED",
                "PLEX_SCAN_TRIGGERED",
                name="eventtype",
                native_enum=False,
            ),
            existing_nullable=False,
        )

    # Add Plex skip settings to trailerprofile
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "skip_if_plex_trailer",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "skip_if_plex_trailer_resolution",
                sa.Integer(),
                server_default="1080",
                nullable=False,
            )
        )

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("skip_if_plex_trailer_resolution")
        batch_op.drop_column("skip_if_plex_trailer")

    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.alter_column(
            "event_type",
            existing_type=sa.Enum(
                "MEDIA_ADDED",
                "MONITOR_CHANGED",
                "YOUTUBE_ID_CHANGED",
                "TRAILER_DETECTED",
                "TRAILER_DOWNLOADED",
                "TRAILER_DELETED",
                "DOWNLOAD_SKIPPED",
                "PLEX_LINKED",
                "PLEX_UNLINKED",
                "PLEX_SCAN_TRIGGERED",
                name="eventtype",
                native_enum=False,
            ),
            type_=sa.VARCHAR(length=18),
            existing_nullable=False,
        )

    with op.batch_alter_table("connection", schema=None) as batch_op:
        batch_op.drop_column("machine_identifier")

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("plex_trailer")
        batch_op.drop_constraint(
            batch_op.f("fk_media_plex_connection_id_connection"),
            type_="foreignkey",
        )
        batch_op.drop_column("plex_connection_id")
        batch_op.drop_column("plex_section_key")
        batch_op.drop_column("plex_rating_key")

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")
