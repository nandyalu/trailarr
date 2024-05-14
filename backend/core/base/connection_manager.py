from abc import ABC, abstractmethod
from functools import cache
from typing import Any, Callable, Protocol

from core.base.database.models.helpers import MediaReadDC, MediaUpdateDC
from core.files_handler import FilesHandler
from core.base.database.models.connection import ConnectionRead, MonitorType


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


class BaseConnectionManager[_MediaCreate](ABC):
    """Connection manager for working with the Arr applications.
    Abstract class that provides the base functionality for working with the Arr applications.
    """

    arr_manager: ArrManagerProtocol
    connection_id: int
    inline_trailer: bool
    monitor: MonitorType
    parse_media: Callable[[int, dict[str, Any]], _MediaCreate]

    def __init__(
        self,
        connection: ConnectionRead,
        arr_manager: ArrManagerProtocol,
        parse_media: Callable[[int, dict[str, Any]], _MediaCreate],
        inline_trailer: bool,
    ):
        """Initialize the ArrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        self.connection_id = connection.id
        self.monitor = connection.monitor
        self.arr_manager = arr_manager
        self.parse_media = parse_media
        self.inline_trailer = inline_trailer

    async def get_system_status(self):
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application.
            None: If the system status could not be retrieved."""
        try:
            return await self.arr_manager.get_system_status()
        except Exception:
            return None

    async def get_media_data(self) -> list[dict[str, Any]]:
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
        media_data = await self.get_media_data()
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

    @cache
    def _check_monitoring(
        self, is_new: bool, trailer_exists: bool, arr_monitored: bool
    ) -> bool:
        """Check if the media should be monitored based on the monitor type.\n
        Args:
            is_new (bool): Flag indicating media is newly created in database.
            trailer_exists (bool): Flag indicating if a trailer exists on disk.
            arr_monitored (bool): Flag indicating if media is monitored in Arr application.\n
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
            return arr_monitored
        return False

    @abstractmethod
    def create_or_update_bulk(
        self, media_data: list[_MediaCreate]
    ) -> list[MediaReadDC]:
        """Create or update media in the database and return \
            objects that satisfy MediaReadProtocol.\n
        Args:
            media_data (list[_MediaCreate]): The media data to create or update.\n
        Returns:
            list[MediaReadProtocol]: The media objects that satisfy MediaReadProtocol."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def update_media_status_bulk(self, media_update_list: list[MediaUpdateDC]):
        """Update the media status in the database. \n
        Args:
            media_update_list (list[MediaUpdateDC]): List of media update data."""
        raise NotImplementedError("Subclasses must implement this method")

    async def refresh(self):
        """Gets new data from Arr API and saves it to the database."""
        # Get the parsed data from the Arr API
        parsed_media = await self._parse_data()
        # Create or update the media in the database
        media_res = self.create_or_update_bulk(parsed_media)
        # Check if media has trailer and should be monitored
        update_list: list[MediaUpdateDC] = []
        for media_read in media_res:
            if media_read.folder_path is None:
                trailer_exists = False
            else:
                trailer_exists = await self._check_trailer(media_read.folder_path)
            # Check if monitor is already enabled
            if media_read.monitor:
                monitor_media = True
            else:
                # Else, check if monitor needs to be enabled now
                monitor_media = self._check_monitoring(
                    media_read.created,
                    trailer_exists,
                    media_read.arr_monitored,
                )
            update_list.append(
                MediaUpdateDC(
                    id=media_read.id,
                    monitor=monitor_media,
                    trailer_exists=trailer_exists,
                )
            )
        # Update the database with trailer and monitoring status
        self.update_media_status_bulk(update_list)
        return
