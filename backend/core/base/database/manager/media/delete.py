from sqlmodel import col, select, Session

from core.base.database.manager.media import logger
from core.base.database.manager.media.base import BaseMediaManager
from core.base.database.models.media import Media
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError

_base = BaseMediaManager()


class DeleteMediaManager:

    __model_name = "Media"

    @manage_session
    def delete(
        self,
        media_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Delete a media item from the database by id.\n
        Args:
            media_id (int): The id of the media to delete.
            _session (Session) [Optional]: A session to use for the database connection.\
                Default is None, in which case a new session will be created.\n
        Returns:
            None
        Raises:
            ItemNotFoundError: If the media item with provided id doesn't exist.
        """
        db_media = _base._get_db_item(media_id, _session)
        _session.delete(db_media)
        _session.commit()
        return

    @manage_session
    def delete_bulk(
        self,
        media_ids: list[int],
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Delete multiple media items from the database at once.\n
        Args:
            media_ids (list[int]): List of media id's to delete.
            _session (Session) [Optional]: A session to use for the database connection.\
                Default is None, in which case a new session will be created.\n
        Returns:
            None
        Raises:
            ItemNotFoundError: If any of the media items with provided id's don't exist.
        """
        for media_id in media_ids:
            try:
                media_db = _base._get_db_item(media_id, _session)
                _session.delete(media_db)
            except ItemNotFoundError:
                logger.debug(
                    f"{self.__model_name} with id {media_id} doesn't exist in the database. "
                    "Skipping!"
                )
        _session.commit()
        return

    @manage_session
    def delete_except(
        self,
        connection_id: int,
        media_ids: list[int],
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Delete all media items from the database except the ones provided.\n
        Args:
            connection_id (int): The id of the connection to delete media items for.
            media_ids (list[int]): List of media id's to keep.
            _session (Session) [Optional]: A session to use for the database connection.\
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
