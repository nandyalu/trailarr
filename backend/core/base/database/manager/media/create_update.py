from datetime import datetime, timezone
from typing import Sequence
from sqlmodel import Session
from core.base.database.manager.media import logger
from core.base.database.manager.media.base import BaseMediaManager
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import Media, MediaCreate, MediaRead, MediaUpdate
from core.base.database.utils.engine import manage_session

_base = BaseMediaManager()


class MediaCreateUpdateManager:
    """
    Database manager for Create and Update operations on Media objects.\n
    """

    __model_name = "Media"

    def _create_or_update(
        self, media_create: MediaCreate, session: Session
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
        db_media = _base._read_if_exists(
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
            if session.is_modified(db_media):
                db_media.updated_at = datetime.now(timezone.utc)
                _updated = True
            session.add(db_media)
            return db_media, False, _updated
        else:
            # Doesn't exist, Create it
            db_media = Media.model_validate(media_create)
            session.add(db_media)
            return db_media, True, False

    @manage_session
    def create_or_update_bulk(
        self,
        media_create_list: list[MediaCreate],
        *,
        _session: Session = None,  # type: ignore
    ) -> list[tuple[MediaRead, bool]]:
        """Create or update multiple media objects in the database at once. \n
        If media already exists, it will be updated, otherwise it will be created.\n
        Args:
            media_create_list (list[MediaCreate]): List of media objects to create or update.\n
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[tuple[MediaRead, bool]]: List of tuples with MediaRead objects and created flag.\n
            Example::\n
                [(<MediaRead obj 1>, True), (<MediaRead obj 2>, False), ...] \n
        Raises:
            ItemNotFoundError: If any of the connections with provided connection_id's are invalid.
            ValidationError: If any of the media items are invalid.
        """
        _base._check_connection_exists_bulk(media_create_list, session=_session)
        db_media_list: list[tuple[Media, bool]] = []
        new_count: int = 0
        updated_count: int = 0
        for media_create in media_create_list:
            db_media, created, updated = self._create_or_update(media_create, _session)
            db_media_list.append((db_media, created))
            if created:
                new_count += 1
            if updated:
                updated_count += 1
        _session.commit()
        logger.info(
            f"{self.__model_name}: {new_count} Created, {updated_count} Updated."
        )
        return [
            (MediaRead.model_validate(db_media), created)
            for db_media, created in db_media_list
        ]

    # DELETE LATER - NOT USING ANYWHERE
    @manage_session
    def update(
        self,
        media_id: int,
        media_update: MediaUpdate,
        *,
        _commit: bool = True,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Update an existing media item in the database by id.\n
        Args:
            media_id (int): The id of the media to update.
            media_update (MediaUpdate): The media data to update.
            _commit (bool) [Optional]: Flag to `commit` the changes. Default is `True`.
            _session (Session) [Optional]: A session to use for the database connection. \
                Default is None, in which case a new session will be created. \n
        Returns:
            None
        Raises:
            ItemNotFoundError: If the media item with provided id doesn't exist.
        """
        db_media = _base._get_db_item(media_id, _session)
        media_update_data = media_update.model_dump(
            exclude_unset=True,
            exclude_defaults=True,
            exclude_none=True,
            exclude={"youtube_trailer_id", "downloaded_at"},
        )
        db_media.sqlmodel_update(media_update_data)
        _session.add(db_media)
        if _commit:
            _session.commit()
        return

    @manage_session
    def update_bulk(
        self,
        media_updates: list[tuple[int, MediaUpdate]],
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Update multiple media items in the database at once.\n
        Args:
            media_updates (list[tuple[int, MediaUpdate]]): List of tuples with media id \
                and update data.\n
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            None
        Raises:
            ItemNotFoundError: If any of the media items with provided id's don't exist.
        """
        for media_id, media_update in media_updates:
            self.update(media_id, media_update, _session=_session, _commit=False)
        _session.commit()
        return

    @manage_session
    def update_media_status(
        self,
        media_update: MediaUpdateDC,
        *,
        _commit: bool = True,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Update the monitoring status of a media item in the database by id.\n
        Args:
            media_update (MediaUpdateProtocol): The media update object satisfying the protocol.
            _commit (bool) [Optional]: Flag to `commit` the changes. Default is `True`.
            _session (Session) [Optional]: A session to use for the database connection. \
                Default is None, in which case a new session will be created.
        Returns:
            None
        Raises:
            ItemNotFoundError: If the media item with provided id doesn't exist.
        """
        db_media = _base._get_db_item(media_update.id, _session)
        db_media.monitor = media_update.monitor
        db_media.trailer_exists = media_update.trailer_exists
        if media_update.downloaded_at:
            db_media.downloaded_at = media_update.downloaded_at
        if media_update.yt_id:
            db_media.youtube_trailer_id = media_update.yt_id
        _session.add(db_media)
        if _commit:
            _session.commit()
        return

    @manage_session
    def update_media_status_bulk(
        self,
        media_update_list: Sequence[MediaUpdateDC],
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Update the monitoring status of multiple media items in the database at once.\n
        Args:
            media_update_list (Sequence[MediaUpdateProtocol]): Sequence of media update objects.\n
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.
        Returns:
            None
        Raises:
            ItemNotFoundError: If any of the media items with provided id's don't exist.
        """
        for media_update in media_update_list:
            self.update_media_status(media_update, _session=_session, _commit=False)
        _session.commit()
        return
