from contextlib import contextmanager
from functools import wraps
from sqlite3 import OperationalError
import time
from typing import Any, Generator
from sqlalchemy import Engine, event, StaticPool, text as sa_text
from sqlmodel import SQLModel, Session, create_engine

from config.settings import app_settings

# sqlite_file_name = "database.db"
sqlite_url = app_settings.database_url
if app_settings.testing:
    # Use an in-memory SQLite database for testing
    sqlite_url = "sqlite:///:memory:"
    engine = create_engine(
        sqlite_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
else:
    engine = create_engine(
        sqlite_url,
        connect_args={
            "check_same_thread": False
        },  # Allow multi-threaded access
        echo=False,
    )  # pragma: no cover
# * Not needed, Alembic will create the database tables
# SQLModel.metadata.create_all(engine)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Apply PRAGMA statements when a new connection is established.
    This will work for existing databases and new ones.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Add busy_timeout for robustness if not already included
    cursor.execute("PRAGMA busy_timeout=5000")  # 5 seconds
    cursor.close()


def flush_records_to_db():
    """Flush in-memory records to the database."""
    with engine.connect() as connection:
        connection.execute(sa_text("PRAGMA wal_checkpoint(FULL);"))
        connection.commit()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a SQLModel session to the context manager

    Yields:
        Session: A SQLModel session

    Example::

        with get_session() as session:
            movie_1 = Movie(title=..., year=..., ...)
            session.add(movie_1)
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def manage_session(func):
    """Decorator to manage the session for a function. \n
    Add '_session' to the function's keyword arguments, \n
    decorator will supply a new session if one is not provided. \n
    Also handles database lock errors by retrying the function (5 times). \n
    Args:
        func: The function to decorate

    Returns:
        The decorated function with a session keyword argument

    Example::

        Within a class method
        class MovieDatabaseHandler:
            @manage_session
            def read(
                self,
                movie_id: int,
                *,
                _session: Session = None,  # type: ignore
            ) -> MovieRead:
                movie = _session.get(Movie, movie_id)
                # do something else with _session or commit the changes
                return movie

        Outside a class method
        @manage_session
        def read(movie_id: int, *, _session: Session = None) -> MovieRead:
            movie = _session.get(Movie, movie_id)
            # do something else with _session or commit the changes
            return movie
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        retries = 5
        delay = 0.1
        for i in range(retries):
            try:
                # Check if a '_session' keyword argument was provided
                if kwargs.get("_session") is None:
                    # If not, create a new session and add it to kwargs
                    with get_session() as _session:
                        kwargs["_session"] = _session
                        return func(*args, **kwargs)
                else:
                    # If a session was provided, just call the function
                    return func(*args, **kwargs)
            except OperationalError as e:
                if "database is locked" in str(e):
                    time.sleep(delay)
                    delay *= 2  # Double the delay for each retry
                else:
                    raise
        raise Exception("Database is locked, retries exhausted.")

    return wrapper
