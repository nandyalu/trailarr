"""The engine and the sessions for the log database.

Logs live in their own SQLite file. A slow or locked log write must never
hold up the application database.
"""

from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import event, text as sa_text
from sqlmodel import Session, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from config.logs.model import LogBase, AppLogRecord  # noqa F401
from config.settings import app_settings

logs_db = f"sqlite:///{app_settings.app_data_dir}/logs/logs.db"
logs_async_db = f"sqlite+aiosqlite:///{app_settings.app_data_dir}/logs/logs.db"

engine = create_engine(
    logs_db,
    connect_args={"check_same_thread": False},
    echo=False,
)

async_engine = create_async_engine(
    logs_async_db,
    connect_args={"check_same_thread": False},
    echo=False,
)

# The largest size that SQLite keeps the WAL file at after a checkpoint.
WAL_SIZE_LIMIT = 32 * 1024 * 1024


def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Apply the pragmas to each new connection to the log database.

    The engine sets its own pragmas. The listener in `database/engine.py`
    also applies to this engine, but this module can create its first
    connection before that listener exists.

    Without `journal_size_limit`, the WAL file never gets smaller. It stays
    at the largest size it ever had. VACUUM writes the full database into
    the WAL, so the daily log purge made a WAL as large as logs.db (#687).
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=20000")
    cursor.execute(f"PRAGMA journal_size_limit={WAL_SIZE_LIMIT}")
    cursor.close()


event.listen(engine, "connect", _set_sqlite_pragma)
event.listen(async_engine.sync_engine, "connect", _set_sqlite_pragma)

LogBase.metadata.create_all(engine)


def flush_logs_to_db():
    """Write the WAL into logs.db and empty the WAL file."""
    with engine.connect() as connection:
        connection.execute(sa_text("PRAGMA wal_checkpoint(TRUNCATE);"))
        connection.commit()


async def vacuum_logs_db() -> None:
    """Reclaim disk space from the logs database.

    SQLite keeps deleted pages inside the file, so purging old log rows
    never shrinks logs.db without an explicit VACUUM. VACUUM cannot run
    inside a transaction, so it needs an autocommit connection.

    VACUUM writes the full database into the WAL. The TRUNCATE checkpoint
    then empties the WAL file, so the disk space comes back at once.
    """
    async with async_engine.connect() as connection:
        connection = await connection.execution_options(
            isolation_level="AUTOCOMMIT"
        )
        await connection.execute(sa_text("VACUUM"))
        await connection.execute(sa_text("PRAGMA wal_checkpoint(TRUNCATE)"))


@contextmanager
def get_logs_session():
    """Create a new session for logs database operations."""
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        print(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()


@asynccontextmanager
async def get_async_logs_session():
    """Create a new async session for logs database operations."""
    async with AsyncSession(async_engine) as session:
        try:
            yield session
        except Exception as e:
            print(f"Error occurred: {e}")
            await session.rollback()
        finally:
            await session.close()
