from contextlib import contextmanager
from sqlalchemy import text as sa_text
from sqlmodel import Session, create_engine

from config.logs.model import LogBase, AppLogRecord  # noqa F401
from config.settings import app_settings

logs_db = f"sqlite:///{app_settings.app_data_dir}/logs/logs.db"
engine = create_engine(
    logs_db,
    connect_args={"check_same_thread": False},
    echo=False,
)

LogBase.metadata.create_all(engine)


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
