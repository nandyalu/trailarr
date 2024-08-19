"""Movie and Series to Media

Revision ID: 34f937f1d7b9
Revises: 325a4fb01c20
Create Date: 2024-08-13 17:09:06.775128

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger
from sqlalchemy.schema import SchemaItem


# revision identifiers, used by Alembic.
revision: str = "34f937f1d7b9"
down_revision: Union[str, None] = "325a4fb01c20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logging = ModuleLogger("AlembicMigrations")


def _check_table_exists(table_name: str) -> bool:
    tables = sa.inspect(op.get_bind()).get_table_names()
    if table_name in tables:
        logging.info(f"{table_name.title()} table already exists")
        return True
    return False


def _create_mapping_table() -> None:
    if _check_table_exists("pathmapping"):
        return
    logging.info("Creating PathMapping Table")
    op.create_table(
        "pathmapping",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("connection_id", sa.Integer(), nullable=True),
        sa.Column("path_from", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("path_to", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["connection.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    return


def _create_media_table(table_name: str, create_is_movie_column: bool) -> None:
    if _check_table_exists(table_name):
        return
    logging.info(f"Creating {table_name} table")
    # Create media table
    _columns: list[SchemaItem] = [
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("arr_id", sa.Integer(), nullable=False),
    ]
    if create_is_movie_column:
        _columns.append(sa.Column("is_movie", sa.Boolean(), nullable=False))

    _columns2: list[SchemaItem] = [
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("overview", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("runtime", sa.Integer(), nullable=False),
        sa.Column(
            "youtube_trailer_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("folder_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("imdb_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("txdb_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("poster_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("fanart_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("poster_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("fanart_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("trailer_exists", sa.Boolean(), nullable=False),
        sa.Column("monitor", sa.Boolean(), nullable=False),
        sa.Column("arr_monitored", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("downloaded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["connection.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    ]
    _columns.extend(_columns2)
    op.create_table(table_name, *_columns)

    # Create indexes
    logging.info(f"Creating indexes for {table_name} table")
    op.create_index(f"ix_{table_name}_year", table_name, ["year"], unique=False)
    op.create_index(f"ix_{table_name}_txdb_id", table_name, ["txdb_id"], unique=False)
    op.create_index(f"ix_{table_name}_title", table_name, ["title"], unique=False)
    op.create_index(f"ix_{table_name}_language", table_name, ["language"], unique=False)
    if create_is_movie_column:
        op.create_index(
            f"ix_{table_name}_is_movie", table_name, ["is_movie"], unique=False
        )
    op.create_index(f"ix_{table_name}_imdb_id", table_name, ["imdb_id"], unique=False)
    op.create_index(
        f"ix_{table_name}_connection_id", table_name, ["connection_id"], unique=False
    )
    op.create_index(f"ix_{table_name}_arr_id", table_name, ["arr_id"], unique=False)

    return


def _create_is_movie_column(table_name: str, create_index: bool) -> None:
    logging.info(f"Adding 'is_movie' column to {table_name} table")
    # Alter table to add is_movie column
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_movie",
                sa.Boolean(),
                server_default=sa.true() if table_name == "movie" else sa.false(),
                nullable=False,
            ),
        )
    # Create index on is_movie column
    if create_index:
        logging.info(f"Creating index for is_movie column in {table_name} table")
        op.create_index(
            f"ix_{table_name}_is_movie", table_name, ["is_movie"], unique=False
        )
    return


def _copy_to_media_table(table_name: str) -> None:
    logging.info(f"Copying data from {table_name} table to media table")
    all_cols = """
        connection_id, arr_id, title, year, language, overview, runtime, youtube_trailer_id, folder_path, imdb_id, txdb_id, poster_url, fanart_url, poster_path, fanart_path, trailer_exists, monitor, arr_monitored, added_at, updated_at, downloaded_at, is_movie
    """  # noqa: E501
    base_statement = """
        INSERT INTO media ({cols})
        SELECT {cols}
        FROM {from_table};
    """
    copy_statement = base_statement.format(cols=all_cols, from_table=table_name)

    # Copy all series data to media table
    op.execute(copy_statement)
    return


def _copy_from_media_table(table_name: str) -> None:
    logging.info(f"Copying data from media table to {table_name} table")
    all_cols = """
        connection_id, arr_id, title, year, language, overview, runtime, youtube_trailer_id, folder_path, imdb_id, txdb_id, poster_url, fanart_url, poster_path, fanart_path, trailer_exists, monitor, arr_monitored, added_at, updated_at, downloaded_at
    """  # noqa: E501
    base_statement = """
        INSERT INTO {to_table} ({cols})
        SELECT {cols}
        FROM media
        WHERE is_movie = {is_movie};
    """
    is_movie = "TRUE" if table_name == "movie" else "FALSE"
    copy_statement = base_statement.format(
        to_table=table_name, cols=all_cols, is_movie=is_movie
    )

    # Copy all series data to media table
    op.execute(copy_statement)
    return


def _drop_table(table_name: str) -> None:
    logging.info(f"Dropping {table_name} table and it's indexes")
    # Get all indexes for the table
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)

    # Drop all indexes for the table
    for index in indexes:
        if not index["name"]:
            continue
        logging.info(f"Dropping index {index['name']} from {table_name} table")
        op.drop_index(index["name"], table_name=table_name)

    # Drop the table
    logging.info(f"Dropping {table_name} table")
    op.drop_table(table_name)
    return


def upgrade() -> None:
    # Adding 'is_movie' column to movie and series tables
    _create_is_movie_column("movie", create_index=False)
    _create_is_movie_column("series", create_index=False)

    # Create media table
    _create_media_table("media", create_is_movie_column=True)

    # Copy data from movie and series tables to media table
    _copy_to_media_table("series")
    _copy_to_media_table("movie")

    # Drop movie and series tables
    _drop_table("series")
    _drop_table("movie")

    # Create PathMapping Table
    _create_mapping_table()
    return


def downgrade() -> None:
    # ### commands auto generated by Alembic - modified to copy movies/series back from media! ###
    # Create movie and series tables
    _create_media_table("movie", create_is_movie_column=False)
    _create_media_table("series", create_is_movie_column=False)

    # Copy data from media table to movie and series tables
    _copy_from_media_table("movie")
    _copy_from_media_table("series")

    # Drop media table and pathmapping table
    _drop_table("media")
    _drop_table("pathmapping")
    # ### end Alembic commands ###
