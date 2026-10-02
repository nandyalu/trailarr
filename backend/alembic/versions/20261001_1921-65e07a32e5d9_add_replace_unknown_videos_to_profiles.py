"""Add Replace Unknown Videos to profiles

Revision ID: 65e07a32e5d9
Revises: 5f47f30bef01
Create Date: 2026-10-01 19:21:06.742986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = '65e07a32e5d9'
down_revision: Union[str, None] = '5f47f30bef01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # Off by default: a trailer whose video is unknown stays, as every
    # profile kept it before this setting existed. Only acts when
    # upgrade_to_tmdb is on.
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "replace_unknown_videos",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("replace_unknown_videos")

    op.execute("PRAGMA foreign_keys=ON")
