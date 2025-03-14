"""Extra options in Media

Revision ID: 4b942197af6a
Revises: 1cc1dd5dbe9f
Create Date: 2025-02-09 01:42:17.928790

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "4b942197af6a"
down_revision: Union[str, None] = "1cc1dd5dbe9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logging = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    logging.info("Adding extra options in Media")
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "clean_title",
                sqlmodel.sql.sqltypes.AutoString(),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "studio",
                sqlmodel.sql.sqltypes.AutoString(),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "media_exists",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "media_filename",
                sqlmodel.sql.sqltypes.AutoString(),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "title_slug",
                sqlmodel.sql.sqltypes.AutoString(),
                server_default="",
                nullable=False,
            )
        )
        batch_op.create_index(
            batch_op.f("ix_media_clean_title"), ["clean_title"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_media_title_slug"), ["title_slug"], unique=False
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    logging.info("Dropping extra options in Media")
    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_media_title_slug"))
        batch_op.drop_index(batch_op.f("ix_media_clean_title"))
        batch_op.drop_column("title_slug")
        batch_op.drop_column("media_filename")
        batch_op.drop_column("media_exists")
        batch_op.drop_column("studio")
        batch_op.drop_column("clean_title")

    # ### end Alembic commands ###
