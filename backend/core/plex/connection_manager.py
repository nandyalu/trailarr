import os
import re
from difflib import SequenceMatcher
from pathlib import Path

from app_logger import ModuleLogger
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.connection import ConnectionRead, MonitorType
from core.base.database.models.event import EventSource
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
        if not path:
            return path
        for pm in self.path_mappings:
            if path.startswith(pm.path_from):
                path = path.replace(pm.path_from, pm.path_to)
                break
            _from = pm.path_from.rstrip("/").rstrip("\\")
            _to = pm.path_to.rstrip("/").rstrip("\\")
            if path.startswith(_from):
                path = path.replace(_from, _to)
                break
        return path.replace("\\", "/")

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
            if plex_folder.startswith(pm.path_from):
                return True
        return False

    def _reverse_path_mapping(self, path: str) -> str:
        """Convert a Trailarr-internal path back to the Plex-side path.

        This is the inverse of ``_apply_path_mapping``: given the ``path_to``
        side of a mapping we return the ``path_from`` (Plex) side.  Used when
        building the path argument for a targeted Plex library scan.
        """
        if not path:
            return path
        for pm in self.path_mappings:
            if path.startswith(pm.path_to):
                return path.replace(pm.path_to, pm.path_from, 1).replace(
                    "\\", "/"
                )
            _to = pm.path_to.rstrip("/").rstrip("\\")
            _from = pm.path_from.rstrip("/").rstrip("\\")
            if path.startswith(_to):
                return path.replace(_to, _from, 1).replace("\\", "/")
        return path

    async def _process_item(
        self,
        item: PlexMediaItem,
        section: PlexLibrarySection,
        is_movie: bool,
        plex_folder: str,
    ) -> None:
        """Merge or create a single media item from a Plex library section."""
        if not self.all_path_mappings:
            return
        if plex_folder and not self._is_in_configured_library(plex_folder):
            logger.debug(
                f"Skipping '{item.title}': folder '{plex_folder}'"
                " not under any configured library"
            )
            return

        folder_path = (
            self._apply_path_mapping(plex_folder) if plex_folder else ""
        )

        existing = None
        if folder_path:
            existing = media_manager.read_by_folder_path(folder_path)

        if existing:
            # Only fire PLEX_LINKED when this row wasn't already linked to this
            # connection — avoids a noisy event on every routine refresh.
            newly_linked = existing.plex_connection_id != self.connection_id
            # For Plex-only items (arr_id=0), keep media_filename in sync with
            # what Plex reports. Arr-linked rows leave this to the Arr refresh.
            # Only pass when non-empty so a show-level item (no Media Part) never
            # blanks out a previously correct value.
            plex_media_filename = (
                item.media_filename
                if not existing.arr_id and item.media_filename
                else None
            )
            media_manager.update_plex_fields(
                media_id=existing.id,
                plex_rating_key=item.ratingKey or None,
                plex_section_key=section.key,
                plex_connection_id=self.connection_id,
                media_filename=plex_media_filename,
            )
            if newly_linked:
                event_manager.track_plex_linked(
                    media_id=existing.id,
                    connection_name=self.connection_name,
                    plex_rating_key=item.ratingKey or "",
                    source=EventSource.SYSTEM,
                    source_detail="PlexRefresh",
                )
            # Re-evaluate monitor only for Plex-only items — Arr-linked items
            # have their monitor state owned by the Arr connection.
            # MONITOR_NEW only affects newly-created items — preserve existing state.
            if not existing.arr_id and self.monitor != MonitorType.MONITOR_NEW:
                new_monitor = self._check_monitoring(existing.trailer_exists)
                if new_monitor != existing.monitor:
                    event_manager.track_monitor_changed(
                        media_id=existing.id,
                        old_monitor=existing.monitor,
                        new_monitor=new_monitor,
                        source=EventSource.SYSTEM,
                        source_detail="PlexRefresh",
                    )
                    media_manager.update_monitor_and_trailer_exists_bulk(
                        [(existing.id, new_monitor, existing.trailer_exists)]
                    )
            logger.debug(
                f"Merged Plex data for '{existing.title}' (id={existing.id})"
            )
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
            media_read = media_manager.create(media_create)
            event_manager.track_media_added(
                media=media_read,
                connection_name=self.connection_name,
                source=EventSource.SYSTEM,
                source_detail="PlexRefresh",
            )
            # Check trailer and apply monitoring logic for Plex-only items
            trailer_exists = False
            if media_read.folder_path:
                trailer_exists = await FilesHandler.check_trailer_exists(
                    path=media_read.folder_path,
                    check_inline_file=True,
                )
            monitor = self._check_monitoring(trailer_exists)
            if monitor != media_read.monitor:
                event_manager.track_monitor_changed(
                    media_id=media_read.id,
                    old_monitor=media_read.monitor,
                    new_monitor=monitor,
                    source=EventSource.SYSTEM,
                    source_detail="PlexRefresh",
                )
            if trailer_exists and not media_read.trailer_exists:
                event_manager.track_trailer_detected(
                    media_id=media_read.id,
                    source=EventSource.SYSTEM,
                    source_detail="PlexRefresh",
                )
            media_manager.update_monitor_and_trailer_exists_bulk(
                [(media_read.id, monitor, trailer_exists)]
            )
            logger.debug(f"Created new Plex-only media row for '{item.title}'")

    async def _process_movie_section(
        self, section: PlexLibrarySection
    ) -> None:
        """Fetch all movies in a section and merge into the DB."""
        count = 0
        async for item in self.api.get_library_media(section.key):
            count += 1
            await self._process_item(
                item, section, is_movie=True, plex_folder=item.media_folder
            )
        logger.debug(f"Section '{section.title}': {count} movies")

    async def _process_show_section(self, section: PlexLibrarySection) -> None:
        """Fetch all shows in a section and merge into the DB.

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

        # Step 2: process show-level items (contain TVDB/TMDB Guid IDs)
        item_count = 0
        async for item in self.api.get_library_media(section.key):
            item_count += 1
            # Prefer folder derived from episode files; fall back to Location path.
            # Then resolve the true show root (strips trailing season dirs).
            plex_folder = _resolve_show_root(
                folder_map.get(item.ratingKey, item.media_folder),
                item.title,
            )
            await self._process_item(
                item, section, is_movie=False, plex_folder=plex_folder
            )
        logger.debug(
            f"Section '{section.title}': {item_count} show-level items"
        )

    async def _process_section(self, section: PlexLibrarySection) -> None:
        """Dispatch to the correct section processor based on library type."""
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
            f"Plex refresh completed for connection '{self.connection_name}'"
        )
