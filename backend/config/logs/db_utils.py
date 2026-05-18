import os
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import event, text as sa_text
from sqlmodel import Session, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from config.logs.model import LogBase, AppLogRecord  # noqa F401
from config.settings import app_settings

os.makedirs(f"{app_settings.app_data_dir}/logs", exist_ok=True)

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


def _set_logs_pragmas(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA wal_autocheckpoint=200")  # checkpoint after ~800 KB
    cursor.close()


event.listen(engine, "connect", _set_logs_pragmas)
event.listen(async_engine.sync_engine, "connect", _set_logs_pragmas)

LogBase.metadata.create_all(engine)


def flush_logs_to_db():
    """Checkpoint and truncate the WAL back to zero bytes."""
    with engine.connect() as connection:
        connection.execute(sa_text("PRAGMA wal_checkpoint(TRUNCATE);"))
        connection.commit()


def compact_logs_db():
    """VACUUM the logs DB to reclaim space freed by deleted rows.
    Must be called outside any active transaction; runs synchronously.
    """
    with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        conn.execute(sa_text("VACUUM;"))


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
