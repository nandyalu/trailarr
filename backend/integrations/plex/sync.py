"""PlexConnectionManager — Plex library sync into the DB.

Ported from backend/core/plex/connection_manager.py with import paths updated.
"""
import os
import re
from difflib import SequenceMatcher
from pathlib import Path

from app_logger import ModuleLogger
import db.repos.connection as connection_repo
import db.repos.media as media_repo
from db.models.connection import ConnectionRead, MonitorType
from db.models.event import EventSource
from integrations.plex.client import PlexAPI
from integrations.plex.models import PlexLibrarySection, PlexMediaItem
from integrations.plex.parser import parse_plex_item
from services import event_service
from utils.path_utils import apply_path_mappings, is_subpath, reverse_path_mappings

logger = ModuleLogger("PlexConnectionManager")

_MOVIE_SECTION_TYPES = {"movie"}
_SHOW_SECTION_TYPES = {"show"}

_SEASON_FOLDER_RE = re.compile(
    r"^(season|series|s|saison|staffel|temporada|stagione|seizoen|säsong|kausi)\s*\d+$"
    r"|^specials?$|^extras?$|^bonus$",
    re.IGNORECASE,
)
_DECORATOR_RE = re.compile(r"\s*[\[{(][^\]})]*[\]})]\s*")


def _normalize_title(name: str) -> str:
    return _DECORATOR_RE.sub(" ", name).strip().lower()


def _resolve_show_root(folder: str, show_title: str) -> str:
    path = Path(folder)
    last = path.name
    if not last:
        return folder
    if _SEASON_FOLDER_RE.match(last):
        return str(path.parent)
    norm_last = _normalize_title(last)
    norm_title = _normalize_title(show_title)
    if norm_title and SequenceMatcher(None, norm_title, norm_last).ratio() >= 0.6:
        return folder
    return folder


