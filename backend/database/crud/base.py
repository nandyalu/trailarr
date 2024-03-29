from datetime import datetime
import logging
import re
from typing import Optional, Sequence
from sqlmodel import Session, col, desc, or_, select

from backend.database.crud.connection import ConnectionDatabaseHandler
from backend.database.models.movie import (
    Movie,
    MovieCreate,
    MovieRead,
    MovieUpdate,
)
from backend.database.models.series import (
    Series,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)
from backend.database.utils.engine import manage_session
from backend.exceptions import ItemNotFoundError


class DatabaseHandler[
    Media: Movie | Series,
    MediaCreate: MovieCreate | SeriesCreate,
    MediaRead: MovieRead | SeriesRead,
    MediaUpdate: MovieUpdate | SeriesUpdate,
]:
    __db_model: type[Media]
    __read_model: type[MediaRead]

    def __init__(
        self, session: Session, db_model: type[Media], read_model: type[MediaRead]
    ):
        self.session = session
        self.__db_model = db_model
        self.__read_model = read_model

    def _create_or_update(
        self, media_create: MediaCreate, session: Session
    ) -> tuple[Media, bool, bool]:
        """-->>This is a private method<<-- \n
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
        db_media = self._read_if_exists(
            media_create.connection_id, media_create.arr_id, session
        )
        if db_media:
            # Exists, update it
            media_update_data = media_create.model_dump(exclude_unset=True)
            db_media.sqlmodel_update(media_update_data)
            _updated = False
            if session.is_modified(db_media):
                db_media.updated_at = datetime.now()
                _updated = True
            session.add(db_media)
            return db_media, False, _updated
        else:
            # Doesn't exist, Create it
            db_media = self.__db_model.model_validate(media_create)
            session.add(db_media)
            return db_media, True, False

    @manage_session
    def create_or_update_bulk(
        self,
        media_creates: list[MediaCreate],
        *,
        _session: Session = None,  # type: ignore
    ) -> list[tuple[MediaRead, bool]]:
        """Create or update multiple media objects in the database at once. \n
        If media already exists, it will be updated, otherwise it will be created.\n
        Args:
            media_creates (list[MediaCreate]): List of media objects to create or update.\n
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
        self._check_connection_exists_bulk(media_creates, session=_session)
        db_media_list: list[tuple[Media, bool]] = []
        new_count: int = 0
        updated_count: int = 0
        for media_create in media_creates:
            db_media, created, updated = self._create_or_update(media_create, _session)
            db_media_list.append((db_media, created))
            if created:
                new_count += 1
            if updated:
                updated_count += 1
            db_media_list.append((db_media, created))
        _session.commit()
        logging.info(
            f"{self.__db_model.__name__}: {new_count} Created, {updated_count} Updated."
        )
        return [
            (self.__read_model.model_validate(db_media), created)
            for db_media, created in db_media_list
        ]

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
        db_media = self._get_db_item(id, _session)
        # Convert Media object to MediaRead object to return
        media_read = self.__read_model.model_validate(db_media)
        return media_read

    @manage_session
    def read_all(
        self,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Get all media objects from the database.\n
        Args:
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[MediaRead]: List of MediaRead objects.
        """
        statement = select(self.__db_model)
        db_media_list = _session.exec(statement).all()
        return self._convert_to_read_list(db_media_list)

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
            self._check_connection_exists(connection_id, session=_session)
        except ItemNotFoundError:
            logging.debug(
                f"Connection with id {connection_id} doesn't exist in the database."
                " Returning empty list."
            )
            return []
        statement = select(self.__db_model).where(
            self.__db_model.connection_id == connection_id
        )
        db_media_list = _session.exec(statement).all()
        return self._convert_to_read_list(db_media_list)

    @manage_session
    def read_recent(
        self,
        limit: int = 100,
        offset: int = 0,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Get the most recent media objects from the database.\n
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
            select(self.__db_model)
            .order_by(desc(self.__db_model.added_at))
            .offset(offset)
            .limit(limit)
        )
        db_media_list = _session.exec(statement).all()
        return self._convert_to_read_list(db_media_list)

    @manage_session
    def search(
        self,
        query: str,
        *,
        offset: int = 0,
        _session: Session = None,  # type: ignore
    ) -> list[MediaRead]:
        """Search for media objects in the database by `title`, `overview`, \
            `imdb id`, or `txdb id` [tmdb for `Movie`, tvdb for `Series`].\n
        If an exact match is found for `imdb id` or `txdb id`, it will return only that item.\n
        If a 4 digit number is found in the query, \
            it will only return list of media from that year [1900-2100].\n
        Otherwise, it will return a list of [max 50 recently added] Media matching the query.\n
        Args:
            query (str): The search query to search for in the media items.
            offset (int) [Optional]: The offset to start from. Default is 0.
            _session (Session) [Optional]: A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            list[MediaRead]: List of MediaRead objects.
        """
        offset = max(0, offset)
        limit = 50
        statement = self._get_search_statement(query, limit, offset)
        if statement is None:
            return []
        db_media_list = _session.exec(statement).all()
        return self._convert_to_read_list(db_media_list)

    @manage_session
    def update(
        self,
        media_id: int,
        media_update: MediaUpdate,
        *,
        _session: Session = None,  # type: ignore
        _commit: bool = True,
    ) -> None:
        """Update an existing media item in the database by id.\n
        Args:
            media_id (int): The id of the media to update.
            media_update (MediaUpdate): The media data to update.
            _session (Session) [Optional]: A session to use for the database connection. \
                Default is None, in which case a new session will be created.
            _commit (bool) [Optional]: Flag to `commit` the changes. Default is `True`. \n
        Returns:
            None
        Raises:
            ItemNotFoundError: If the media item with provided id doesn't exist.
        """
        db_media = self._get_db_item(media_id, _session)
        media_update_data = media_update.model_dump(exclude_unset=True)
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
        db_media = self._get_db_item(media_id, _session)
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
                media_db = self._get_db_item(media_id, _session)
                _session.delete(media_db)
            except ItemNotFoundError:
                logging.debug(
                    f"{self.__db_model.__name__} with id {media_id} doesn't exist in the database. "
                    "Skipping!"
                )
        _session.commit()
        return

    def _check_connection_exists(self, connection_id: int, session: Session) -> None:
        """-->>This is a private method<<-- \n
        Check if a connection exists in the database.\n
        Args:
            connection_id (int): The id of the connection to check.
            session (Session): A session to use for the database connection.\n
        Raises:
            ItemNotFoundError: If the connection with provided connection_id is invalid.
        """
        if not ConnectionDatabaseHandler().check_if_exists(
            connection_id, _session=session
        ):
            raise ItemNotFoundError("Connection", connection_id)
        return

    def _check_connection_exists_bulk(
        self, media_items: list[MediaCreate], session: Session
    ) -> None:
        """-->>This is a private method<<-- \n
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
        """-->>This is a private method<<-- \n
        Convert a list of Media objects to a list of MediaRead objects.\n"""
        if not db_media_list or len(db_media_list) == 0:
            return []
        media_read_list: list[MediaRead] = []
        for db_media in db_media_list:
            media_read = self.__read_model.model_validate(db_media)
            media_read_list.append(media_read)
        return media_read_list

    def _extract_four_digit_number(self, query: str) -> Optional[str]:
        """-->>This is a private method<<-- \n
        Extract a 4 digit number from a string."""
        matches = re.findall(r"\b\d{4}\b", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _extract_imdb_id(self, query: str) -> Optional[str]:
        """-->>This is a private method<<-- \n
        Extract an imdb id from a string."""
        matches = re.findall(r"tt\d{7,}", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _extract_tmdb_id(self, query: str) -> Optional[str]:
        """-->>This is a private method<<-- \n
        Extract a tmdb id from a string."""
        matches = re.findall(r"\b\d{6}\b", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _get_search_statement(self, query: str, limit: int = 50, offset: int = 0):
        """-->>This is a private method<<-- \n
        Get a search statement for the database query.\n"""
        if not query:
            return None
        imdb_id = self._extract_imdb_id(query)
        statement = select(self.__db_model)
        if imdb_id:
            statement = statement.where(self.__db_model.imdb_id == imdb_id)
            return statement
        tmdb_id = self._extract_tmdb_id(query)
        if tmdb_id:
            statement = statement.where(self.__db_model.tmdb_id == tmdb_id)
            return statement
        year = self._extract_four_digit_number(query)
        if year and int(year) > 1900 and int(year) < 2100:
            query = query.replace(year, "").strip().replace("  ", " ")
            statement = statement.where(self.__db_model.year == year)
        statement = (
            statement.where(
                or_(
                    col(self.__db_model.title).ilike(query),
                    col(self.__db_model.overview).ilike(query),
                )
            )
            .offset(offset)
            .limit(limit)
            .order_by(desc(self.__db_model.added_at))
        )
        return statement

    def _get_db_item(self, media_id: int, session: Session) -> Media:
        """-->>This is a private method<<-- \n
        Get a media item from the database by id.\n
        Args:
            media_id (int): The id of the media item to get.
            session (Session): A session to use for the database connection.\n
        Returns:
            Media: The media object if it exists.
        Raises:
            ItemNotFoundError: If the media item with provided id doesn't exist.
        """
        db_media = session.get(self.__db_model, media_id)
        if not db_media:
            raise ItemNotFoundError(self.__db_model.__name__, media_id)
        return db_media

    def _read_if_exists(
        self,
        connection_id: int,
        arr_id: int,
        session: Session,
    ) -> Media | None:
        """-->>This is a private method<<-- \n
        Check if a media item exists in the database for any given connection and arr ids.\n
        Args:
            connection_id (int): The id of the connection to check.
            arr_id (int): The arr id of the media item to check.
            session (Session): A session to use for the database connection.\n
        Returns:
            Media | None: The media object if it exists, otherwise None.
        """
        statement = (
            select(self.__db_model)
            .where(self.__db_model.connection_id == connection_id)
            .where(self.__db_model.arr_id == arr_id)
        )
        db_media = session.exec(statement).one_or_none()
        return db_media
