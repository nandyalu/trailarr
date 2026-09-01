from datetime import datetime, timedelta, timezone
from typing import Generator
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, desc, or_, select, text
from sqlmodel.sql.expression import SelectOfScalar

from . import base
import core.base.database.manager.connection as connection_manager
from core.base.database.models.download import Download
from core.base.database.models.media import Media, MediaRead
from core.base.database.utils.engine import read_session

_MEDIA_BATCH_SIZE = 500


def _active_download_exists():
    """Correlated EXISTS: the media has at least one active
    (file_exists=True) download row. Phase 3: downloads — not any stored
    flag — are the source of truth for downloaded-ness."""
    return (
        select(Download.id)
        .where(
            col(Download.media_id) == col(Media.id),
            col(Download.file_exists).is_(True),
        )
        .exists()
    )


@read_session
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


@read_session
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


@read_session
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


@read_session
def read_all_generator(
    movies_only: bool | None = None,
    monitored_only: bool = False,
    downloaded_only: bool = False,
    plex_linked_only: bool = False,
    *,
    _session: Session = None,  # type: ignore
) -> Generator[MediaRead, None, None]:
    """Generator to get all media objects from the database one by one.\n
    Args:
        movies_only (bool, Optional=None): Flag to get only movies. \
            If `True`, it will return only movies. \
            If `False`, it will return only series. \
            If `None`, it will return both movies and series.
        monitored_only (bool, Optional=False): Flag to get only monitored media.
        downloaded_only (bool, Optional=False): Flag to get only downloaded media.
        plex_linked_only (bool, Optional=False): Flag to get only media linked to a Plex connection.
        _session (Session, Optional=None): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Yields:
        MediaRead: The next MediaRead object.
    """
    statement = (
        select(Media)
        .options(selectinload(Media.downloads))
        .execution_options(yield_per=_MEDIA_BATCH_SIZE)
    )
    if movies_only is not None:
        statement = statement.where(col(Media.is_movie).is_(movies_only))
    if monitored_only:
        statement = _apply_filter(statement, "monitored")
    if downloaded_only:
        statement = _apply_filter(statement, "downloaded")
    if plex_linked_only:
        statement = statement.where(
            col(Media.plex_connection_id).is_not(None),
            col(Media.plex_rating_key).is_not(None),
        )
    stream = _session.exec(statement)
    try:
        for db_media in stream:
            yield MediaRead.model_validate(db_media)
    finally:
        # @read_session closes the session before the generator body runs;
        # when iterated, the generator re-acquires a connection. Explicitly
        # close here so that connection is returned to the pool whether the
        # generator is exhausted naturally, closed early, or receives an exception.
        _session.close()


@read_session
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


@read_session
def read_arr_linked_to_plex_connection(
    plex_connection_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaRead]:
    """Return Arr-sourced media rows linked to a specific Plex connection.

    These are rows where ``plex_connection_id`` matches but ``connection_id``
    does not — i.e., the media came from Radarr/Sonarr but was linked to Plex
    via folder-path matching. When the Plex connection is deleted the DB sets
    ``plex_connection_id`` to NULL via SET NULL; this function is used *before*
    deletion to fire PLEX_UNLINKED events for each affected row.

    Args:
        plex_connection_id (int): The Plex connection id to look up.
        _session: A session to use for the database connection.

    Returns:
        list[MediaRead]: Arr-sourced media rows linked to this Plex connection.
    """
    statement = select(Media).where(
        (Media.plex_connection_id == plex_connection_id)
        & (Media.connection_id != plex_connection_id)
    )
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


@read_session
def read_by_folder_path(
    folder_path: str,
    *,
    _session: Session = None,  # type: ignore
) -> MediaRead | None:
    """Find a media item by folder path, with fallback to prefix matching.

    Two-stage lookup:
    1. Exact match on folder_path (covers movies and single-folder media).
    2. Prefix match: find the stored folder_path that is a parent directory
       of the given path (covers TV shows where Plex gives a season subfolder
       but Sonarr stores the series root folder).

    Args:
        folder_path (str): The folder path to look up (Plex-mapped path).
        _session (Session, Optional): A session to use for the database connection.
    Returns:
        MediaRead | None: The MediaRead object if found, otherwise None.
    """
    if not folder_path:
        return None
    # Stage 1: exact match
    statement = select(Media).where(Media.folder_path == folder_path)
    db_media = _session.exec(statement).first()
    if db_media:
        return MediaRead.model_validate(db_media)

    # Stage 2: prefix match — stored folder_path is a parent of the given path.
    # Fetch only id + folder_path to avoid loading full rows, filter in Python,
    # then fetch the single winning row by id.
    id_path_stmt = select(Media.id, Media.folder_path).where(
        col(Media.folder_path).is_not(None)
    )
    rows = _session.exec(id_path_stmt).all()

    best_id: int | None = None
    best_norm: str = ""
    for row_id, row_path in rows:
        if not row_path or not row_id:
            continue
        norm = row_path.rstrip("/\\")
        if (
            folder_path.startswith(norm + "/")
            or folder_path.startswith(norm + "\\")
        ) and len(norm) > len(best_norm):
            best_id = row_id
            best_norm = norm
    if best_id is None:
        return None
    # Never match a row whose folder is a library root (bad data from old
    # versions). Such a row is a parent of every media folder in that
    # library, so it would incorrectly match all of them. A legitimate
    # parent row is always deeper than the root, so it always wins the
    # longest-match rule over a root row when both are present.
    if base._is_at_or_above_library_root(
        best_norm, base._library_root_paths(_session)
    ):
        return None
    return MediaRead.model_validate(base._get_db_item(best_id, _session))


@read_session
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


@read_session
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
    # Phase 3: downloaded-ness and recency come from download rows, never
    # from the stored status/downloaded_at columns.
    statement = (
        select(Media)
        .join(Download)
        .where(col(Download.file_exists).is_(True))
        .group_by(col(Media.id))
        .order_by(desc(func.max(col(Download.added_at))))
        .offset(offset)
        .limit(limit)
    )
    db_media_list = _session.exec(statement).all()
    return base._convert_to_read_list(db_media_list)


@read_session
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
    # Phase 3: downloaded/missing/unmonitored are decided by download rows
    # (EXISTS subquery), never by a stored mirror column.
    if filter_by == "downloaded":
        statement = statement.where(_active_download_exists())
        return statement
    if filter_by == "monitored":
        statement = statement.where(col(Media.monitor).is_(True))
        return statement
    if filter_by == "missing":
        statement = statement.where(~_active_download_exists())
        return statement
    if filter_by == "unmonitored":
        statement = statement.where(col(Media.monitor).is_(False))
        statement = statement.where(~_active_download_exists())
        return statement
    # If filter_by is `all` or doesn't match any of the above,
    # return the statement as is
    return statement
