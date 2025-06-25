"""Add season_count to Media

Revision ID: f030a0fdc9d8
Revises: 6265228864f0
Create Date: 2025-06-25 02:05:55.825423

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger

# revision identifiers, used by Alembic.
revision: str = "f030a0fdc9d8"
down_revision: Union[str, None] = "6265228864f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logging = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    logging.info("Adding 'season_count' to media table")
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "season_count",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )


def downgrade() -> None:
    logging.info("Removing 'season_count' from media table")
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("season_count")
