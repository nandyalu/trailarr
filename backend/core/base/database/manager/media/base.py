from typing import Sequence
from sqlmodel import Session, select

from core.base.database.manager.connection import ConnectionDatabaseManager
from core.base.database.models.media import (
    Media,
    MediaCreate,
    MediaRead,
)
from exceptions import ItemNotFoundError


class BaseMediaManager:
    """🚨This is a private class🚨 \n
    Base Database manager for internal CRUD operations on Media objects.\n
    """

    __model_name = "Media"

    def _check_connection_exists(self, connection_id: int, session: Session) -> None:
        """🚨This is a private method🚨 \n
        Check if a connection exists in the database.\n
        Args:
            connection_id (int): The id of the connection to check.
            session (Session): A session to use for the database connection.\n
        Raises:
            ItemNotFoundError: If the connection with provided connection_id is invalid.
        """
        if not ConnectionDatabaseManager().check_if_exists(
            connection_id, _session=session
        ):
            raise ItemNotFoundError("Connection", connection_id)
        return

    def _check_connection_exists_bulk(
        self, media_items: list[MediaCreate], session: Session
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
            self._check_connection_exists(connection_id, session=session)
        return

    def _convert_to_read_list(self, db_media_list: Sequence[Media]) -> list[MediaRead]:
        """🚨This is a private method🚨 \n
        Convert a list of Media objects to a list of MediaRead objects.\n"""
        if not db_media_list or len(db_media_list) == 0:
            return []
        media_read_list: list[MediaRead] = []
        for db_media in db_media_list:
            media_read = MediaRead.model_validate(db_media)
            media_read_list.append(media_read)
        return media_read_list

    def _get_db_item(self, media_id: int, session: Session) -> Media:
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
            raise ItemNotFoundError(self.__model_name, media_id)
        return db_media

    def _read_if_exists(
        self,
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
