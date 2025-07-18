from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import text as sa_text
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

# LogBase.metadata.create_all(engine)


def flush_logs_to_db():
    """Flush in-memory logs to the database."""
    with engine.connect() as connection:
        connection.execute(sa_text("PRAGMA wal_checkpoint(FULL);"))
        connection.commit()


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
