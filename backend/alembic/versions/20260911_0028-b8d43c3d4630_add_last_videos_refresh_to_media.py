"""Add last videos refresh to media

Revision ID: b8d43c3d4630
Revises: a1c139ad7cd2
Create Date: 2026-09-11 00:28:28.946103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = 'b8d43c3d4630'
down_revision: Union[str, None] = 'a1c139ad7cd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # NULL means Trailarr never asked TMDB about this item, so the next
    # run asks. Every existing item starts that way.
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_videos_refresh", sa.DateTime(), nullable=True)
        )

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("last_videos_refresh")

    op.execute("PRAGMA foreign_keys=ON")
