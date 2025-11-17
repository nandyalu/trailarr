from typing import Sequence
from sqlmodel import Session

from core.base.database.models.media import (
    Media,
    MediaRead,
)
from exceptions import ItemNotFoundError


def _convert_to_read_list(db_media_list: Sequence[Media]) -> list[MediaRead]:
    """🚨This is a private method🚨 \n
    Convert a list of Media objects to a list of MediaRead objects.\n"""
    if not db_media_list or len(db_media_list) == 0:
        return []
    media_read_list: list[MediaRead] = []
    for db_media in db_media_list:
        media_read = MediaRead.model_validate(db_media)
        media_read_list.append(media_read)
    return media_read_list


def _get_db_item(media_id: int, session: Session) -> Media:
    """🚨This is a private method🚨 \n
    Get a media item from the database by id.\n
    Args:
        media_id (int): The id of the media item to get.
        session (Session): A session to use for the database connection.\n
    Returns:
        Media: The media object if it exists.
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = session.get(Media, media_id)
    if not db_media:
        raise ItemNotFoundError("Media", media_id)
    return db_media
