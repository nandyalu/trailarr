import asyncio
from datetime import datetime
from typing import Any
from backend.core.arr_data_parser import parse_movie, parse_series
from backend.core.files_handler import FilesHandler
from backend.database.crud.movie import MovieDatabaseHandler
from backend.database.crud.series import SeriesDatabaseHandler
from backend.database.models.connection import ArrType, ConnectionRead, MonitorType
from backend.database.models.movie import MovieCreate, MovieRead, MovieUpdate
from backend.database.models.series import SeriesCreate, SeriesRead, SeriesUpdate
from backend.services.arr_manager.radarr import RadarrManager
from backend.services.arr_manager.sonarr import SonarrManager


class ArrConnectionManager:

    connection_id: int
    monitor: MonitorType
    arr_manager: RadarrManager | SonarrManager

    def __init__(self, connection: ConnectionRead):
        """Initialize the ArrConnectionHelper. \n
        Args:
            connection (ConnectionRead): The connection data."""
        self.connection_id = connection.id
        self.monitor = connection.monitor
        if connection.arr_type == ArrType.SONARR:
            self.arr_manager = SonarrManager(connection.url, connection.api_key)
        elif connection.arr_type == ArrType.RADARR:
            self.arr_manager = RadarrManager(connection.url, connection.api_key)

    def __new__(cls, connection: ConnectionRead):
        """Create a helper instance based on the Arr type."""
        if connection.arr_type == ArrType.SONARR:
            return SonarrConnectionManager(connection)
        elif connection.arr_type == ArrType.RADARR:
            return RadarrConnectionManager(connection)
        else:
            raise NotImplementedError("Arr type not implemented")

    async def get_system_status(self):
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application.
            None: If the system status could not be retrieved."""
        try:
            return await self.arr_manager.get_system_status()
        except Exception:
            return None

    async def _get_data(self) -> list[dict[str, Any]]:
        """Get the data from the Arr application. \n
        Returns:
            - list[dict[str, Any]]: The data from the Arr application.
            - An empty list if the data could not be retrieved."""
        try:
            return await self.arr_manager.get_all_media()
        except Exception:
            return []

    def _parse_data(self) -> list[object]:
        """Parse media received from the Arr API to objects that can be added to database.\n
        Returns:
            list[object]: list of parsed media objects."""
        raise NotImplementedError("Subclasses must implement this method")

    async def _set_monitoring(self, media_read: object, is_new: bool = False) -> object:
        """Set the monitoring status for the media and by checking if a trailar exists on disk.\n
        Args:
            media_read (object): The media data to be saved to the database.
            is_new (bool): Flag indicating media is newly created in database.\n
        Returns:
            object: The update object with the monitoring status set."""
        raise NotImplementedError("Subclasses must implement this method")

    async def refresh(self):
        """Gets new data from Arr API and saves it to the database."""
        raise NotImplementedError("Subclasses must implement this method")


class RadarrConnectionManager(ArrConnectionManager):
    """Connection manager for working with the Radarr application."""

    async def _parse_data(self) -> list[MovieCreate]:
        """Get the parsed data from the Radarr application. \n
        Returns:
            list[MovieCreate]: list of parsed movie objects."""
        movie_data = await self._get_data()
        return [
            parse_movie(self.connection_id, each_movie_data)
            for each_movie_data in movie_data
        ]

    async def _set_monitoring(
        self, movie_read: MovieRead, is_new: bool = False
    ) -> MovieUpdate:
        """Set the monitoring status for the movie in the application. \n
        Args:
            movie_read (MovieRead): The movie data to be saved to the database.
            is_new (bool): Flag indicating movie is newly created in database. \n
        Returns:
            MovieUpdate: The update object with the monitoring status set.
        """
        movie_update = MovieUpdate(tmdb_id=movie_read.tmdb_id)
        _folder_path = movie_read.folder_path or ""
        _check_inline_file = True
        movie_update.trailer_exists = await FilesHandler.check_trailer_exists(
            path=_folder_path,
            check_inline_file=_check_inline_file,
        )

        movie_update.monitor = False
        # If Trailer already exists, no need to monitor
        if movie_update.trailer_exists:
            return movie_update
        # Monitor trailers if set to monitor new
        if self.monitor == MonitorType.MONITOR_NEW:
            movie_update.monitor = is_new
        # Monitor trailers if set to monitor missing
        if self.monitor == MonitorType.MONITOR_MISSING:
            movie_update.monitor = True
        return movie_update

    async def refresh(self):
        """Gets new data from Radarr API and saves it to the database."""
        parsed_movies = await self._parse_data()
        movies_res = MovieDatabaseHandler().create_or_update_bulk(parsed_movies)
        update_list: list[tuple[int, MovieUpdate]] = []
        for movie_read, _created in movies_res:
            movie_update = await self._set_monitoring(movie_read, is_new=_created)
            update_list.append((movie_read.id, movie_update))
        MovieDatabaseHandler().update_bulk(update_list)


class SonarrConnectionManager(ArrConnectionManager):
    """Connection manager for working with the Sonarr application."""

    async def _parse_data(self) -> list[SeriesCreate]:
        """Get the parsed data from the Sonarr application. \n
        Returns:
            list[SeriesCreate]: list of parsed series objects."""
        series_data = await self._get_data()
        return [
            parse_series(self.connection_id, each_series_data)
            for each_series_data in series_data
        ]

    async def _set_monitoring(
        self, series_read: SeriesRead, is_new: bool = False
    ) -> SeriesUpdate:
        """Set the monitoring status for the series in the application. \n
        Args:
            series_read (SeriesRead): The series data to be saved to the database.
            is_new (bool): Flag indicating series is newly created in database. \n
        Returns:
            SeriesUpdate: The update object with the monitoring status set.
        """
        series_update = SeriesUpdate(tvdb_id=series_read.tvdb_id)
        _folder_path = series_read.folder_path or ""
        _check_inline_file = False
        series_update.trailer_exists = await FilesHandler.check_trailer_exists(
            path=_folder_path,
            check_inline_file=_check_inline_file,
        )

        series_update.monitor = False
        # If Trailer already exists, no need to monitor
        if series_update.trailer_exists:
            return series_update
        # Monitor trailers if set to monitor new
        if self.monitor == MonitorType.MONITOR_NEW:
            series_update.monitor = is_new
        # Monitor trailers if set to monitor missing
        if self.monitor == MonitorType.MONITOR_MISSING:
            series_update.monitor = True
        return series_update

    async def refresh(self):
        """Gets new data from Sonarr API and saves it to the database."""
        parsed_series = await self._parse_data()
        series_res = SeriesDatabaseHandler().create_or_update_bulk(parsed_series)
        for series_read, _created in series_res:  # type: ignore
            series_update = await self._set_monitoring(series_read, is_new=_created)
            if isinstance(series_update, SeriesUpdate):
                SeriesDatabaseHandler().update(series_read.id, series_update)


# class ArrConnectionManager:
#     """Connection manager for working with the Arr applications."""

#     def __init__(self, connection: ConnectionRead):
#         """Initialize the ArrConnectionManager. \n
#         Args:
#             connection (ConnectionRead): The connection data.
#         Raises:
#             NotImplementedError: If the Arr type is not implemented."""

#         # Raise a NotImplementedError if the Arr type is not implemented
#         if connection.arr_type not in [ArrType.SONARR, ArrType.RADARR]:
#             raise NotImplementedError("Arr type not implemented")
#         if connection.arr_type == ArrType.SONARR:
#             self.arr_helper = SonarrConnectionHelper(connection)
#         elif connection.arr_type == ArrType.RADARR:
#             self.arr_helper = RadarrConnectionHelper(connection)

#     async def refresh(self) -> None:
#         """Refresh the data from the Arr application."""
#         # media_data = await self._get_data()
#         await self.arr_helper.save_media()


async def refresh_connection(connection: ConnectionRead):
    """Refresh the connection data from the Arr application. \n
    Args:
        connection (ConnectionRead): The connection data."""
    arr_manager = ArrConnectionManager(connection)
    await arr_manager.refresh()


connection = ConnectionRead(
    id=1,
    name="Test Connection",
    url="http://localhost",
    api_key="1234",
    arr_type=ArrType.SONARR,
    monitor=MonitorType.MONITOR_NEW,
    added_at=datetime(2024, 3, 27, 18, 30, 0),
)
asyncio.run(refresh_connection(connection))
