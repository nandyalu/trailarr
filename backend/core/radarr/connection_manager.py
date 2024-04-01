from dataclasses import dataclass
from datetime import datetime
from backend.core.base.connection_manager import (
    BaseConnectionManager,
    MediaUpdateDC,
)
from backend.core.radarr.data_parser import parse_movie
from backend.core.radarr.database_manager import MovieDatabaseHandler
from backend.core.base.database.models import (
    ArrType,
    ConnectionRead,
    MonitorType,
)
from backend.core.radarr.models import MovieCreate
from backend.core.radarr.api_manager import RadarrManager


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MovieReadDC:
    id: int
    created: bool
    folder_path: str | None


class RadarrConnectionManager(BaseConnectionManager[MovieCreate]):
    """Connection manager for working with the Radarr application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the RadarrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        radarr_manager = RadarrManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        # db_handler = MovieDatabaseHandler()
        super().__init__(
            connection,
            radarr_manager,
            parse_movie,
            inline_trailer=True,
            # db_handler=db_handler,
        )

    def create_or_update_bulk(self, media_data: list[MovieCreate]) -> list[MovieReadDC]:
        """Create or update movies in the database and return MediaRead objects.\n
        Args:
            media_data (list[MovieCreate]): The movie data to create or update.\n
        Returns:
            list[MediaReadDC]: A list of MediaRead objects."""
        movie_read_list = MovieDatabaseHandler().create_or_update_bulk(media_data)
        return [
            MovieReadDC(movie_read.id, created, movie_read.folder_path)
            for movie_read, created in movie_read_list
        ]

    def update_media_status_bulk(self, media_update_list: list[MediaUpdateDC]):
        """Update the media status in the database. \n
        Args:
            media_status_list (list[tuple[int, bool, bool]]): List of tuples containing the \
                media id, monitor status, and trailer status."""
        MovieDatabaseHandler().update_media_status_bulk(media_update_list)
        return


connection = ConnectionRead(
    id=1,
    arr_type=ArrType.RADARR,
    name="Radarr",
    monitor=MonitorType.MONITOR_NEW,
    added_at=datetime.now(),
    url="http://localhost:7878",
    api_key="api_key",
)
radarr_manager = RadarrConnectionManager(connection).create_or_update_bulk([])

# async def _parse_data(self) -> list[MovieCreate]:
#     """Get the parsed data from the Radarr application. \n
#     Returns:
#         list[MovieCreate]: list of parsed movie objects."""
#     movie_data = await self._get_data()
#     return [
#         parse_movie(self.connection_id, each_movie_data)
#         for each_movie_data in movie_data
#     ]

# async def _check_trailer(self, folder_path: str) -> bool:
#     """Check if a trailer exists for the movie with given folder path.\n
#     Args:
#         folder_path (str): The folder path to check for the trailer.\n
#     Returns:
#         bool: True if the trailer exists, False otherwise."""
#     trailer_exists = await FilesHandler.check_trailer_exists(
#         path=folder_path,
#         check_inline_file=True,
#     )
#     return trailer_exists

# async def refresh(self):
#     """Gets new data from Radarr API and saves it to the database."""
#     # Get the parsed data from the Radarr API
#     parsed_movies = await self._parse_data()
#     # Create or update the movies in the database
#     db_handler = MovieDatabaseHandler()
#     movies_res = db_handler.create_or_update_bulk(parsed_movies)
#     # Check if movie has trailer and should be monitored
#     update_list: list[tuple[int, bool, bool]] = []
#     for movie_read, _created in movies_res:
#         if movie_read.folder_path is None:
#             trailer_exists = False
#         else:
#             trailer_exists = await self._check_trailer(movie_read.folder_path)
#         monitor_movie = False
#         if not trailer_exists:
#             monitor_movie = self._check_monitoring(_created, trailer_exists)
#         update_list.append((movie_read.id, monitor_movie, trailer_exists))
#     # Update the database with trailer and monitoring status
#     db_handler.update_media_status_bulk(update_list)
#     return
