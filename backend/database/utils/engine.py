from contextlib import contextmanager
from functools import wraps
from typing import Any, Generator
from sqlalchemy import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from backend.config.config import config

sqlite_file_name = "database.db"
sqlite_url = config.DATABASE_URL
if config.DEBUG:
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
    # TODO: Change the echo to False when in production
    engine = create_engine(sqlite_url, echo=True)  # pragma: no cover


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
    Add '_session' to the function's keyword arguments,
    decorator will supply a new session if one is not provided.

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
        # Check if a '_session' keyword argument was provided
        if kwargs.get("_session") is None:
            # If not, create a new session and add it to kwargs
            with get_session() as _session:
                kwargs["_session"] = _session
                return func(*args, **kwargs)
        else:
            # If a session was provided, just call the function
            return func(*args, **kwargs)

    return wrapper
