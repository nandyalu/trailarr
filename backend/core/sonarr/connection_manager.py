from core.base.connection_manager import BaseConnectionManager
from core.sonarr.data_parser import parse_series
from core.base.database.models.connection import ConnectionRead
from core.sonarr.api_manager import SonarrManager


class SonarrConnectionManager(BaseConnectionManager):
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
