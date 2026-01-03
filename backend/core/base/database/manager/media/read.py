from datetime import datetime, timedelta, timezone
from typing import Generator
from sqlmodel import Session, col, desc, or_, select, text
from sqlmodel.sql.expression import SelectOfScalar

from . import base
import core.base.database.manager.connection as connection_manager
from core.base.database.models.media import Media, MediaRead, MonitorStatus
from core.base.database.utils.engine import manage_session


@manage_session
def read(
    id: int,
    *,
    _session: Session = None,  # type: ignore
) -> MediaRead:
    """Get a media object from the database by id.\n
    Args:
        id (int): The id of the media object to get.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        MediaRead: The MediaRead object if it exists.
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(id, _session)
    # Convert Media object to MediaRead object to return
    media_read = MediaRead.model_validate(db_media)
    return media_read


@manage_session
def read_all_raw(
    *,
    _session: Session = None,  # type: ignore
) -> list[dict]:
    """Get all media items from the database as raw dictionaries.\n
    Args:
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[dict]: List of all media items as dictionaries.
    """
    query = text("SELECT * FROM media")
    result = _session.execute(query)
    rows = []
    for row in result.mappings():
        item = dict(row)
        rows.append(item)
    return rows


@manage_session
def read_all(
    movies_only: bool | None = None,
    filter_by: str | None = "all",
    sort_by: str | None = None,
    sort_asc: bool = True,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Get all media objects from the database. \n
    Optionally apply filtering and sorting\n
    Args:
        movies_only (bool, Optional): Flag to get only movies. Default is None.\
            If `True`, it will return only movies. \
            If `False`, it will return only series. \
            If `None`, it will return both movies and series.
        filter_by (str, Optional): Filter the media items by a column value. \
            Can be `all`, `downloaded`, `monitored`, `missing`, or `unmonitored`. \
            Default is `all`.
        sort_by (str, Optional): Sort the media items by `title`, `year`, `added_at`, \
            or `updated_at`. Default is None.
        sort_asc (bool, Optional): Flag to sort in ascending order. Default is True.
        _session (Session, Optional): A session to use for the database connection.\
            Default is None, in which case a new session will be created.\n
    Returns:
        list[MediaRead]: List of MediaRead objects.
    """
    statement = select(Media)
    if movies_only is not None:
        statement = statement.where(col(Media.is_movie).is_(movies_only))
    if filter_by:
        statement = _apply_filter(statement, filter_by)
    if sort_by and hasattr(Media, sort_by):
        if sort_asc:
            statement = statement.order_by(sort_by)
        else:
            statement = statement.order_by(desc(sort_by))
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


@manage_session
def read_all_generator(
    movies_only: bool | None = None,
    monitored_only: bool = False,
    *,
    _session: Session = None,  # type: ignore
) -> Generator[MediaRead, None, None]:
    """Generator to get all media objects from the database one by one.\n
    Args:
        movies_only (bool, Optional): Flag to get only movies. Default is None.\
            If `True`, it will return only movies. \
            If `False`, it will return only series. \
            If `None`, it will return both movies and series.
        monitored_only (bool, Optional): Flag to get only monitored media. Default is False.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Yields:
        MediaRead: The next MediaRead object.
    """
    statement = select(Media).execution_options(stream_results=True)
    if movies_only is not None:
        statement = statement.where(col(Media.is_movie).is_(movies_only))
    if monitored_only:
        statement = statement.where(col(Media.monitor).is_(True))
    stream = _session.exec(statement)
    for db_media in stream:
        yield MediaRead.model_validate(db_media)
    return


@manage_session
def read_all_by_connection(
    connection_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Get all media objects from the database for a given connection.\n
    Args:
        connection_id (int): The id of the connection to get media items for.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[MediaRead]: List of MediaRead objects.
    """
    if not connection_manager.exists(connection_id, _session=_session):
        return []
    statement = select(Media).where(Media.connection_id == connection_id)
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


@manage_session
def read_recent(
    limit: int = 100,
    offset: int = 0,
    movies_only: bool | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Get the most recent media objects from the database.\n
    Args:
        limit (int, Optional): The number of recent media items to get. Max 100
        offset (int, Optional): The offset to start from. Default is 0.
        movies_only (bool, Optional): Flag to get only movies. Default is None.\n
            If True, it will return only movies. If False, it will return only series.\n
            If None, it will return all media items.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[MediaRead]: List of MediaRead objects.
    """
    offset = max(0, offset)
    limit = max(1, min(limit, 100))
    statement = select(Media)
    if movies_only is not None:
        statement = statement.where(col(Media.is_movie).is_(movies_only))
    statement = (
        statement.order_by(desc(Media.added_at)).offset(offset).limit(limit)
    )
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


@manage_session
def read_recently_downloaded(
    limit: int = 100,
    offset: int = 0,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Get the most recently downloaded media objects from the database.\n
    Args:
        limit (int, Optional): The number of recent media items to get. Max 100
        offset (int, Optional): The offset to start from. Default is 0.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[MediaRead]: List of MediaRead objects.
    """
    offset = max(0, offset)
    limit = max(1, min(limit, 100))
    statement = (
        select(Media)
        .where(Media.status == MonitorStatus.DOWNLOADED)
        .order_by(desc(Media.downloaded_at))
        .offset(offset)
        .limit(limit)
    )
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


@manage_session
def read_updated_after(
    seconds: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Get all media objects from the database that were updated after a given date.\n
    Args:
        updated_at (datetime): The date to check for updates.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[MediaRead]: List of MediaRead objects.
    """
    seconds = max(1, seconds + 1)  # Add 1 second to avoid missing items
    seconds = min(seconds, 86400)  # Max 1 day
    updated_at = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    statement = select(Media).where(
        or_(
            Media.updated_at > updated_at,
            Media.added_at > updated_at,
            Media.downloaded_at > updated_at,  # type: ignore
        )
    )
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


def _apply_filter(
    statement: SelectOfScalar[Media], filter_by: str
) -> SelectOfScalar[Media]:
    """🚨This is a private method🚨 \n
    Apply a filter to the database query based on the filter_by parameter.\n
    Args:
        statement (SelectOfScalar[Media]): The database query statement.
        filter_by (str): The filter to apply to the statement.\
            Can be `all`, `downloaded`, `monitored`, `missing`, or `unmonitored`.\n
    Returns:
        SelectOfScalar[Media]: The updated statement with the filter applied.
    """
    if filter_by == "downloaded":
        statement = statement.where(col(Media.trailer_exists).is_(True))
        return statement
    if filter_by == "monitored":
        statement = statement.where(col(Media.monitor).is_(True))
        return statement
    if filter_by == "missing":
        statement = statement.where(col(Media.trailer_exists).is_(False))
        return statement
    if filter_by == "unmonitored":
        statement = statement.where(col(Media.monitor).is_(False))
        statement = statement.where(col(Media.trailer_exists).is_(False))
        return statement
    # If filter_by is `all` or doesn't match any of the above,
    # return the statement as is
    return statement
