from datetime import datetime, timezone
from sqlmodel import Session, col, select

from . import base
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.event as event_manager
from core.base.database.models.event import EventSource
from core.base.database.models.media import (
    Media,
    MediaCreate,
    MediaRead,
)
from core.base.database.utils.engine import write_session
from exceptions import ItemNotFoundError


@write_session
def create(
    media_create: MediaCreate,
    *,
    _session: Session = None,  # type: ignore
) -> MediaRead:
    """Create a single new media item in the database.\n
    Args:
        media_create (MediaCreate): The media item to create.
        _session (Session, Optional): A session to use for the database connection.\n
    Returns:
        MediaRead: The created MediaRead object.
    Raises:
        ItemNotFoundError: If the connection_id is invalid.
    """
    if not connection_manager.exists(media_create.connection_id, _session=_session):
        raise ItemNotFoundError("Connection", media_create.connection_id)
    db_media = Media.model_validate(media_create)
    _session.add(db_media)
    _session.commit()
    _session.refresh(db_media)
    return MediaRead.model_validate(db_media)


@write_session
def create_or_update_bulk(
    media_create_list: list[MediaCreate],
    *,
    _session: Session = None,  # type: ignore
) -> list[tuple[MediaRead, bool, bool, bool]]:
    """Create or update multiple media objects in the database at once. \n
    If media already exists, it will be updated, otherwise it will be created.\n
    Args:
        media_create_list (list[MediaCreate]): List of media objects to create or update.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[tuple[MediaRead, bool, bool, bool]]: List of tuples with MediaRead object, \
            created, updated, and arr_linked flags.\n
        Example::\n
            [(<MediaRead obj 1>, True, False), (<MediaRead obj 2>, False, False), ...] \n
    Raises:
        ItemNotFoundError: If any of the connections with provided connection_id's are invalid.
        ValidationError: If any of the media items are invalid.
    """
    _check_connection_exists_bulk(media_create_list, session=_session)
    db_media_list: list[tuple[Media, bool, bool, bool]] = []
    new_count: int = 0
    updated_count: int = 0
    for media_create in media_create_list:
        db_media, created, updated, arr_linked = _create_or_update(media_create, _session)
        db_media_list.append((db_media, created, updated, arr_linked))
        if created:
            new_count += 1
        if updated:
            updated_count += 1
    _session.commit()
    return [
        (MediaRead.model_validate(db_media), created, updated, arr_linked)
        for db_media, created, updated, arr_linked in db_media_list
    ]


def _check_connection_exists_bulk(
    media_items: list[MediaCreate], session: Session
) -> None:
    """🚨This is a private method🚨 \n
    Check if a connection exists in the database for multiple media items.\n
    Args:
        media_items (list[MediaCreate]): List of media items to check.
        session (Session): A session to use for the database connection.\n
    Raises:
        ItemNotFoundError: If any of the connections with provided connection_id's are invalid.
    """
    connection_ids = {media.connection_id for media in media_items}
    for connection_id in connection_ids:
        if not connection_manager.exists(connection_id, _session=session):
            raise ItemNotFoundError("Connection", connection_id)
    return


