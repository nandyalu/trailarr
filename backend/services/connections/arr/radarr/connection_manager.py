from core.base.connection_manager import BaseConnectionManager
from services.connections.arr.radarr.data_parser import parse_movie
from database.models.connection import ConnectionRead
from services.connections.arr.radarr.api_manager import RadarrManager


class RadarrConnectionManager(BaseConnectionManager):
    """Connection manager for working with the Radarr application."""

    connection_id: int

    def __init__(self, connection: ConnectionRead):
        """Initialize the RadarrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        radarr_manager = RadarrManager(connection.url, connection.api_key)
        self.connection_id = connection.id
        super().__init__(
            connection,
            radarr_manager,
            parse_movie,
            # inline_trailer=True,
            is_movie=True,
        )
