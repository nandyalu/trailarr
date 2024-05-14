from core.base.connection_manager import (
    BaseConnectionManager,
    MediaUpdateDC,
)
from core.base.database.models.helpers import MediaReadDC
from core.sonarr.data_parser import parse_series
from core.sonarr.database_manager import SeriesDatabaseManager
from core.base.database.models.connection import ConnectionRead
from core.sonarr.models import SeriesCreate
from core.sonarr.api_manager import SonarrManager


class SonarrConnectionManager(BaseConnectionManager[SeriesCreate]):
    """Connection manager for working with the Sonarr application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the SonarrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        sonarr_manager = SonarrManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        super().__init__(
            connection,
            sonarr_manager,
            parse_series,
            inline_trailer=False,
        )

    def create_or_update_bulk(
        self, media_data: list[SeriesCreate]
    ) -> list[MediaReadDC]:
        """Create or update series in the database and return SeriesRead objects.\n
        Args:
            media_data (list[SeriesCreate]): The series data to create or update.\n
        Returns:
            list[SeriesRead]: A list of SeriesRead objects."""
        series_read_list = SeriesDatabaseManager().create_or_update_bulk(media_data)
        return [
            MediaReadDC(
                id=series_read.id,
                created=created,
                folder_path=series_read.folder_path,
                arr_monitored=series_read.arr_monitored,
                monitor=series_read.monitor,
            )
            for series_read, created in series_read_list
        ]

    def update_media_status_bulk(self, media_update_list: list[MediaUpdateDC]):
        """Update the media status in the database. \n
        Args:
            media_update_list (list[MediaUpdateDC]): List of MediaUpdateDC objects."""
        SeriesDatabaseManager().update_media_status_bulk(media_update_list)
        return
