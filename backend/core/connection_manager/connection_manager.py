from abc import ABC
from typing import Any, Callable, Optional, Protocol
from backend.core.files_handler import FilesHandler
from backend.database.models.connection import ConnectionRead, MonitorType


class ArrManagerProtocol(Protocol):
    """Abstract class for getting data from the Arr APIs."""

    async def get_system_status(self) -> str:
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")

    async def get_all_media(self) -> list[dict[str, Any]]:
        """Get all media from the Arr application. \n
        Returns:
            list[dict[str, Any]]: The media from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")


class MediaReadProtocol(Protocol):
    """Abstract class for reading media data."""

    id: int
    folder_path: Optional[str]


class ArrDatabaseHandlerProtocol[_MediaCreate, _MediaRead](Protocol):
    """Abstract class for handling database operations."""

    def create_or_update_bulk(
        self, media_create_list: list[_MediaCreate]
    ) -> list[tuple[_MediaRead, bool]]:
        """Create or update the data in the database. \n
        Args:
            media_create_list (list[Any]): The data to create or update in the database. \n
        Returns:
            list[tuple[_MediaRead, bool]]: List of tuples containing the _MediaRead objects \
                and a flag indicating if the data was created.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def update_media_status_bulk(self, media_status_list: list[tuple[int, bool, bool]]):
        """Update the media status in the database. \n
        Args:
            media_status_list (list[tuple[int, bool, bool]]): List of tuples containing the \
                media id, monitor status, and trailer status.
        """
        raise NotImplementedError("Subclasses must implement this method")


class ArrConnectionManager[_MediaCreate, _MediaRead: MediaReadProtocol](ABC):
    """Connection manager for working with the Arr applications.
    Abstract class that provides the base functionality for working with the Arr applications.
    """

    arr_manager: ArrManagerProtocol
    connection_id: int
    db_handler: ArrDatabaseHandlerProtocol[_MediaCreate, _MediaRead]
    inline_trailer: bool
    monitor: MonitorType
    parse_media: Callable[[int, dict[str, Any]], _MediaCreate]

    def __init__(
        self,
        connection: ConnectionRead,
        arr_manager: ArrManagerProtocol,
        parse_media: Callable[[int, dict[str, Any]], _MediaCreate],
        inline_trailer: bool,
        db_handler: ArrDatabaseHandlerProtocol[_MediaCreate, _MediaRead],
    ):
        """Initialize the ArrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        self.connection_id = connection.id
        self.monitor = connection.monitor
        self.arr_manager = arr_manager
        self.parse_media = parse_media
        self.inline_trailer = inline_trailer
        self.db_handler = db_handler

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

    async def _parse_data(self) -> list[_MediaCreate]:
        """Parse media received from the Arr API to objects that can be added to database.\n
        Returns:
            list[_MediaCreate]: list of parsed media objects."""
        media_data = await self._get_data()
        return [
            self.parse_media(self.connection_id, each_media_data)
            for each_media_data in media_data
        ]

    async def _check_trailer(self, folder_path: str) -> bool:
        """Check if a trailer exists for the media in the folder path.\n
        Args:
            folder_path (str): The folder path to check for the trailer.\n
        Returns:
            bool: True if the trailer exists, False otherwise."""
        trailer_exists = await FilesHandler.check_trailer_exists(
            path=folder_path,
            check_inline_file=self.inline_trailer,
        )
        return trailer_exists

    def _check_monitoring(self, is_new: bool, trailer_exists: bool) -> bool:
        """Check if the media should be monitored based on the monitor type.\n
        Args:
            is_new (bool): Flag indicating media is newly created in database.
            trailer_exists (bool): Flag indicating if a trailer exists on disk.\n
        Returns:
            bool: True if the media should be monitored, False otherwise."""
        # If Trailer already exists, no need to monitor
        if trailer_exists:
            return False
        # Monitor trailers if set to monitor missing
        if self.monitor == MonitorType.MONITOR_MISSING:
            return True
        # Monitor trailers if set to monitor new
        if self.monitor == MonitorType.MONITOR_NEW:
            return is_new
        # Sync monitor based on arr monitor status
        if self.monitor == MonitorType.MONITOR_SYNC:
            return True
        return False

    async def refresh(self):
        """Gets new data from Arr API and saves it to the database."""
        # Get the parsed data from the Arr API
        parsed_media = await self._parse_data()
        # Create or update the media in the database
        media_res = self.db_handler.create_or_update_bulk(parsed_media)
        # Check if media has trailer and should be monitored
        update_list: list[tuple[int, bool, bool]] = []
        for media_read, _created in media_res:
            if media_read.folder_path is None:
                trailer_exists = False
            else:
                trailer_exists = await self._check_trailer(media_read.folder_path)
            monitor_media = self._check_monitoring(_created, trailer_exists)
            update_list.append((media_read.id, monitor_media, trailer_exists))
        # Update the database with trailer and monitoring status
        self.db_handler.update_media_status_bulk(update_list)
        return
