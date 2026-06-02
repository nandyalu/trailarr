"""BaseConnectionManager — Arr/Plex refresh orchestration.

Ported from backend/core/base/connection_manager.py with import paths updated.
This class handles the full refresh cycle: parse → upsert → monitor → clean up.
Actual Arr/Plex API clients live in integrations/.
"""
from abc import ABC
from functools import cache
from itertools import batched
from typing import Any, AsyncGenerator, Callable

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.connection import ConnectionRead, MonitorType
from db.models.event import EventSource
from db.models.helpers import MediaReadDC
from db.models.media import MediaCreate, MediaRead
import db.repos.media as media_repo
from services import event_service
from services.files_service import FilesHandler
from utils.path_utils import apply_path_mappings

logger = ModuleLogger("ConnectionManager")


class BaseConnectionManager(ABC):
    arr_manager: Any
    connection_id: int
    is_movie: bool
    monitor: MonitorType
    parse_media: Callable[[int, dict[str, Any]], MediaCreate]

    def __init__(
        self,
        connection: ConnectionRead,
        arr_manager: Any,
        parse_media: Callable[[int, dict[str, Any]], MediaCreate],
        is_movie: bool = True,
    ):
        self.connection_id = connection.id
        self.connection_name = connection.name
        self.path_mappings = [pm for pm in connection.path_mappings if pm.path_from != pm.path_to]
        self.monitor = connection.monitor
        self.arr_manager = arr_manager
        self.parse_media = parse_media
        self.is_movie = is_movie
        self.created_count = 0
        self.updated_count = 0
        self.media_ids: list[int] = []

    async def get_system_status(self) -> str | None:
        try:
            return await self.arr_manager.get_system_status()
        except Exception:
            return None

    def _apply_path_mappings_to_path(self, path: str) -> str:
        return apply_path_mappings(path, self.path_mappings)

    async def get_rootfolders(self) -> list[str]:
        try:
            rootfolders: list[str] = await self.arr_manager.get_rootfolders()
            if not self.path_mappings:
                return rootfolders
            return [self._apply_path_mappings_to_path(rf) for rf in rootfolders]
        except Exception:
            logger.error("Failed to get root folders from Arr application.")
            return []

    async def get_media_data(self) -> list[dict[str, Any]]:
        try:
            return await self.arr_manager.get_all_media()
        except Exception:
            logger.error("Failed to get media data from Arr application.")
            return []

    async def _parse_data(self) -> AsyncGenerator[list[MediaCreate], None]:
        media_data = await self.get_media_data()
        logger.debug(f"Media data received: {len(media_data)} items")
        if not media_data:
            logger.warning("No media data received from Arr application")
            return
        for chunk in batched(media_data, 100):
            parsed_media: list[MediaCreate] = []
            for media in chunk:
                media_create = self.parse_media(self.connection_id, media)
                parsed_media.append(media_create)
            self._apply_path_mappings(parsed_media)
            yield parsed_media

    def _apply_path_mappings(self, media_list: list[MediaCreate]) -> list[MediaCreate]:
        if not self.path_mappings:
            return media_list
        for media in media_list:
            if media.folder_path:
                media.folder_path = self._apply_path_mappings_to_path(media.folder_path)
        return media_list

    async def _check_trailer(self, folder_path: str) -> bool:
        return await FilesHandler.check_trailer_exists(path=folder_path, check_inline_file=True)

    @cache
    def _check_monitoring(self, is_new: bool, arr_monitored: bool) -> bool:
        if self.monitor == MonitorType.MONITOR_NONE:
            return False
        if self.monitor == MonitorType.MONITOR_MISSING:
            return True
        if self.monitor == MonitorType.MONITOR_NEW:
            return is_new
        if self.monitor == MonitorType.MONITOR_SYNC:
            return arr_monitored
        return False

    def create_or_update_bulk(self, media_data: list[MediaCreate]) -> list[MediaReadDC]:
        import db.repos.video_id as video_id_repo
        results = media_repo.create_or_update_bulk(media_data)
        media_read_dc_list = []
        for media_read, created, updated, arr_linked, old_season_count in results:
            self.media_ids.append(media_read.id)
            if created:
                self.created_count += 1
                event_service.track_media_added(
                    media=media_read,
                    connection_name=self.connection_name,
                    source=EventSource.SYSTEM,
                    source_detail="ConnectionRefresh",
                )
            if arr_linked:
                event_service.track_arr_linked(
                    media_id=media_read.id,
                    connection_name=self.connection_name,
                    source=EventSource.SYSTEM,
                    source_detail="ConnectionRefresh",
                )
            if updated:
                self.updated_count += 1
            # Upsert Arr-provided YouTube trailer ID into VideoId table
            if media_read.youtube_trailer_id:
                video_id_repo.upsert_arr(media_read.id, media_read.youtube_trailer_id)
            media_read_dc_list.append(MediaReadDC(**media_read.model_dump(), created=created))
        return media_read_dc_list

    async def delete_trailers_for_media(self, media: MediaRead) -> bool:
        if app_settings.delete_trailer_media:
            if not media.folder_path:
                return False
            if FilesHandler.check_media_exists(media.folder_path):
                return False
        deleted = False
        for download in media.downloads:
            if not download.file_exists or not download.path:
                continue
            if await FilesHandler.delete_file(download.path):
                deleted = True
                logger.info(f"Media '{media.title}' removed — deleted trailer '{download.path}'")
            else:
                logger.warning(f"Media '{media.title}' removed — failed to delete '{download.path}'")
        if not media.folder_path:
            return deleted
        deleted = deleted or await FilesHandler.delete_trailers_for_media(media.folder_path)
        return deleted

    async def delete_removed_media_trailers(self) -> None:
        if not self.media_ids:
            return
        logger.debug(f"Deleting trailers for media removed from Connection '{self.connection_name}'")
        all_media = media_repo.read_all_by_connection(self.connection_id)
        ids_to_keep = set(self.media_ids)
        for media in all_media:
            if media.id not in ids_to_keep:
                await self.delete_trailers_for_media(media)

    def remove_media_deleted_in_arr_from_db(self) -> None:
        if not self.media_ids:
            return
        logger.debug("Removing media not present in Arr application")
        demoted_ids = media_repo.demote_arr_items_with_plex_to_plex_only(self.connection_id, self.media_ids)
        for media_id in demoted_ids:
            event_service.track_arr_unlinked(
                media_id=media_id,
                connection_name=self.connection_name,
                source=EventSource.SYSTEM,
                source_detail="ConnectionRefresh",
            )
        media_repo.delete_except(self.connection_id, self.media_ids)

    async def _process_media_list(self, parsed_media: list[MediaCreate]) -> None:
        if not parsed_media:
            return
        media_res = self.create_or_update_bulk(parsed_media)
        update_list: list[tuple[int, bool, bool]] = []
        for media_read in media_res:
            if media_read.monitor:
                monitor_media = True
            elif media_read.created or self.monitor == MonitorType.MONITOR_SYNC:
                # New items: apply the connection's monitoring rule.
                # SYNC: always mirror Arr's monitored flag, even on existing items.
                monitor_media = self._check_monitoring(media_read.created, media_read.arr_monitored)
            else:
                # Existing item already unmonitored: preserve False.
                # MONITOR_MISSING would otherwise re-enable it on every refresh.
                monitor_media = False
            if monitor_media != media_read.monitor:
                event_service.track_monitor_changed(
                    media_id=media_read.id,
                    old_monitor=media_read.monitor,
                    new_monitor=monitor_media,
                    source=EventSource.SYSTEM,
                    source_detail="ConnectionRefresh",
                )
            update_list.append((media_read.id, monitor_media, False))
        media_repo.update_monitor_and_trailer_exists_bulk(update_list)

    async def refresh(self) -> None:
        async for parsed_media in self._parse_data():
            await self._process_media_list(parsed_media)
        media_type = "Movies" if self.is_movie else "Series"
        logger.info(f"{media_type}: {self.created_count} created, {self.updated_count} updated.")
        if app_settings.delete_trailer_connection:
            await self.delete_removed_media_trailers()
        self.remove_media_deleted_in_arr_from_db()
