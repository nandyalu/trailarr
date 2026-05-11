"""Add uploader_ids to trailerprofile

Revision ID: f1a2b3c4d5e6
Revises: e3a59c94c6dc
Create Date: 2026-05-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e3a59c94c6dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("uploader_ids", sa.String(), server_default="", nullable=False)
        )
    logger.info("Added 'uploader_ids' column to trailerprofile table")


def downgrade() -> None:
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("uploader_ids")
