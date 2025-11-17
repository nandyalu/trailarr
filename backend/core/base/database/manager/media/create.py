from datetime import datetime, timezone
from sqlmodel import Session, select

import core.base.database.manager.connection as connection_manager
from core.base.database.models.media import (
    Media,
    MediaCreate,
    MediaRead,
)
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError


@manage_session
def create_or_update_bulk(
    media_create_list: list[MediaCreate],
    *,
    _session: Session = None,  # type: ignore
) -> list[tuple[MediaRead, bool, bool]]:
    """Create or update multiple media objects in the database at once. \n
    If media already exists, it will be updated, otherwise it will be created.\n
    Args:
        media_create_list (list[MediaCreate]): List of media objects to create or update.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[tuple[MediaRead, bool, bool]]: List of tuples with MediaRead object, \
            created and updated flags.\n
        Example::\n
            [(<MediaRead obj 1>, True, False), (<MediaRead obj 2>, False, False), ...] \n
    Raises:
        ItemNotFoundError: If any of the connections with provided connection_id's are invalid.
        ValidationError: If any of the media items are invalid.
    """
    _check_connection_exists_bulk(media_create_list, session=_session)
    db_media_list: list[tuple[Media, bool, bool]] = []
    new_count: int = 0
    updated_count: int = 0
    for media_create in media_create_list:
        db_media, created, updated = _create_or_update(media_create, _session)
        db_media_list.append((db_media, created, updated))
        if created:
            new_count += 1
        if updated:
            updated_count += 1
    _session.commit()
    return [
        (MediaRead.model_validate(db_media), created, updated)
        for db_media, created, updated in db_media_list
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
) -> tuple[Media, bool, bool]:
    """🚨This is a private method🚨 \n
    Create or update a media in the database. \n
    If media already exists, it will be updated, otherwise it will be created.\n
    Does not commit the changes to database. Only adds to session.\n
    Args:
        media_create (MediaCreate): The media to create or update.
        _session (Session): A session to use for the database connection.\n
    Returns:
        tuple[Media, bool, bool]: Media object and flags indicating created and updated.\n
        Example::\n
            (<Media obj>, True)
    """
    db_media = _read_if_exists(
        media_create.connection_id, media_create.txdb_id, session
    )
    if db_media:
        # Exists, update it
        media_update_data = media_create.model_dump(
            exclude_unset=True,
            # exclude_defaults=True,
            exclude_none=True,
            exclude={"youtube_trailer_id", "downloaded_at"},
        )
        db_media.sqlmodel_update(media_update_data)
        _updated = False
        if _has_updated(db_media, media_create):
            db_media.updated_at = datetime.now(timezone.utc)
            _updated = True
        session.add(db_media)
        return db_media, False, _updated
    else:
        # Doesn't exist, Create it
        db_media = Media.model_validate(media_create)
        session.add(db_media)
        return db_media, True, False


def _has_updated(
    db_media: Media,
    media_update: MediaCreate,
) -> bool:
    """🚨This is a private method🚨 \n
    Check if certain fields in the media update differ from the existing media object.\n
    Field that will be compared:
        - title
        - year
        - media_exists
        - media_filename
        - folder_path
        - arr_monitored
    Args:
        db_media (Media): The existing media object from the database.
        media_update (MediaCreate): The media update object to compare.\n
    Returns:
        bool: True if any fields have changed, False otherwise.
    """
    if db_media.title != media_update.title:
        return True
    if db_media.year != media_update.year:
        return True
    if db_media.media_exists != media_update.media_exists:
        return True
    if db_media.media_filename != media_update.media_filename:
        return True
    if db_media.folder_path != media_update.folder_path:
        return True
    if db_media.arr_monitored != media_update.arr_monitored:
        return True
    return False


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
