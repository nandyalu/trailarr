"""Add profile language for TMDB trailers

Revision ID: a1c139ad7cd2
Revises: 1c9c26339940
Create Date: 2026-09-11 00:10:54.420901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = 'a1c139ad7cd2'
down_revision: Union[str, None] = '1c9c26339940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    # Empty means any language, and every existing profile gets it: that
    # is what they did before the field existed. A language here is a
    # filter, so defaulting to English would quietly stop a profile from
    # downloading the trailers it downloads today.
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "language",
                sa.String(),
                server_default="",
                nullable=False,
            )
        )

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("language")

    op.execute("PRAGMA foreign_keys=ON")