def _create_or_update(
    media_create: MediaCreate, session: Session
) -> tuple[Media, bool, bool, bool]:
    """🚨This is a private method🚨 \n
    Create or update a media in the database. \n
    If media already exists, it will be updated, otherwise it will be created.\n
    Does not commit the changes to database. Only adds to session.\n
    Args:
        media_create (MediaCreate): The media to create or update.
        _session (Session): A session to use for the database connection.\n
    Returns:
        tuple[Media, bool, bool, bool]: Media object and flags for created, updated,
            and arr_linked (True when a Plex-only row was adopted by this Arr item).\n
        Example::\n
            (<Media obj>, True, False, False)
    """
    db_media = _read_if_exists(
        media_create.connection_id, media_create.txdb_id, session
    )
    arr_linked = False
    if db_media is None:
        # Fallback: adopt a Plex-only row at the same folder path to avoid duplicates.
        plex_row = _read_plex_only_by_folder_path(media_create.folder_path, session)
        if plex_row is not None:
            db_media = plex_row
            arr_linked = True
    if db_media:
        # Exists (or newly adopted Plex-only row), update it.
        # exclude_none=True preserves plex_* fields when adopting a Plex-only row.
        media_update_data = media_create.model_dump(
            exclude_unset=True,
            # exclude_defaults=True,
            exclude_none=True,
            exclude={
                "youtube_trailer_id",
                "downloaded_at",
                "created_at",
                "updated_at",
            },
        )
        db_media.sqlmodel_update(media_update_data)
        _updated = False
        if not db_media.youtube_trailer_id and media_create.youtube_trailer_id:
            event_manager.track_youtube_id_changed(
                media_id=db_media.id,  # type: ignore
                old_yt_id=db_media.youtube_trailer_id,
                new_yt_id=media_create.youtube_trailer_id,
                source=EventSource.SYSTEM,
                source_detail="ConnectionRefresh",
                session=session,
            )
            db_media.youtube_trailer_id = media_create.youtube_trailer_id
            _updated = True
        elif base.has_updated(
            db_media,
            media_create,
            ignore_attrs={
                "monitor",
                "updated_at",
                "downloaded_at",
                "youtube_trailer_id",
                "created_at",
            },
        ):
            db_media.updated_at = datetime.now(timezone.utc)
            _updated = True
        session.add(db_media)
        return db_media, False, _updated, arr_linked
    else:
        # Doesn't exist, Create it
        db_media = Media.model_validate(media_create)
        session.add(db_media)
        # youtube_id tracking for new media is done in connection_manager
        # after media_added event to ensure correct event ordering
        return db_media, True, False, False


def _read_plex_only_by_folder_path(
    folder_path: str | None,
    session: Session,
) -> Media | None:
    """🚨This is a private method🚨 \n
    Find a Plex-only media item (arr_id=0) by folder path within an existing session.

    Two-stage lookup matching read_by_folder_path semantics:
    1. Exact match on folder_path.
    2. Prefix match: stored path is a parent directory of the given path.
    Returns None if folder_path is falsy or no Plex-only item matches.
    """
    if not folder_path:
        return None
    # Stage 1: exact match
    statement = (
        select(Media)
        .where(Media.folder_path == folder_path)
        .where(Media.arr_id == 0)
    )
    db_media = session.exec(statement).first()
    if db_media:
        return db_media
    # Stage 2: prefix match (stored path is a parent of folder_path)
    id_path_stmt = (
        select(Media.id, Media.folder_path)
        .where(col(Media.folder_path).is_not(None))
        .where(Media.arr_id == 0)
    )
    rows = session.exec(id_path_stmt).all()
    best_id: int | None = None
    best_path_len: int = 0
    for row_id, row_path in rows:
        if not row_path or not row_id:
            continue
        if folder_path.startswith(row_path) and len(row_path) > best_path_len:
            best_id = row_id
            best_path_len = len(row_path)
    if best_id is None:
        return None
    return base._get_db_item(best_id, session)


def _read_if_exists(
    connection_id: int,
    txdb_id: str,
    session: Session,
) -> Media | None:
    """🚨This is a private method🚨 \n
    Check if a media item exists in the database for any given connection and arr ids.\n
    Args:
        connection_id (int): The id of the connection to check.
        txdb_id (str): The txdb id of the media item to check.
        session (Session): A session to use for the database connection.\n
    Returns:
        Media | None: The media object if it exists, otherwise None.
    """
    statement = (
        select(Media)
        .where(Media.connection_id == connection_id)
        .where(Media.txdb_id == txdb_id)
    )
    db_media = session.exec(statement).first()
    return db_media
