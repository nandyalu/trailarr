import re
from typing import Optional
from typing import Sequence
from sqlmodel import Session, col, desc, select, or_
from backend.database.crud.connection import ConnectionDatabaseHandler
from backend.database.models.series import (
    Series,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)
from backend.database.utils.engine import manage_session
from backend.exceptions import ItemNotFoundError


class SeriesDatabaseHandler:
    """CRUD operations for series database table."""

    NO_SERIES_MESSAGE = "Series not found. Series id: {} does not exist!"
    NO_CONN_MESSAGE = "Connection not found. Connection id: {} does not exist!"

    # @manage_session
    # def create(
    #     self,
    #     series: SeriesCreate,
    #     *,
    #     _session: Session = None,  # type: ignore
    # ) -> bool:
    #     """Create a new series in the database.

    #     Args:
    #         series (SeriesCreate): The series to create.
    #         _session (optional): A session to use for the database connection. \
    #             Defaults to None, in which case a new session is created.

    #     Returns:
    #         bool: True if series creation is successful.

    #     Raises:
    #         ItemNotFoundError: If the connection with provided connection_id does not exist.
    #         ValidationError: If the series is invalid.
    #     """
    #     db_series = Series.model_validate(series)
    #     self._check_connection_exists(db_series.connection_id, _session=_session)
    #     _session.add(db_series)
    #     _session.commit()
    #     return True

    # @manage_session
    # def create_bulk(
    #     self,
    #     series_list: list[SeriesCreate],
    #     *,
    #     _session: Session = None,  # type: ignore
    # ) -> bool:
    #     """Create multiple series in the database at once.

    #     Args:
    #         series_list (list[SeriesCreate]): The list of series to create.
    #         _session (optional): A session to use for the database connection. \
    #             Defaults to None, in which case a new session is created.

    #     Returns:
    #         bool: True if all series are created successfully.

    #     Raises:
    #         ItemNotFoundError: If any of the connections with provided connection_id's are invalid
    #         ValidationError: If any of the series are invalid.
    #     """
    #     self._check_connection_exists_bulk(series_list)
    #     for series in series_list:
    #         db_series = Series.model_validate(series)
    #         _session.add(db_series)
    #     _session.commit()
    #     return True

    @manage_session
    def create_or_update_bulk(
        self,
        series_list: list[SeriesCreate],
        *,
        _session: Session = None,  # type: ignore
    ) -> bool:
        """Create or update multiple series in the database at once.

        If a series already exists, it will be updated, otherwise it will be created.

        Args:
            series_list (list[SeriesCreate]): The list of series to create or update.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if all series are created or updated successfully.

        Raises:
            ItemNotFoundError: If any of the connections with provided connection_id's are invalid.
            ValidationError: If any of the series are invalid.
        """
        self._check_connection_exists_bulk(series_list)
        for series in series_list:
            # TVDB id will be unique for every series in the same connection
            # So, we can use it to check if the series already exists in the database
            # If it does, we will update it, otherwise we will create it
            statement = (
                select(Series)
                .where(Series.connection_id == series.connection_id)
                .where(Series.tvdb_id == series.tvdb_id)
            )
            db_series = _session.exec(statement).one_or_none()
            if not db_series:
                # Doesn't exist, create it
                db_series = Series.model_validate(series)
            else:
                # Exists, update it
                series_update_data = series.model_dump(exclude_unset=True)
                db_series.sqlmodel_update(series_update_data)
            _session.add(db_series)
        _session.commit()
        return True

    @manage_session
    def _get_db_item(
        self,
        series_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> Series:
        """Get a series from the database. This is a private method.

        Args:
            series_id (int): The id of the series to read.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            Series: The series object.

        Raises:
            ItemNotFoundError: If a series with provided id does not exist.
        """
        db_series = _session.get(Series, series_id)
        if not db_series:
            raise ItemNotFoundError("Series", series_id)
        return db_series

    @manage_session
    def read(
        self,
        series_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> SeriesRead:
        """Read a series from the database.

        Args:
            series_id (int): The id of the series to read.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            SeriesRead: The read-only series object.

        Raises:
            ItemNotFoundError: If a series with provided id does not exist.
        """
        db_series = self._get_db_item(series_id, _session=_session)
        # Convert the database model (Series) to read-only model (SeriesRead) to return
        series = SeriesRead.model_validate(db_series)
        return series

    @manage_session
    def read_all(
        self,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[SeriesRead]:
        """Read all series from the database.

        Args:
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[SeriesRead]: The list of series[read] objects.
        """
        results = _session.exec(select(Series))
        series_list_results = results.all()
        return self._convert_to_read_list(series_list_results)

    @manage_session
    def read_all_by_connection(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[SeriesRead]:
        """Read all series from the database by connection id.

        Args:
            connection_id (int): The id of the connection to filter series.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[SeriesRead]: The list of series[read] objects.
        """
        statement = select(Series).where(Series.connection_id == connection_id)
        results = _session.exec(statement)
        series_list_results = results.all()
        return self._convert_to_read_list(series_list_results)

    @manage_session
    def read_recent(
        self,
        offset: int = 0,
        limit: int = 100,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[SeriesRead]:
        """Read series from the database with offset and limit (recently added first).

        Args:
            offset (int): The number of records to skip.
            limit (int): The number of records to return. Max 100.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[SeriesRead]: The list of series[read] objects.
        """
        offset = max(offset, 0)
        limit = max(1, min(limit, 100))

        statement = (
            select(Series).offset(offset).limit(limit).order_by(desc(Series.added_at))
        )
        results = _session.exec(statement)
        series_list_results = results.all()
        return self._convert_to_read_list(series_list_results)

    @manage_session
    def search(
        self,
        query: str,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[SeriesRead]:
        """Search series from the database by title, overview, imdb id, or tvdb id.
        If an exact match is found for imdb id or tvdb id, it will return only that series.
        If a 4 digit number is found in the query, it will return series from that year only.
        Otherwise, it will return a list of series matching the query. Recently added first, 50 max.

        Args:
            query (str): The search query.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[SeriesRead]: The list of series[read] objects.
        """
        if not query:
            return []
        # check if imdb id, tvdb id or year is present in the query
        imdb_id = self._extract_imdb_id(query)
        tvdb_id = self._extract_tvdb_id(query) if not imdb_id else None
        year = (
            self._extract_four_digit_number(query)
            if not imdb_id and not tvdb_id
            else None
        )

        statement = select(Series)
        if imdb_id:
            statement = statement.where(Series.imdb_id == imdb_id)
        elif tvdb_id:
            statement = statement.where(Series.tvdb_id == tvdb_id)
        else:
            if year:
                query = query.replace(year, "").strip().replace("  ", " ")
                statement = statement.where(Series.year == year)
            # Build rest of the query
            statement = (
                statement.where(
                    or_(
                        col(Series.title).ilike(query),
                        col(Series.overview).ilike(query),
                    )
                )
                .limit(50)
                .order_by(desc(Series.added_at))
            )
        results = _session.exec(statement)
        series_list_results = results.all()
        return self._convert_to_read_list(series_list_results)

    @manage_session
    def update(
        self,
        series_id: int,
        series: SeriesUpdate,
        *,
        _session: Session = None,  # type: ignore
    ):
        """Update an existing series in the database.

        Args:
            series_id (int): The id of the series to update.
            series (SeriesUpdate): The series data to update.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if series update is successful.

        Raises:
            ItemNotFoundError: If a series with provided id does not exist.
        """
        # Get the series from the database
        db_series = self._get_db_item(series_id, _session=_session)

        # Update the series details from input
        series_update_data = series.model_dump(exclude_unset=True)
        db_series.sqlmodel_update(series_update_data)

        # Check if the connection exists
        self._check_connection_exists(db_series.connection_id)

        # Commit the changes to the database
        _session.add(db_series)
        _session.commit()
        return True

    @manage_session
    def delete(
        self,
        series_id: int,
        *,
        _session: Session = None,  # type: ignore
    ):
        """Delete an existing series from the database.

        Args:
            series_id (int): The id of the series to delete.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if series deletion is successful.

        Raises:
            ItemNotFoundError: If a series with provided id does not exist.
        """
        db_series = self._get_db_item(series_id, _session=_session)
        _session.delete(db_series)
        _session.commit()
        return True

    @manage_session
    def delete_bulk(
        self,
        series_ids: set[int],
        *,
        _session: Session = None,  # type: ignore
    ):
        """Delete multiple existing series from the database at once.

        Args:
            series_ids (list[int]): The list of series id's to delete.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if all series deletions are successful.

        Raises:
            ItemNotFoundError: If any of the series with provided id's do not exist.
        """
        for series_id in series_ids:
            db_series = self._get_db_item(series_id, _session=_session)
            _session.delete(db_series)
        _session.commit()
        return True

    @manage_session
    def _check_connection_exists(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ):
        """Check if the connection exists in the database.

        Args:
            connection_id (int): The id of the connection to check.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            None

        Raises:
            ItemNotFoundError: If a connection with provided id does not exist.
        """
        if not ConnectionDatabaseHandler().check_if_exists(
            connection_id, _session=_session
        ):
            raise ItemNotFoundError("Connection", connection_id)

    @manage_session
    def _check_connection_exists_bulk(
        self,
        series_list: list[SeriesCreate],
        *,
        _session: Session = None,  # type: ignore
    ):
        """Check if the connections exist in the database.

        Args:
            series_list (list[SeriesCreate]): The list of series to check.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            None

        Raises:
            ItemNotFoundError: If any of the connections with provided id's do not exist.
        """
        connection_ids = {series.connection_id for series in series_list}
        for connection_id in connection_ids:
            if not ConnectionDatabaseHandler().check_if_exists(
                connection_id, _session=_session
            ):
                raise ItemNotFoundError("Connection", connection_id)

    def _convert_to_read_list(self, series_list: Sequence[Series]) -> list[SeriesRead]:
        """Convert a list of Series to a list of SeriesRead."""
        if not series_list or len(series_list) == 0:
            return []
        series_list_read: list[SeriesRead] = []
        for series in series_list:
            series_list_read.append(SeriesRead.model_validate(series))
        return series_list_read

    def _extract_four_digit_number(self, query: str) -> Optional[str]:
        """Extract last 4 digit number from a string."""
        matches = re.findall(r"\b\d{4}\b", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _extract_imdb_id(self, query: str) -> Optional[str]:
        """Extract an imdb id from a string."""
        matches = re.findall(r"tt\d{7,}", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _extract_tvdb_id(self, query: str) -> Optional[str]:
        """Extract a tvdb id from a string."""
        matches = re.findall(r"\b\d{5,}\b", query)
        last_match = matches[-1] if matches else None
        return last_match
