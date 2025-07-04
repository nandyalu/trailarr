"""Add Yt-dlp Extra Options

Revision ID: 6265228864f0
Revises: 8c9a39658afa
Create Date: 2025-06-16 19:08:24.507315

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger

# revision identifiers, used by Alembic.
revision: str = "6265228864f0"
down_revision: Union[str, None] = "8c9a39658afa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logging = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "ytdlp_extra_options",
                sqlmodel.sql.sqltypes.AutoString(),
                server_default="",
                nullable=False,
            )
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("ytdlp_extra_options")

    # ### end Alembic commands ###
