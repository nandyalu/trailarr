from sqlmodel import Session, col, select

from . import base
from core.base.database.models.media import (
    Media,
)
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError
from app_logger import logger


@manage_session
def delete(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Delete a media item from the database by id.\n
    Args:
        media_id (int): The id of the media to delete.
        _session (Session, Optional): A session to use for the database connection.\
            Default is None, in which case a new session will be created.\n
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_id, _session)
    _session.delete(db_media)
    _session.commit()
    return


@manage_session
def delete_bulk(
    media_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Delete multiple media items from the database at once.\n
    Args:
        media_ids (list[int]): List of media id's to delete.
        _session (Session, Optional): A session to use for the database connection.\
            Default is None, in which case a new session will be created.\n
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    for media_id in media_ids:
        try:
            media_db = base._get_db_item(media_id, _session)
            _session.delete(media_db)
        except ItemNotFoundError:
            logger.debug(
                f"Media with id {media_id} doesn't exist in"
                " the database. Skipping!"
            )
    _session.commit()
    return


@manage_session
def delete_except(
    connection_id: int,
    media_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Delete all media items from the database except the ones provided.\n
    Args:
        connection_id (int): The id of the connection to delete media items for.
        media_ids (list[int]): List of media id's to keep.
        _session (Session, Optional): A session to use for the database connection.\
            Default is None, in which case a new session will be created.\n
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    statement = (
        select(Media)
        .where(Media.connection_id == connection_id)
        .where(~col(Media.id).in_(media_ids))
    )
    db_media_list = _session.exec(statement).all()
    for db_media in db_media_list:
        _session.delete(db_media)
    _session.commit()
    return
