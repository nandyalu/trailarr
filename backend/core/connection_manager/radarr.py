from backend.core.arr_data_parser import parse_movie
from backend.core.connection_manager.connection_manager import ArrConnectionManager
from backend.database.crud.movie import MovieDatabaseHandler
from backend.database.models.connection import ConnectionRead
from backend.database.models.movie import MovieCreate, MovieRead
from backend.services.arr_manager.radarr import RadarrManager


class RadarrConnectionManager(ArrConnectionManager[MovieCreate, MovieRead]):
    """Connection manager for working with the Radarr application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the RadarrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        radarr_manager = RadarrManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        db_handler = MovieDatabaseHandler()
        super().__init__(
            connection,
            radarr_manager,
            parse_movie,
            inline_trailer=True,
            db_handler=db_handler,
        )

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
