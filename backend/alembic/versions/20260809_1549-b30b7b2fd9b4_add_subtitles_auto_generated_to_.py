"""Add subtitles_auto_generated to trailerprofile

Revision ID: b30b7b2fd9b4
Revises: 011109b10e82
Create Date: 2026-08-09 15:49:45.842370

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "b30b7b2fd9b4"
down_revision: Union[str, None] = "011109b10e82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    # Existing profiles keep uploader subtitles only (auto subs off).
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "subtitles_auto_generated",
                sa.Boolean(),
                server_default="0",
                nullable=False,
            )
        )

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("subtitles_auto_generated")

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")
