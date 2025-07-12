# from logging.config import fileConfig

import logging
from sqlalchemy import Connection, engine_from_config, pool, text as sa_text
from sqlmodel import SQLModel

from alembic import context

import core.base.database.utils.init_db  # noqa: F401
from config.settings import app_settings
import app_logger  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)
#  ## Removed default logging configuration and import app_logger instead

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_main_option("sqlalchemy.url", app_settings.database_url)


EXCLUDE_TABLES = [
    "applogrecord",
]


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


def set_sqlite_pragmas(connection: Connection) -> None:
    # Enable foreign keys for schema comparison and enforcement
    connection.execute(sa_text("PRAGMA foreign_keys = OFF;"))
    # Set WAL mode for better concurrency and resilience
    connection.execute(sa_text("PRAGMA journal_mode = DELETE;"))
    # Set synchronous mode (NORMAL is often a good balance)
    # connection.execute(sa_text("PRAGMA synchronous = NORMAL;"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    logging.info("Running migrations in offline mode")
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_as_batch=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    logging.info("Running migrations in online mode")
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # set_sqlite_pragmas(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_server_default=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


try:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
except Exception as e:
    logging.error(f"Migration failed: {e}")
    raise
