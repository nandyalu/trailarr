from abc import ABC
from functools import cache
from itertools import batched
from typing import Any, AsyncGenerator, Callable, Protocol

from app_logger import ModuleLogger
from config.settings import app_settings
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.event import EventSource
from core.base.database.models.helpers import MediaReadDC
from core.base.utils.path_utils import apply_path_mappings
from core.files_handler import FilesHandler
from core.base.database.models.connection import ConnectionRead, MonitorType
from core.base.database.models.media import (
    MediaCreate,
    MediaRead,
)

logger = ModuleLogger("ConnectionManager")


class ArrManagerProtocol(Protocol):
    """Abstract class for getting data from the Arr APIs."""

    async def get_system_status(self) -> str:
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")

    async def get_rootfolders(self) -> list[str]:
        """Get the root folders from the Arr application. \n
        Returns:
            list[str]: The root folders from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")

    async def get_all_media(self) -> list[dict[str, Any]]:
        """Get all media from the Arr application. \n
        Returns:
            list[dict[str, Any]]: The media from the Arr application."""
        raise NotImplementedError("Subclasses must implement this method")


class BaseConnectionManager(ABC):
    """Connection manager for working with the Arr applications.
    Abstract class that provides the base functionality for working with the Arr applications.
    """

    arr_manager: ArrManagerProtocol
    connection_id: int
    # inline_trailer: bool
    is_movie: bool
    monitor: MonitorType
    parse_media: Callable[[int, dict[str, Any]], MediaCreate]

    def __init__(
        self,
        connection: ConnectionRead,
        arr_manager: ArrManagerProtocol,
        parse_media: Callable[[int, dict[str, Any]], MediaCreate],
        # inline_trailer: bool,
        is_movie: bool = True,
    ):
        """Initialize the ArrConnectionManager. \n
        Args:
            connection (ConnectionRead): The connection data."""
        self.connection_id = connection.id
        self.connection_name = connection.name
        self.path_mappings = [
            pm for pm in connection.path_mappings if pm.path_from != pm.path_to
        ]
        self.monitor = connection.monitor
        self.arr_manager = arr_manager
        self.parse_media = parse_media
        # self.inline_trailer = inline_trailer
        self.is_movie = is_movie
        self.created_count = 0
        self.updated_count = 0
        self.media_ids = []

    async def get_system_status(self):
        """Get the system status from the Arr application. \n
        Returns:
            str: The system status from the Arr application.
            None: If the system status could not be retrieved."""
        try:
            return await self.arr_manager.get_system_status()
        except Exception:
            return None

    def _apply_path_mappings_to_path(self, path: str) -> str:
        """Apply the path mappings to the given path. \n
        Args:
            path (str): The path to apply the mappings to. \n
        Returns:
            str: The updated path."""
        return apply_path_mappings(path, self.path_mappings)

    async def get_rootfolders(self) -> list[str]:
        """Get the root folders from the Arr application. \n
        Returns:
            - list[str]: The root folders from the Arr application.
            - An empty list if the root folders could not be retrieved."""
        try:
            rootfolders: list[str] = await self.arr_manager.get_rootfolders()
            # If no path mappings exist, return the rootfolders list as is
            if len(self.path_mappings) == 0:
                return rootfolders
            # Apply path mappings to the rootfolders
            final_rootfolders: list[str] = []
            for rootfolder in rootfolders:
                final_rootfolders.append(
                    self._apply_path_mappings_to_path(rootfolder)
                )
            return final_rootfolders
        except Exception:
            logger.error("Failed to get root folders from Arr application.")
            return []

    async def get_media_data(self) -> list[dict[str, Any]]:
        """Get the data from the Arr application. \n
        Returns:
            - list[dict[str, Any]]: The data from the Arr application.
            - An empty list if the data could not be retrieved."""
        try:
            return await self.arr_manager.get_all_media()
        except Exception:
            logger.error("Failed to get media data from Arr application.")
            return []

    async def _parse_data(self) -> AsyncGenerator[list[MediaCreate], None]:
        """Parse media received from the Arr API to objects that can be added to database.\n
        Yields:
            list[_MediaCreate]: list of parsed media objects in chunks of 100.
        """
        media_data = await self.get_media_data()
        logger.debug(f"Media data received: {len(media_data)} items")
        if not media_data:
            logger.warning("No media data received from Arr application")
            return
        # Parse the media data to MediaCreate objects in chunks of 100
        for chunk in batched(media_data, 100):
            parsed_media: list[MediaCreate] = []
            for media in chunk:
                media_create = self.parse_media(self.connection_id, media)
                parsed_media.append(media_create)
            self._apply_path_mappings(parsed_media)
            yield parsed_media
        return

    def _apply_path_mappings(
        self, media_list: list[MediaCreate]
    ) -> list[MediaCreate]:
        """Update the paths of the media based on the path mappings.\n
        Args:
            media_list (list[MediaCreate]): The list of media objects.\n
        Returns:
            list[MediaCreate]: The updated list of media objects."""
        # If no path mappings exist, return the media list as is
        if len(self.path_mappings) == 0:
            return media_list
        # Loop through the media_list and apply the path mappings
        logger.debug(
            f"Applying path mappings to {len(media_list)} media items"
        )
        for media in media_list:
            if not media.folder_path:
                continue
            media.folder_path = self._apply_path_mappings_to_path(
                media.folder_path
            )
        return media_list

    async def _check_trailer(self, folder_path: str) -> bool:
        """Check if a trailer exists for the media in the folder path.\n
        Args:
            folder_path (str): The folder path to check for the trailer.\n
        Returns:
            bool: True if the trailer exists, False otherwise."""
        # Check if there ia a trailer either inline or in a 'Trailers' subfolder
        trailer_exists = await FilesHandler.check_trailer_exists(
            path=folder_path,
            check_inline_file=True,
        )
        return trailer_exists

    @cache
    def _check_monitoring(
        self, is_new: bool, arr_monitored: bool
    ) -> bool:
        """Check if the media should be monitored based on the monitor type.\n
        Args:
            is_new (bool): Flag indicating media is newly created in database.
            arr_monitored (bool): Flag indicating if media is monitored in Arr application.\n
        Returns:
            bool: True if the media should be monitored, False otherwise."""
        # Disable monitoring if monitor is set to none
        if self.monitor == MonitorType.MONITOR_NONE:
            return False
        # Monitor trailers if set to monitor missing (always monitor)
        if self.monitor == MonitorType.MONITOR_MISSING:
            return True
        # Monitor trailers if set to monitor new
        if self.monitor == MonitorType.MONITOR_NEW:
            return is_new
        # Sync monitor based on arr monitor status
        if self.monitor == MonitorType.MONITOR_SYNC:
            return arr_monitored
        return False

    def create_or_update_bulk(
        self, media_data: list[MediaCreate]
    ) -> list[MediaReadDC]:
        """Create or update media in the database and return MediaRead objects.\n
        Args:
            media_data (list[MovieCreate]): The movie data to create or update.\n
        Returns:
            list[MediaReadDC]: A list of MediaRead objects."""
        media_read_list = media_manager.create_or_update_bulk(media_data)
        media_read_dc_list = []
        for media_read, created, updated, arr_linked in media_read_list:
            self.media_ids.append(media_read.id)
            if created:
                self.created_count += 1
                # Track all events for new media (added, youtube_id, monitor)
                event_manager.track_media_added(
                    media=media_read,
                    connection_name=self.connection_name,
                    source=EventSource.SYSTEM,
                    source_detail="ConnectionRefresh",
                )
            if arr_linked:
                event_manager.track_arr_linked(
                    media_id=media_read.id,
                    connection_name=self.connection_name,
                    source=EventSource.SYSTEM,
                    source_detail="ConnectionRefresh",
                )
            if updated:
                self.updated_count += 1
            media_read_dc = MediaReadDC(
                **media_read.model_dump(), created=created
            )
            media_read_dc_list.append(media_read_dc)
        return media_read_dc_list

    async def delete_trailers_for_media(self, media: MediaRead) -> bool:
        """Delete trailers for a media item.\n
        - If `app_settings.delete_trailer_media` is True, check if media files exist on disk.
        Args:
            media (MediaRead): The media item.\n
        Returns:
            bool: True if the trailers were deleted, False otherwise."""
        if app_settings.delete_trailer_media:
            if not media.folder_path:
                return False
            if FilesHandler.check_media_exists(media.folder_path):
                # Media files still exist on disk, nothing to delete
                return False
        # Delete download files associated with the media
        _deleted = False
        for download in media.downloads:
            if not download.file_exists:
                continue
            if not download.path:
                continue
            if await FilesHandler.delete_file(download.path):
                _deleted = True
                logger.info(
                    f"Media '{media.title}' removed from Arr application."
                    f" Deleted trailer file '{download.path}'"
                )
            else:
                logger.warning(
                    f"Media '{media.title}' removed from Arr application."
                    f" Failed to delete trailer file '{download.path}'"
                )
        if not media.folder_path:
            return _deleted
        # Delete trailers from media folder and 'Trailers' subfolder if exists
        _deleted = _deleted or await FilesHandler.delete_trailers_for_media(
            media.folder_path
        )
        return _deleted

    async def delete_removed_media_trailers(self) -> None:
        """Delete trailers for media that have been removed from the Arr application."""
        if len(self.media_ids) == 0:
            # If no media IDs exist, avoid deleting all trailers
            return
        logger.debug(
            "Deleting trailers for media removed from Connection"
            f" '{self.connection_name}' (ID: {self.connection_id})"
        )
        all_media = media_manager.read_all_by_connection(self.connection_id)
        ids_to_keep = set(self.media_ids)
        for media in all_media:
            if media.id in ids_to_keep:
                continue
            # Delete download files associated with the media
            await self.delete_trailers_for_media(media)
        return

    def remove_media_deleted_in_arr_from_db(self) -> None:
        """Remove the media from the database that are not present in the Arr application."""
        if len(self.media_ids) == 0:
            return
        logger.debug("Removing media not present in Arr application")
        # Demote Plex-linked items back to Plex-only instead of deleting them.
        demoted_ids = media_manager.demote_arr_items_with_plex_to_plex_only(
            self.connection_id, self.media_ids
        )
        for media_id in demoted_ids:
            event_manager.track_arr_unlinked(
                media_id=media_id,
                connection_name=self.connection_name,
                source=EventSource.SYSTEM,
                source_detail="ConnectionRefresh",
            )
        media_manager.delete_except(self.connection_id, self.media_ids)
        return

    async def _process_media_list(self, parsed_media: list[MediaCreate]):
        """Process the media list and update the database with the new data.\n
        Args:
            parsed_media (list[MediaCreate]): The parsed media data."""
        if len(parsed_media) == 0:
            logger.debug("No media to process")
            return
        # Create or update the media in the database
        media_res = self.create_or_update_bulk(parsed_media)
        # Determine monitoring status and build update list
        update_list: list[tuple[int, bool, bool]] = []
        for media_read in media_res:
            # Keep existing monitor status unless we need to set it on new items
            if media_read.monitor:
                monitor_media = True
            else:
                monitor_media = self._check_monitoring(
                    media_read.created,
                    media_read.arr_monitored,
                )
            # Track monitor change event if monitor status changed
            if monitor_media != media_read.monitor:
                event_manager.track_monitor_changed(
                    media_id=media_read.id,
                    old_monitor=media_read.monitor,
                    new_monitor=monitor_media,
                    source=EventSource.SYSTEM,
                    source_detail="ConnectionRefresh",
                )
            # Pass False as the trailer_exists placeholder (ignored by bulk update)
            update_list.append((media_read.id, monitor_media, False))
        # Update the database with monitoring status
        media_manager.update_monitor_and_trailer_exists_bulk(update_list)
        return

    async def refresh(self):
        """Gets new data from Arr API and saves it to the database."""
        # Get the parsed data from the Arr API
        # parsed_media = await self._parse_data()
        async for parsed_media in self._parse_data():
            # Process the media list
            await self._process_media_list(parsed_media)
        media_type = "Movies" if self.is_movie else "Series"
        logger.info(
            f"{media_type}: {self.created_count} created,"
            f" {self.updated_count} updated."
        )

        # Delete any trailer content for media removed from Arr
        if app_settings.delete_trailer_connection:
            await self.delete_removed_media_trailers()

        # Delete any media that is not present in the Arr application
        self.remove_media_deleted_in_arr_from_db()
        return
