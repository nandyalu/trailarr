from contextlib import contextmanager
from functools import wraps
from sqlite3 import OperationalError as SQLiteOperationalError
import threading
from sqlalchemy.exc import OperationalError as SAOperationalError
import time
from typing import Any, Generator
from sqlalchemy import Engine, event, StaticPool, text as sa_text
from sqlmodel import SQLModel, Session, create_engine

from app_logger import ModuleLogger
from config.settings import app_settings

logger = ModuleLogger("database_engine")
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
            "check_same_thread": False,
            "timeout": 30,  # High timeout at the driver level
        },  # Allow multi-threaded access
        echo=False,
        pool_size=30,
        max_overflow=20,
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
    cursor.execute("PRAGMA busy_timeout=20000")  # 20 seconds
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
    Example:
        ```python
        with get_session() as session:
            movie_1 = Movie(title=..., year=..., ...)
            session.add(movie_1)
            session.commit()
        ```
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# TODO: Once all code is migrated to use the read/write decorators, we can remove the manage_session decorator and its logic.
def manage_session(func):
    """Decorator to manage the session for a function. \n
    Add '_session' to the function's keyword arguments, \n
    decorator will supply a new session if one is not provided. \n
    Also handles database lock errors by retrying the function (5 times). \n
    Args:
        func: The function to decorate
    Returns:
        The decorated function with a session keyword argument
    Example:
        1. Within a class method
        ```python
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
        ```
        2. Outside a class method
        ```python
        @manage_session
        def read(movie_id: int, *, _session: Session = None) -> MovieRead:
            movie = _session.get(Movie, movie_id)
            # do something else with _session or commit the changes
            return movie
        ```
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
            except (SAOperationalError, SQLiteOperationalError) as e:
                if "database is locked" in str(e).lower():
                    # If this was the last attempt, raise the final exception
                    if i == retries - 1:
                        raise Exception(
                            f"Database locked after {retries} retries: {e}"
                        )
                    # Wait and retry
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    # If it's a different Exception, raise it immediately
                    raise
        # If we exit the loop without returning, raise an exception
        raise Exception("Database is locked, retries exhausted.")

    return wrapper


# Lock for write operations - only acquired when creating a new write session
db_write_lock = threading.Lock()


def _session_handler(func, *args, is_blocking: bool = False, **kwargs):
    """
    Internal logic used by both decorators.
    Maintains your existing retry logic as a safety net.

    Args:
        func: The function to call
        *args: Positional arguments for the function
        is_blocking: If True, acquire the write lock when creating a new session
        **kwargs: Keyword arguments for the function (including _session)
    """
    retries = 5
    delay = 0.1
    for i in range(retries):
        try:
            # Check if a '_session' keyword argument was provided
            if kwargs.get("_session") is None:
                # If not, create a new session and add it to kwargs
                # Only acquire write lock if this is a write operation creating a new session
                if is_blocking:
                    with db_write_lock:
                        with get_session() as _session:
                            kwargs["_session"] = _session
                            return func(*args, **kwargs)
                else:
                    with get_session() as _session:
                        kwargs["_session"] = _session
                        return func(*args, **kwargs)
            else:
                # If a session was provided, just call the function
                # No lock needed - the caller already holds it
                return func(*args, **kwargs)
        except (SAOperationalError, SQLiteOperationalError) as e:
            if "database is locked" in str(e).lower():
                # If this was the last attempt, raise the final exception
                if i == retries - 1:
                    raise Exception(
                        f"Database locked after {retries} retries: {e}"
                    )
                # Wait and retry
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                # If it's a different Exception, raise it immediately
                raise
    # If we exit the loop without returning, raise an exception
    raise Exception("Database is locked, retries exhausted.")


def read_session(func):
    """Decorator for managing a read-only session for a function. \n
    **Note: Use for GET/Select operations. Where no locking is required.** \n
    Add '_session' to the function's keyword arguments, \n
    decorator will supply a new session if one is not provided. \n
    Also handles database lock errors by retrying the function (5 times). \n
    Args:
        func: The function to decorate
    Returns:
        The decorated function with a session keyword argument
    Example:
        1. Within a class method
        ```python
        class MovieDatabaseHandler:
            @read_session
            def read(
                self,
                movie_id: int,
                *,
                _session: Session = None,  # type: ignore
            ) -> MovieRead:
                movie = _session.get(Movie, movie_id)
                # do something else with _session or commit the changes
                return movie
        ```
        2. Outside a class method
        ```python
        @read_session
        def read(movie_id: int, *, _session: Session = None) -> MovieRead:
            movie = _session.get(Movie, movie_id)
            # do something else with _session or commit the changes
            return movie
        ```
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return _session_handler(func, *args, **kwargs)

    return wrapper


def write_session(func):
    """Decorator for managing a write session for a function. \n
    **Note: Use for Create/Update/Delete operations. Where locking is required.** \n
    Add '_session' to the function's keyword arguments, \n
    decorator will supply a new session if one is not provided. \n
    Also handles database lock errors by retrying the function (5 times). \n
    Args:
        func: The function to decorate
    Returns:
        The decorated function with a session keyword argument
    Example:
        1. Within a class method
        ```python
        class MovieDatabaseHandler:
            @write_session
            def write(
                self,
                movie_id: int,
                *,
                _session: Session = None,  # type: ignore
            ) -> MovieRead:
                movie = _session.get(Movie, movie_id)
                # do something else with _session or commit the changes
                return movie
        ```
        2. Outside a class method
        ```python
        @write_session
        def write(movie_id: int, *, _session: Session = None) -> MovieRead:
            movie = _session.get(Movie, movie_id)
            # do something else with _session or commit the changes
            return movie
        ```
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return _session_handler(func, *args, is_blocking=True, **kwargs)

    return wrapper
