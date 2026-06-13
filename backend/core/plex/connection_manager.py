import asyncio
import os
import re
from difflib import SequenceMatcher
from itertools import batched
from pathlib import Path

from app_logger import ModuleLogger
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.connection import ConnectionRead, MonitorType
from core.base.database.models.event import EventCreate, EventSource, EventType
from core.base.database.models.media import MediaCreate
from core.base.utils.path_utils import apply_path_mappings, is_subpath, reverse_path_mappings
from core.files_handler import FilesHandler
from core.plex.api_manager import PlexAPI
from core.plex.data_parser import parse_plex_item
from core.plex.models import PlexLibrarySection, PlexMediaItem

logger = ModuleLogger("PlexConnectionManager")

_MOVIE_SECTION_TYPES = {"movie"}
_SHOW_SECTION_TYPES = {"show"}

# Matches standard and localized season/special folder names
_SEASON_FOLDER_RE = re.compile(
    r"^(season|series|s|saison|staffel|temporada|stagione|seizoen|säsong|kausi)\s*\d+$"
    r"|^specials?$|^extras?$|^bonus$",
    re.IGNORECASE,
)

# Strips (year), {id-tag}, [id-tag] decorators before fuzzy title comparison
_DECORATOR_RE = re.compile(r"\s*[\[{(][^\]})]*[\]})]\s*")


def _normalize_title(name: str) -> str:
    return _DECORATOR_RE.sub(" ", name).strip().lower()


