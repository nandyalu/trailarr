from sqlmodel import Session, select
from core.base.database.manager.customfilter.base import convert_to_read_list
from core.base.database.models.customfilter import (
    CustomFilter,
    CustomFilterRead,
    FilterType,
)
from core.base.database.utils.engine import manage_session


@manage_session
def get_home_customfilters(
    *,
    _session: Session = None,  # type: ignore
) -> list[CustomFilterRead]:
    """
    Get all home view filters.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[CustomFilterRead]: List of home view filters (read-only).
    """
    statement = select(CustomFilter).where(
        CustomFilter.filter_type == FilterType.HOME
    )
    db_customfilters = _session.exec(statement).all()
    return convert_to_read_list(db_customfilters)


@manage_session
def get_movie_customfilters(
    *,
    _session: Session = None,  # type: ignore
) -> list[CustomFilterRead]:
    """
    Get all movie view filters.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[CustomFilterRead]: List of movie view filters (read-only).
    """
    statement = select(CustomFilter).where(
        CustomFilter.filter_type == FilterType.MOVIES
    )
    db_customfilters = _session.exec(statement).all()
    return convert_to_read_list(db_customfilters)


@manage_session
def get_series_customfilters(
    *,
    _session: Session = None,  # type: ignore
) -> list[CustomFilterRead]:
    """
    Get all series view filters.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[CustomFilterRead]: List of series view filters (read-only).
    """
    statement = select(CustomFilter).where(
        CustomFilter.filter_type == FilterType.SERIES
    )
    db_customfilters = _session.exec(statement).all()
    return convert_to_read_list(db_customfilters)