class PlexConnectionManager:
    def __init__(self, connection: ConnectionRead):
        self.connection_id = connection.id
        self.connection_name = connection.name
        self.all_path_mappings = connection.path_mappings
        self.path_mappings = [pm for pm in connection.path_mappings if pm.path_from != pm.path_to]
        self.monitor = connection.monitor
        self._stats_added = 0
        self._stats_updated = 0
        self._stats_linked = 0
        self._stats_sections_scanned = 0
        self.api = PlexAPI(
            server_url=connection.url,
            token=connection.api_key,
            identifier=f"trailarr_{connection.id}",
        )
        self.server_url = self.api.server_url

    def _apply_path_mapping(self, path: str) -> str:
        return apply_path_mappings(path, self.path_mappings)

    def _check_monitoring(self) -> bool:
        if self.monitor == MonitorType.MONITOR_NONE:
            return False
        return True

    def _is_in_configured_library(self, plex_folder: str) -> bool:
        for pm in self.all_path_mappings:
            if is_subpath(pm.path_from, plex_folder):
                return True
        return False

    def _section_is_tracked(self, section: PlexLibrarySection) -> bool:
        for pm in self.all_path_mappings:
            for folder in section.folders:
                if is_subpath(pm.path_from, folder):
                    return True
        return False

    def _persist_section_keys(self, section: PlexLibrarySection) -> None:
        for pm in self.all_path_mappings:
            if pm.plex_section_key is not None:
                continue
            for folder in section.folders:
                if is_subpath(pm.path_from, folder):
                    connection_repo.update_path_mapping_section_key(pm.id, section.key)
                    pm.plex_section_key = section.key
                    break

    def _reverse_path_mapping(self, path: str) -> str:
        return reverse_path_mappings(path, self.path_mappings)

    async def _process_item(
        self,
        item: PlexMediaItem,
        section: PlexLibrarySection,
        is_movie: bool,
        plex_folder: str,
    ) -> None:
        if not self.all_path_mappings:
            return
        if plex_folder and not self._is_in_configured_library(plex_folder):
            logger.debug(f"Skipping '{item.title}': folder '{plex_folder}' not under any configured library")
            return

        folder_path = self._apply_path_mapping(plex_folder) if plex_folder else ""
        existing = media_repo.read_by_folder_path(folder_path) if folder_path else None

        if existing:
            newly_linked = existing.plex_connection_id != self.connection_id
            plex_media_filename = (
                item.media_filename if not existing.arr_id and item.media_filename else None
            )
            plex_fields_changed = media_repo.update_plex_fields(
                media_id=existing.id,
                plex_rating_key=item.ratingKey or None,
                plex_section_key=section.key,
                plex_connection_id=self.connection_id,
                media_filename=plex_media_filename,
            )
            if newly_linked:
                event_service.track_plex_linked(
                    media_id=existing.id,
                    connection_name=self.connection_name,
                    plex_rating_key=item.ratingKey or "",
                    source=EventSource.SYSTEM,
                    source_detail="PlexRefresh",
                )
            monitor_changed = False
            if not existing.arr_id and self.monitor != MonitorType.MONITOR_NEW:
                new_monitor = self._check_monitoring()
                if new_monitor != existing.monitor:
                    event_service.track_monitor_changed(
                        media_id=existing.id,
                        old_monitor=existing.monitor,
                        new_monitor=new_monitor,
                        source=EventSource.SYSTEM,
                        source_detail="PlexRefresh",
                    )
                    media_repo.update_monitor_only(existing.id, new_monitor)
                    monitor_changed = True
            if plex_fields_changed or monitor_changed:
                self._stats_updated += 1
            if newly_linked:
                self._stats_linked += 1
        else:
            media_create = parse_plex_item(
                item=item,
                connection_id=self.connection_id,
                section_key=section.key,
                is_movie=is_movie,
                server_url=self.server_url,
            )
            if folder_path:
                media_create.folder_path = folder_path
            media_read = media_repo.create(media_create)
            event_service.track_media_added(
                media=media_read,
                connection_name=self.connection_name,
                source=EventSource.SYSTEM,
                source_detail="PlexRefresh",
            )
            monitor = self._check_monitoring()
            if monitor != media_read.monitor:
                event_service.track_monitor_changed(
                    media_id=media_read.id,
                    old_monitor=media_read.monitor,
                    new_monitor=monitor,
                    source=EventSource.SYSTEM,
                    source_detail="PlexRefresh",
                )
                media_repo.update_monitor_only(media_read.id, monitor)
            self._stats_added += 1

    async def _process_movie_section(self, section: PlexLibrarySection) -> None:
        count = 0
        async for item in self.api.get_library_media(section.key):
            count += 1
            await self._process_item(item, section, is_movie=True, plex_folder=item.media_folder)
        logger.debug(f"Section '{section.title}': {count} movies")

    async def _process_show_section(self, section: PlexLibrarySection) -> None:
        folder_paths: dict[str, list[str]] = {}
        leaf_count = 0
        async for leaf in self.api.get_library_leaves(section.key):
            leaf_count += 1
            if leaf.grandparentRatingKey and leaf.media_folder:
                folder_paths.setdefault(leaf.grandparentRatingKey, [])
                folder_paths[leaf.grandparentRatingKey].append(leaf.media_folder)
        folder_map: dict[str, str] = {}
        for rating_key, paths in folder_paths.items():
            try:
                folder_map[rating_key] = os.path.commonpath(paths)
            except ValueError:
                folder_map[rating_key] = paths[0]
        logger.debug(f"Section '{section.title}': {len(folder_map)} unique shows from {leaf_count} episodes")

        item_count = 0
        async for item in self.api.get_library_media(section.key):
            item_count += 1
            plex_folder = _resolve_show_root(
                folder_map.get(item.ratingKey, item.media_folder), item.title
            )
            await self._process_item(item, section, is_movie=False, plex_folder=plex_folder)
        logger.debug(f"Section '{section.title}': {item_count} show-level items")

    async def _process_section(self, section: PlexLibrarySection) -> None:
        if not self._section_is_tracked(section):
            logger.info(f"Plex section '{section.title}' [{section.key}] has no configured path mappings — skipping.")
            return
        self._persist_section_keys(section)
        self._stats_sections_scanned += 1
        if section.type in _MOVIE_SECTION_TYPES:
            await self._process_movie_section(section)
        elif section.type in _SHOW_SECTION_TYPES:
            await self._process_show_section(section)
        else:
            logger.debug(f"Skipping unsupported section type '{section.type}' (section: {section.title})")

    async def trigger_item_scan(
        self,
        media_id: int,
        section_key: str,
        folder_path: str,
        source: EventSource = EventSource.SYSTEM,
        source_detail: str = "",
    ) -> bool:
        plex_path = self._reverse_path_mapping(folder_path)
        success = await self.api.scan_section_path(section_key, plex_path)
        if success:
            event_service.track_plex_scan_triggered(
                media_id=media_id,
                scan_path=plex_path,
                source=source,
                source_detail=source_detail,
            )
        return success

    async def refresh(self) -> None:
        self._stats_added = 0
        self._stats_updated = 0
        self._stats_linked = 0
        self._stats_sections_scanned = 0
        logger.info(f"Starting Plex refresh for connection '{self.connection_name}'")
        if not self.all_path_mappings:
            logger.warning(
                f"Plex connection '{self.connection_name}' has no library folders configured — skipping refresh."
            )
            return
        sections = await self.api.get_libraries()
        logger.info(f"Found {len(sections)} library sections in '{self.connection_name}'")
        for section in sections:
            try:
                await self._process_section(section)
            except Exception as e:
                logger.error(f"Error processing section '{section.title}': {e}")
        logger.info(
            f"Plex refresh complete for '{self.connection_name}':"
            f" {self._stats_sections_scanned}/{len(sections)} sections scanned,"
            f" {self._stats_added} added, {self._stats_updated} updated,"
            f" {self._stats_linked} newly linked."
        )