def _resolve_show_root(folder: str, show_title: str) -> str:
    """Return the true show-root folder, stripping a trailing season directory
    if one is detected.

    Signal 1 — regex: last component matches a known season-folder pattern
    (e.g. 'Season 1', 'S02', 'Staffel 3', 'Specials') → go up one level.

    Signal 2 — fuzzy title match: after stripping year/ID decorators, the
    last component is compared against the show title with SequenceMatcher.
    A ratio ≥ 0.6 means we are already at the show root → return as-is.

    If neither signal fires the folder is returned unchanged; the prefix
    match in read_by_folder_path acts as a safety net.
    """
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
    """Connection manager for the Plex Media Server.

    Unlike the Arr connection managers, Plex does not have a 1-to-1 mapping
    from Plex item to DB Media row driven by an arr_id.  Instead we match by
    folder_path so that Plex data can be layered on top of existing Radarr /
    Sonarr rows (or stand alone when no Arr connection exists).

    Merge rules:
    - Match found by folder_path:
        Update plex_rating_key, plex_section_key, plex_connection_id only.
        All Arr-sourced fields (title, txdb_id, arr_id, etc.) are preserved.
    - No match found:
        Create a new Media row with arr_id=0 and plex_* fields populated.
        connection_id = plex_connection_id = this connection's id.
    """

    def __init__(self, connection: ConnectionRead):
        self.connection_id = connection.id
        self.connection_name = connection.name
        # All path mappings (including identity) — used to decide which
        # Plex libraries are included.  An empty list means "nothing added".
        self.all_path_mappings = connection.path_mappings
        # Non-identity mappings only — used for path translation.
        self.path_mappings = [
            pm for pm in connection.path_mappings if pm.path_from != pm.path_to
        ]
        self.monitor = connection.monitor
        # Refresh-run counters — reset at the start of each refresh() call.
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

    # ------------------------------------------------------------------
    # Path mapping helpers (mirrors BaseConnectionManager)
    # ------------------------------------------------------------------

    def _apply_path_mapping(self, path: str) -> str:
        return apply_path_mappings(path, self.path_mappings)

    def _check_monitoring(self, trailer_exists: bool) -> bool:
        """Return the monitor value for a newly-created Plex-only media item.

        Plex items have no arr_monitored concept; MONITOR_SYNC treats presence
        in the Plex library as implicitly monitored (arr_monitored=True)."""
        if trailer_exists:
            return False
        if self.monitor == MonitorType.MONITOR_NONE:
            return False
        # MONITOR_MISSING, MONITOR_NEW, MONITOR_SYNC all resolve to True:
        # - MISSING: no trailer → monitor
        # - NEW: Plex-only items are always newly created → monitor
        #        Existing items don't call this function since they won't
        #        be re-created → no change
        # - SYNC: Plex library presence = monitored → monitor
        return True

    # ------------------------------------------------------------------
    # Core refresh logic
    # ------------------------------------------------------------------

    def _is_in_configured_library(self, plex_folder: str) -> bool:
        """Return True if *plex_folder* falls under any configured path_from."""
        for pm in self.all_path_mappings:
            if is_subpath(pm.path_from, plex_folder):
                return True
        return False

    def _section_is_tracked(self, section: PlexLibrarySection) -> bool:
        """Return True if any path mapping covers this section's root folders."""
        for pm in self.all_path_mappings:
            for folder in section.folders:
                if is_subpath(pm.path_from, folder):
                    return True
        return False

    def _persist_section_keys(self, section: PlexLibrarySection) -> None:
        """Cache the section key on path mappings that cover this section.

        Only writes to the DB when plex_section_key is still None — a one-time
        operation per mapping so subsequent refreshes skip the write entirely.
        """
        for pm in self.all_path_mappings:
            if pm.plex_section_key is not None:
                continue
            for folder in section.folders:
                if is_subpath(pm.path_from, folder):
                    connection_manager.update_path_mapping_section_key(
                        pm.id, section.key
                    )
                    pm.plex_section_key = section.key
                    break

    def _reverse_path_mapping(self, path: str) -> str:
        """Convert a Trailarr-internal path back to the Plex-side path.

        This is the inverse of ``_apply_path_mapping``: given the ``path_to``
        side of a mapping we return the ``path_from`` (Plex) side.  Used when
        building the path argument for a targeted Plex library scan.
        """
        return reverse_path_mappings(path, self.path_mappings)

    async def _process_item_chunk(
        self,
        chunk: list[tuple[PlexMediaItem, PlexLibrarySection, bool, str]],
    ) -> None:
        """Process a chunk of up to 100 Plex items using bulk DB operations.

        Args:
            chunk: List of (item, section, is_movie, plex_folder) tuples.
                   plex_folder is the raw Plex-side path (before mapping).
        """
        if not chunk:
            return

        # 1. Filter out items not in configured libraries and build MediaCreate list
        parsed: list[tuple[MediaCreate, PlexMediaItem]] = []
        for item, section, is_movie, plex_folder in chunk:
            if plex_folder and not self._is_in_configured_library(plex_folder):
                logger.debug(
                    f"Skipping '{item.title}': folder '{plex_folder}'"
                    " not under any configured library"
                )
                continue
            folder_path = self._apply_path_mapping(plex_folder) if plex_folder else ""
            media_create = parse_plex_item(
                item=item,
                connection_id=self.connection_id,
                section_key=section.key,
                is_movie=is_movie,
                server_url=self.server_url,
            )
            if folder_path:
                media_create.folder_path = folder_path
            parsed.append((media_create, item))

        if not parsed:
            return

        # 2. Bulk create/update — 1 DB session for the whole chunk
        bulk_results = media_manager.plex_create_or_update_bulk(
            [mc for mc, _ in parsed]
        )

        # 3. Collect pending events and identify new items needing file checks
        pending_events: list[EventCreate] = []
        # (media_read, folder_path) for new items — need async file check
        new_items: list[tuple[int, str, bool]] = []  # (id, folder_path, default_monitor)
        # (media_read, plex_fields_changed) for existing items
        existing_items: list[tuple, bool, bool] = []

        for (mc, item), (media_read, created, newly_linked, plex_fields_changed) in zip(
            parsed, bulk_results
        ):
            if newly_linked:
                pending_events.append(
                    EventCreate(
                        media_id=media_read.id,
                        event_type=EventType.PLEX_LINKED,
                        source=EventSource.SYSTEM,
                        source_detail="PlexRefresh",
                        new_value=self.connection_name,
                        old_value=item.ratingKey or "",
                    )
                )
                self._stats_linked += 1

            if created:
                # MEDIA_ADDED
                pending_events.append(
                    EventCreate(
                        media_id=media_read.id,
                        event_type=EventType.MEDIA_ADDED,
                        source=EventSource.SYSTEM,
                        source_detail="PlexRefresh",
                        new_value=self.connection_name,
                    )
                )
                # YOUTUBE_ID_CHANGED (initial, if present)
                if media_read.youtube_trailer_id:
                    pending_events.append(
                        EventCreate(
                            media_id=media_read.id,
                            event_type=EventType.YOUTUBE_ID_CHANGED,
                            source=EventSource.SYSTEM,
                            source_detail="PlexRefresh",
                            old_value="",
                            new_value=media_read.youtube_trailer_id,
                        )
                    )
                # Initial MONITOR_CHANGED (from False default)
                pending_events.append(
                    EventCreate(
                        media_id=media_read.id,
                        event_type=EventType.MONITOR_CHANGED,
                        source=EventSource.SYSTEM,
                        source_detail="PlexRefresh",
                        old_value="",
                        new_value=str(media_read.monitor).lower(),
                    )
                )
                new_items.append(
                    (media_read.id, media_read.folder_path or "", media_read.monitor)
                )
                self._stats_added += 1
            else:
                existing_items.append((media_read, plex_fields_changed))

        # 4. Concurrent async file checks for new items
        update_list: list[tuple[int, bool, bool]] = []

        async def _check_trailer(folder_path: str) -> bool:
            if not folder_path:
                return False
            return await FilesHandler.check_trailer_exists(
                path=folder_path, check_inline_file=True
            )

        if new_items:
            trailer_results = await asyncio.gather(
                *[_check_trailer(fp) for _, fp, _ in new_items]
            )
            for (media_id, folder_path, default_monitor), trailer_exists in zip(
                new_items, trailer_results
            ):
                monitor = self._check_monitoring(trailer_exists)
                if monitor != default_monitor:
                    pending_events.append(
                        EventCreate(
                            media_id=media_id,
                            event_type=EventType.MONITOR_CHANGED,
                            source=EventSource.SYSTEM,
                            source_detail="PlexRefresh",
                            old_value=str(default_monitor).lower(),
                            new_value=str(monitor).lower(),
                        )
                    )
                if trailer_exists:
                    pending_events.append(
                        EventCreate(
                            media_id=media_id,
                            event_type=EventType.TRAILER_DETECTED,
                            source=EventSource.SYSTEM,
                            source_detail="PlexRefresh",
                        )
                    )
                update_list.append((media_id, monitor, trailer_exists))

        # 5. Monitor check for existing Plex-only items
        for media_read, plex_fields_changed in existing_items:
            monitor_changed = False
            if not media_read.arr_id and self.monitor != MonitorType.MONITOR_NEW:
                new_monitor = self._check_monitoring(media_read.trailer_exists)
                if new_monitor != media_read.monitor:
                    pending_events.append(
                        EventCreate(
                            media_id=media_read.id,
                            event_type=EventType.MONITOR_CHANGED,
                            source=EventSource.SYSTEM,
                            source_detail="PlexRefresh",
                            old_value=str(media_read.monitor).lower(),
                            new_value=str(new_monitor).lower(),
                        )
                    )
                    update_list.append(
                        (media_read.id, new_monitor, media_read.trailer_exists)
                    )
                    monitor_changed = True
            if plex_fields_changed or monitor_changed:
                self._stats_updated += 1

        # 6. Bulk update monitor and trailer_exists — 1 DB session
        if update_list:
            media_manager.update_monitor_and_trailer_exists_bulk(update_list)

        # 7. Bulk event insert — 1 DB session
        if pending_events:
            event_manager.create_bulk(pending_events)

    async def _process_movie_section(
        self, section: PlexLibrarySection
    ) -> None:
        """Fetch all movies in a section and merge into the DB in chunks of 100."""
        items: list[tuple[PlexMediaItem, PlexLibrarySection, bool, str]] = []
        async for item in self.api.get_library_media(section.key):
            items.append((item, section, True, item.media_folder))
        for chunk in batched(items, 100):
            await self._process_item_chunk(list(chunk))
        logger.debug(f"Section '{section.title}': {len(items)} movies")

    async def _process_show_section(self, section: PlexLibrarySection) -> None:
        """Fetch all shows in a section and merge into the DB in chunks of 100.

        Uses two endpoints:
        - ``/allLeaves`` → episode file paths → builds a ratingKey→folder map
        - ``/all``       → show-level metadata including TVDB Guid IDs

        The folder map is applied to each show so that folder_path is correctly
        derived from a real episode file rather than the unreliable Location[].path.
        """
        # Step 1: build grandparentRatingKey → show-root-folder from episodes.
        # Collect every episode's parent directory per show, then take the
        # common path — this correctly handles both seasonal and flat layouts.
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
        logger.debug(
            f"Section '{section.title}': {len(folder_map)} unique shows"
            f" from {leaf_count} episodes"
        )

        # Step 2: collect all show items, then process in chunks of 100
        items: list[tuple[PlexMediaItem, PlexLibrarySection, bool, str]] = []
        async for item in self.api.get_library_media(section.key):
            plex_folder = _resolve_show_root(
                folder_map.get(item.ratingKey, item.media_folder),
                item.title,
            )
            items.append((item, section, False, plex_folder))
        for chunk in batched(items, 100):
            await self._process_item_chunk(list(chunk))
        logger.debug(
            f"Section '{section.title}': {len(items)} show-level items"
        )

    async def _process_section(self, section: PlexLibrarySection) -> None:
        """Dispatch to the correct section processor based on library type."""
        if not self._section_is_tracked(section):
            logger.info(
                f"Plex section '{section.title}' [{section.key}] has no"
                " configured path mappings — skipping."
            )
            return
        self._persist_section_keys(section)
        self._stats_sections_scanned += 1
        if section.type in _MOVIE_SECTION_TYPES:
            await self._process_movie_section(section)
        elif section.type in _SHOW_SECTION_TYPES:
            await self._process_show_section(section)
        else:
            logger.debug(
                f"Skipping unsupported section type '{section.type}'"
                f" (section: {section.title})"
            )

    async def trigger_item_scan(
        self,
        media_id: int,
        section_key: str,
        folder_path: str,
        source: EventSource = EventSource.SYSTEM,
        source_detail: str = "",
    ) -> bool:
        """Trigger a targeted Plex file-system scan for a single media item.

        Reverses the path mapping so the path sent to Plex is on the Plex
        side of the mapping (i.e., the path Plex understands).  Fires a
        ``PLEX_SCAN_TRIGGERED`` event on success.

        Args:
            media_id: DB id of the media item (for event tracking).
            section_key: Plex library section key for this item.
            folder_path: Trailarr-internal folder path of the media item.
            source: Event source (USER for manual triggers, SYSTEM for automatic).
            source_detail: Context string stored on the event (e.g. "TrailerDownloaded").

        Returns:
            True if the scan request was accepted by Plex, False otherwise.
        """
        plex_path = self._reverse_path_mapping(folder_path)
        success = await self.api.scan_section_path(section_key, plex_path)
        if success:
            event_manager.track_plex_scan_triggered(
                media_id=media_id,
                scan_path=plex_path,
                source=source,
                source_detail=source_detail,
            )
        return success

    async def refresh(self) -> None:
        """Fetch all Plex libraries and sync them into the database."""
        self._stats_added = 0
        self._stats_updated = 0
        self._stats_linked = 0
        self._stats_sections_scanned = 0
        logger.info(
            f"Starting Plex refresh for connection '{self.connection_name}'"
        )
        if not self.all_path_mappings:
            logger.warning(
                f"Plex connection '{self.connection_name}' has no library"
                " folders configured — skipping refresh (no media will be"
                " added)."
            )
            return
        sections = await self.api.get_libraries()
        logger.info(
            f"Found {len(sections)} library sections in"
            f" '{self.connection_name}'"
        )
        for section in sections:
            try:
                await self._process_section(section)
            except Exception as e:
                logger.error(
                    f"Error processing section '{section.title}': {e}"
                )
        logger.info(
            f"Plex refresh complete for '{self.connection_name}':"
            f" {self._stats_sections_scanned}/{len(sections)} sections scanned,"
            f" {self._stats_added} added,"
            f" {self._stats_updated} updated,"
            f" {self._stats_linked} newly linked."
        )
