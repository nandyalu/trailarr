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
from utils.sqlite_wal import (
    STOP_BUSY_TIMEOUT_MS,
    truncate_wal,
    truncate_wal_async,
)

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


def flush_logs_to_db() -> bool:
    """Write the WAL into logs.db and empty the WAL file.

    This runs at the start and the stop of the app. Each connection waits
    20 seconds for a busy database, and Docker stops the container after
    10, so the checkpoint gets a short timeout of its own.

    Returns:
        bool: False when another connection kept the WAL busy, so it was
            not emptied. `journal_size_limit` still caps its size.
    """
    with engine.connect() as connection:
        done = truncate_wal(connection, busy_timeout_ms=STOP_BUSY_TIMEOUT_MS)
        connection.commit()
    return done


async def truncate_logs_wal(attempts: int = 3) -> bool:
    """Empty the WAL file of logs.db after a purge.

    A purge writes the pages it frees into the WAL, and the WAL file keeps
    that size until a checkpoint empties it (#687). New log lines arrive
    all the time, so the checkpoint can find the WAL busy. It tries a few
    times.

    Returns:
        bool: True when the WAL is empty.
    """
    async with async_engine.connect() as connection:
        connection = await connection.execution_options(
            isolation_level="AUTOCOMMIT"
        )
        return await truncate_wal_async(connection, attempts=attempts)


# VACUUM rewrites the full file. Run it only when this part of the file is free.
VACUUM_MIN_FREE_RATIO = 0.25


async def logs_db_free_ratio() -> float:
    """Return the part of logs.db that is free pages, from 0.0 to 1.0.

    The daily purge deletes about one day of logs in thirty. SQLite uses
    those free pages again for new logs, so the file does not grow. A
    VACUUM for so little free space rewrites the full file for almost no
    gain.
    """
    async with async_engine.connect() as connection:
        free = await connection.execute(sa_text("PRAGMA freelist_count"))
        total = await connection.execute(sa_text("PRAGMA page_count"))
        free_pages = free.scalar() or 0
        total_pages = total.scalar() or 0
    return free_pages / total_pages if total_pages else 0.0


async def vacuum_logs_db() -> bool:
    """Reclaim disk space from the logs database.

    SQLite keeps deleted pages inside the file, so purging old log rows
    never shrinks logs.db without an explicit VACUUM. VACUUM cannot run
    inside a transaction, so it needs an autocommit connection.

    VACUUM writes the full database into the WAL. The TRUNCATE checkpoint
    then empties the WAL file, so the disk space comes back at once. New
    log lines arrive all the time, so the checkpoint can find the WAL busy.
    It tries a few times.

    Returns:
        bool: True when the WAL is empty after the VACUUM.
    """
    async with async_engine.connect() as connection:
        connection = await connection.execution_options(
            isolation_level="AUTOCOMMIT"
        )
        await connection.execute(sa_text("VACUUM"))
        return await truncate_wal_async(connection, attempts=5)


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
