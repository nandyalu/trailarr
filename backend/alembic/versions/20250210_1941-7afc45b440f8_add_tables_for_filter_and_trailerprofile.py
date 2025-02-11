"""Add tables for 'Filter' and 'TrailerProfile'

Revision ID: 7afc45b440f8
Revises: 4b942197af6a
Create Date: 2025-02-10 19:41:31.821760

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger


# revision identifiers, used by Alembic.
revision: str = "7afc45b440f8"
down_revision: Union[str, None] = "4b942197af6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logging = ModuleLogger("AlembicMigrations")


def _check_table_exists(table_name: str) -> bool:
    tables = sa.inspect(op.get_bind()).get_table_names()
    if table_name in tables:
        logging.info(f"{table_name.title()} table already exists")
        return True
    return False


def _create_trailerprofile_table() -> None:
    if _check_table_exists("trailerprofile"):
        return
    logging.info("Creating TrailerProfile Table")
    op.create_table(
        "trailerprofile",
        sa.Column("file_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("folder_enabled", sa.Boolean(), nullable=False),
        sa.Column("folder_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_volume_level", sa.Integer(), nullable=False),
        sa.Column("video_resolution", sa.Integer(), nullable=False),
        sa.Column("video_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("subtitles_enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "subtitles_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "subtitles_language", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("embed_metadata", sa.Boolean(), nullable=False),
        sa.Column("exclude_words", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("include_words", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("min_duration", sa.Integer(), nullable=False),
        sa.Column("max_duration", sa.Integer(), nullable=False),
        sa.Column("remove_silence", sa.Boolean(), nullable=False),
        sa.Column("search_query", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("viewfilter_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    return


def _create_viewfilter_table() -> None:
    if _check_table_exists("viewfilter"):
        return
    logging.info("Creating ViewFilter Table")
    op.create_table(
        "viewfilter",
        sa.Column("view_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    return


def _create_filter_table() -> None:
    if _check_table_exists("filter"):
        return
    logging.info("Creating Filter Table")
    op.create_table(
        "filter",
        sa.Column("filter_by", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "filter_condition",
            sa.Enum(
                "EQUAL",
                "NOT_EQUAL",
                "GREATER_THAN",
                "GREATER_THAN_EQUAL",
                "LESS_THAN",
                "LESS_THAN_EQUAL",
                "IN",
                "NOT_IN",
                "IS_NULL",
                "IS_NOT_NULL",
                "STARTSWITH",
                "ENDSWITH",
                "CONTAINS",
                "NOT_CONTAINS",
                name="filtercondition",
            ),
            nullable=False,
        ),
        sa.Column("filter_value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("viewfilter_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["viewfilter_id"],
            ["viewfilter.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    return


def _drop_table(table_name: str) -> None:
    if not _check_table_exists(table_name):
        logging.info(f"{table_name.title()} table does not exist")
        return
    logging.info(f"Dropping {table_name} table and it's indexes")
    # Get all indexes for the table
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)

    # Drop all indexes for the table
    for index in indexes:
        if index["name"]:
            logging.info(f"Dropping index {index['name']} from {table_name} table")
            op.drop_index(index["name"], table_name=table_name)

    # Drop foreign key constraints if any
    foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys(table_name)
    for fk in foreign_keys:
        if fk["name"]:
            logging.info(
                f"Dropping foreign key constraint {fk['name']} from {table_name} table"
            )
            op.drop_constraint(fk["name"], table_name, type_="foreignkey")

    # Drop the table
    logging.info(f"Dropping {table_name} table")
    op.drop_table(table_name)
    return


def upgrade() -> None:

    # ### commands auto generated by Alembic - please adjust! ###
    _create_trailerprofile_table()
    _create_viewfilter_table()
    _create_filter_table()
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    _drop_table("filter")
    _drop_table("viewfilter")
    _drop_table("trailerprofile")
    # ### end Alembic commands ###
