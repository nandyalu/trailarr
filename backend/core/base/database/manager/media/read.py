from sqlmodel import col, desc, select, Session
from core.base.database.manager.media import logger
from core.base.database.manager.media.base import BaseMediaManager
from core.base.database.models.media import Media, MediaRead
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError

_base = BaseMediaManager()


class ReadMediaManager:

    @manage_session
    def read(
        self,
        id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> MediaRead:
        """Get a media object from the database by id.\n
        Args:
            id (int): The id of the media object to get.
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            MediaRead: The MediaRead object if it exists.
        Raises:
            ItemNotFoundError: If the media item with provided id doesn't exist.
        """
        db_media = _base._get_db_item(id, _session)
        # Convert Media object to MediaRead object to return
        media_read = MediaRead.model_validate(db_media)
        return media_read

    @manage_session
    def read_all(
        self,
        movies_only: bool | None = None,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Get all media objects from the database.\n
        Args:
            movies_only (bool) [Optional]: Flag to get only movies. Default is None.\n
                If True, it will return only movies. If False, it will return only series.\n
                If None, it will return all media items.\n
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[MediaRead]: List of MediaRead objects.
        """
        statement = select(Media)
        if movies_only is not None:
            statement = statement.where(col(Media.is_movie).is_(movies_only))
        db_media_list = _session.exec(statement).all()
        return _base._convert_to_read_list(db_media_list)

    @manage_session
    def read_all_by_connection(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Get all media objects from the database for a given connection.\n
        Args:
            connection_id (int): The id of the connection to get media items for.
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[MediaRead]: List of MediaRead objects.
        """
        try:
            _base._check_connection_exists(connection_id, session=_session)
        except ItemNotFoundError:
            logger.debug(
                f"Connection with id {connection_id} doesn't exist in the database."
                " Returning empty list."
            )
            return []
        statement = select(Media).where(Media.connection_id == connection_id)
        db_media_list = _session.exec(statement).all()
        return _base._convert_to_read_list(db_media_list)

    @manage_session
    def read_recent(
        self,
        limit: int = 100,
        offset: int = 0,
        movies_only: bool | None = None,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Get the most recent media objects from the database.\n
        Args:
            limit (int) [Optional]: The number of recent media items to get. Max 100
            offset (int) [Optional]: The offset to start from. Default is 0.
            movies_only (bool) [Optional]: Flag to get only movies. Default is None.\n
                If True, it will return only movies. If False, it will return only series.\n
                If None, it will return all media items.\n
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[MediaRead]: List of MediaRead objects.
        """
        offset = max(0, offset)
        limit = max(1, min(limit, 100))
        statement = select(Media)
        if movies_only is not None:
            statement = statement.where(col(Media.is_movie).is_(movies_only))
        statement = statement.order_by(desc(Media.added_at)).offset(offset).limit(limit)
        db_media_list = _session.exec(statement).all()
        return _base._convert_to_read_list(db_media_list)

    @manage_session
    def read_recently_downloaded(
        self,
        limit: int = 100,
        offset: int = 0,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Get the most recently downloaded media objects from the database.\n
        Args:
            limit (int) [Optional]: The number of recent media items to get. Max 100
            offset (int) [Optional]: The offset to start from. Default is 0.
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[MediaRead]: List of MediaRead objects.
        """
        offset = max(0, offset)
        limit = max(1, min(limit, 100))
        statement = (
            select(Media)
            .where(col(Media.downloaded_at).is_not(None))
            .order_by(desc(Media.downloaded_at))
            .offset(offset)
            .limit(limit)
        )
        db_media_list = _session.exec(statement).all()
        return _base._convert_to_read_list(db_media_list)
