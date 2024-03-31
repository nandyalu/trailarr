from backend.core.arr_data_parser import parse_series
from backend.core.connection_manager.connection_manager import ArrConnectionManager
from backend.database.crud.series import SeriesDatabaseHandler
from backend.database.models.connection import ConnectionRead
from backend.database.models.series import SeriesCreate, SeriesRead
from backend.services.arr_manager.sonarr import SonarrManager


class SonarrConnectionManager(ArrConnectionManager[SeriesCreate, SeriesRead]):
    """Connection manager for working with the Sonarr application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the SonarrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        sonarr_manager = SonarrManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        db_handler = SeriesDatabaseHandler()
        super().__init__(
            connection,
            sonarr_manager,
            parse_series,
            inline_trailer=False,
            db_handler=db_handler,
        )

    # async def _parse_data(self) -> list[SeriesCreate]:
    #     """Get the parsed data from the Sonarr application. \n
    #     Returns:
    #         list[SeriesCreate]: list of parsed series objects."""
    #     series_data = await self._get_data()
    #     return [
    #         parse_series(self.connection_id, each_series_data)
    #         for each_series_data in series_data
    #     ]

    # async def _check_trailer(self, folder_path: str) -> bool:
    #     """Check if a trailer exists for the series with given folder path.\n
    #     Args:
    #         folder_path (str): The folder path to check for the trailer.\n
    #     Returns:
    #         bool: True if the trailer exists, False otherwise."""
    #     trailer_exists = await FilesHandler.check_trailer_exists(
    #         path=folder_path,
    #         check_inline_file=False,
    #     )
    #     return trailer_exists

    async def refresh(self):
        """Gets new data from Sonarr API and saves it to the database."""
        # Get the parsed data from the Sonarr API
        parsed_series = await self._parse_data()
        # Create or update the series in the database
        db_handler = SeriesDatabaseHandler()
        series_res = db_handler.create_or_update_bulk(parsed_series)
        # Check if series has trailer and should be monitored
        update_list: list[tuple[int, bool, bool]] = []
        for series_read, _created in series_res:
            if series_read.folder_path is None:
                trailer_exists = False
            else:
                trailer_exists = await self._check_trailer(series_read.folder_path)
            monitor_series = self._check_monitoring(_created, trailer_exists)
            update_list.append((series_read.id, monitor_series, trailer_exists))
        # Update the database with trailer and monitoring status
        db_handler.update_media_status_bulk(update_list)
        return
