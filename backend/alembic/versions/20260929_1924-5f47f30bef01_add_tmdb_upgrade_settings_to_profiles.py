"""Add TMDB upgrade settings to profiles

Revision ID: 5f47f30bef01
Revises: b8d43c3d4630
Create Date: 2026-09-29 19:24:27.819432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = '5f47f30bef01'
down_revision: Union[str, None] = 'b8d43c3d4630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # Both default to what every profile did before: no upgrade. The
    # delete setting only acts when the upgrade setting is on.
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "upgrade_to_tmdb",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "delete_replaced_trailer",
                sa.Boolean(),
                server_default="1",
                nullable=False,
            )
        )

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("delete_replaced_trailer")
        batch_op.drop_column("upgrade_to_tmdb")

    op.execute("PRAGMA foreign_keys=ON")
