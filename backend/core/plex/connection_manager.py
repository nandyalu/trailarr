import os
import re
from collections import Counter
from pathlib import Path

from app_logger import ModuleLogger
from config.settings import app_settings
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
from core.base.connection_manager import delete_trailers_for_removed_media
from core.base.database.models.connection import ConnectionRead
from core.base.database.models.event import EventCreate, EventSource, EventType
from core.base.database.models.media import MediaCreate, MediaRead
from core.base.utils.path_utils import (
    apply_path_mappings,
    is_subpath,
    reverse_path_mappings,
)
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

def _resolve_show_root(folder: str) -> str:
    """Return the show-root folder. Strip a trailing season directory
    if one is detected.

    When the last component matches a known season-folder pattern
    (e.g. 'Season 1', 'S02', 'Staffel 3', 'Specials'), go up one level.

    Otherwise the folder is returned unchanged; the prefix match in
    read_by_folder_path acts as a safety net.
    """
    path = Path(folder)
    last = path.name
    if not last:
        return folder
    if _SEASON_FOLDER_RE.match(last):
        return str(path.parent)
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
        self.monitor_new_media = connection.monitor_new_media
        # Refresh-run counters — reset at the start of each refresh() call.
        self._stats_added = 0
        self._stats_updated = 0
        self._stats_linked = 0
        self._stats_sections_scanned = 0
        self._sections_failed = 0
        # Media ids seen during the current refresh — used afterwards to
        # remove items that are no longer in the Plex library.
        self.media_ids: list[int] = []
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

    # ------------------------------------------------------------------
    # Core refresh logic
    # ------------------------------------------------------------------

    def _is_in_configured_library(self, plex_folder: str) -> bool:
        """Return True if *plex_folder* falls under any configured path_from."""
        for pm in self.all_path_mappings:
            if is_subpath(pm.path_from, plex_folder):
                return True
        return False

    def _is_at_or_above_library_root(self, plex_folder: str) -> bool:
        """Return True if *plex_folder* is a configured library root or a
        parent of one.

        A media folder must always be deeper than the library root. A folder
        at or above the root would claim the whole library as one media item.
        """
        if not plex_folder:
            return False
        for pm in self.all_path_mappings:
            if is_subpath(plex_folder, pm.path_from):
                return True
        return False

    def _derive_show_folder(self, paths: list[str], title: str) -> str:
        """Derive the show-root folder from episode parent directories.

        Primary signal: the common path of all episode directories,
        season-stripped. This handles seasonal and flat layouts.

        When episodes live in more than one show folder (e.g. a stale
        duplicate folder), the common path collapses to the library root.
        In that case, fall back to a majority vote over the per-episode
        show-root candidates so one stray folder cannot poison the result.

        Returns an empty string when no safe folder can be derived.
        """
        try:
            common = os.path.commonpath(paths)
        except ValueError:
            common = paths[0]
        folder = _resolve_show_root(common)
        if not self._is_at_or_above_library_root(folder):
            return folder
        candidates = Counter(
            c
            for c in (_resolve_show_root(p) for p in paths)
            if not self._is_at_or_above_library_root(c)
        )
        if not candidates:
            return ""
        best, count = candidates.most_common(1)[0]
        logger.warning(
            f"Show '{title}': episode folders do not share one show root"
            f" (common path '{common}' is at or above the library root)."
            f" Selected '{best}' ({count}/{len(paths)} episodes). Check the"
            " show for stray or duplicate folders in Plex."
        )
        return best

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
            if pm.plex_section_key is not None or pm.id is None:
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
            # Safety net: never store a library root as a media folder. A
            # root folder would match every media item under it and adopt
            # their files and trailers.
            if plex_folder and self._is_at_or_above_library_root(plex_folder):
                logger.warning(
                    f"Skipping '{item.title}': derived folder '{plex_folder}'"
                    " is at or above a library root. Cannot track this item"
                    " safely."
                )
                continue
            folder_path = (
                self._apply_path_mapping(plex_folder) if plex_folder else ""
            )
            media_create = parse_plex_item(
                item=item,
                connection_id=self.connection_id,
                section_key=section.key,
                is_movie=is_movie,
                server_url=self.server_url,
            )
            if folder_path:
                media_create.folder_path = folder_path
            # Phase 4: monitor is user intent — the connection default is
            # applied ONCE at creation (the plex bulk upsert never writes
            # monitor on existing rows).
            media_create.monitor = self.monitor_new_media
            parsed.append((media_create, item))

        if not parsed:
            return

        # 2. Bulk create/update — 1 DB session for the whole chunk
        bulk_results = media_manager.plex_create_or_update_bulk(
            [mc for mc, _ in parsed]
        )

        # 3. Collect pending events
        pending_events: list[EventCreate] = []
        # (media_read, plex_fields_changed) for existing items
        existing_items: list[tuple[MediaRead, bool]] = []

        for (mc, item), (
            media_read,
            created,
            newly_linked,
            plex_fields_changed,
        ) in zip(parsed, bulk_results):
            if media_read.id:
                self.media_ids.append(media_read.id)
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
                # Initial MONITOR_CHANGED — records the creation default
                # (monitor_new_media); syncs never change monitor afterwards
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
                self._stats_added += 1
            else:
                existing_items.append((media_read, plex_fields_changed))

        # 4. Stats for existing items (Phase 4: no monitor re-evaluation.
        # Phase 5: no disk trailer checks here either — the files scan owns
        # trailer detection and records download rows for it.)
        for media_read, plex_fields_changed in existing_items:
            if plex_fields_changed:
                self._stats_updated += 1

        # 5. Bulk event insert — 1 DB session
        if pending_events:
            event_manager.create_bulk(pending_events)

    async def _process_movie_section(
        self, section: PlexLibrarySection
    ) -> None:
        """Fetch all movies in a section and merge into the DB in chunks of 100."""
        buffer: list[tuple[PlexMediaItem, PlexLibrarySection, bool, str]] = []
        count = 0
        async for item in self.api.get_library_media(section.key):
            buffer.append((item, section, True, item.media_folder))
            count += 1
            if len(buffer) >= 100:
                await self._process_item_chunk(buffer)
                buffer = []
        if buffer:
            await self._process_item_chunk(buffer)
        logger.debug(f"Section '{section.title}': {count} movies")

    async def _process_show_section(self, section: PlexLibrarySection) -> None:
        """Fetch all shows in a section and merge into the DB in chunks of 100.

        Uses two endpoints:
        - ``/allLeaves`` → episode file paths → builds a ratingKey→folder map
        - ``/all``       → show-level metadata including TVDB Guid IDs

        The folder map is applied to each show so that folder_path is correctly
        derived from a real episode file rather than the unreliable Location[].path.
        """
        # Step 1: collect every episode's parent directory per show
        # (grandparentRatingKey). The show root is derived from these in
        # step 2. The same pass collects each show's distinct season
        # numbers, so a season count is available for Plex-only series
        # (Specials/season 0 are excluded to match Sonarr's seasonCount
        # semantics).
        folder_paths: dict[str, list[str]] = {}
        season_numbers: dict[str, set[int]] = {}
        leaf_count = 0
        async for leaf in self.api.get_library_leaves(section.key):
            leaf_count += 1
            if leaf.grandparentRatingKey and leaf.media_folder:
                folder_paths.setdefault(leaf.grandparentRatingKey, [])
                folder_paths[leaf.grandparentRatingKey].append(
                    leaf.media_folder
                )
            if leaf.grandparentRatingKey and leaf.parentIndex > 0:
                season_numbers.setdefault(
                    leaf.grandparentRatingKey, set()
                ).add(leaf.parentIndex)
        logger.debug(
            f"Section '{section.title}': {len(folder_paths)} unique shows"
            f" from {leaf_count} episodes"
        )

        # Step 2: process show items in chunks of 100 incrementally
        buffer: list[tuple[PlexMediaItem, PlexLibrarySection, bool, str]] = []
        total = 0
        async for item in self.api.get_library_media(section.key):
            paths = folder_paths.get(item.ratingKey)
            if paths:
                plex_folder = self._derive_show_folder(paths, item.title)
                if not plex_folder:
                    logger.warning(
                        f"Skipping show '{item.title}': no safe show folder"
                        " can be derived from its episode folders."
                    )
                    continue
            else:
                # No episode files — fall back to the show's Location path.
                plex_folder = _resolve_show_root(item.media_folder)
            item.season_count = len(season_numbers.get(item.ratingKey, ()))
            buffer.append((item, section, False, plex_folder))
            total += 1
            if len(buffer) >= 100:
                await self._process_item_chunk(buffer)
                buffer = []
        if buffer:
            await self._process_item_chunk(buffer)
        logger.debug(f"Section '{section.title}': {total} show-level items")

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
        rating_key: str | None = None,
        source: EventSource = EventSource.SYSTEM,
        source_detail: str = "",
    ) -> bool:
        """Make a media item's new files visible in Plex.

        Reverses the path mapping so the path sent to Plex is on the Plex
        side of the mapping (i.e., the path Plex understands), then does
        two things:

        1. Scans the folder, so Plex indexes the new files.
        2. Refreshes the item's metadata when *rating_key* is known.

        Both are needed: a folder scan alone indexes the file but leaves
        a local extra (a downloaded trailer) invisible on the item, and
        the metadata refresh is what attaches it. This is one operation
        for the user, so it fires one ``PLEX_SCAN_TRIGGERED`` event.

        Args:
            media_id: DB id of the media item (for event tracking).
            section_key: Plex library section key for this item.
            folder_path: Trailarr-internal folder path of the media item.
            rating_key: Plex ratingKey of the item, when it is linked.
                Without it, only the folder scan runs.
            source: Event source (USER for manual triggers, SYSTEM for automatic).
            source_detail: Context string stored on the event (e.g. "TrailerDownloaded").

        Returns:
            True if the scan request was accepted by Plex, False otherwise.
        """
        plex_path = self._reverse_path_mapping(folder_path)
        success = await self.api.scan_section_path(section_key, plex_path)
        if rating_key:
            await self.api.refresh_item(rating_key)
        if success:
            event_manager.track_plex_scan_triggered(
                media_id=media_id,
                scan_path=plex_path,
                source=source,
                source_detail=source_detail,
            )
        return success

    async def _remove_media_deleted_in_plex(self) -> None:
        """Remove media that are no longer present in the Plex library.

        The mirror of the Arr-side `remove_media_deleted_in_arr_from_db`:
        - Arr-sourced rows that lost their Plex presence only lose their
          `plex_*` fields (PLEX_UNLINKED) — Radarr/Sonarr still owns them.
        - Plex-only rows are deleted, with trailer-file cleanup when the
          `delete_trailer_connection` setting is on.
        """
        if self._sections_failed:
            logger.warning(
                f"Plex connection '{self.connection_name}':"
                f" {self._sections_failed} section(s) failed to process —"
                " skipping removal of missing media this run."
            )
            return
        if len(self.media_ids) == 0:
            # If no media IDs exist, avoid deleting all media
            return
        # Unlink Arr-sourced rows that are gone from the Plex library
        unlinked_ids = media_manager.unlink_plex_missing_items(
            self.connection_id, self.media_ids
        )
        for media_id in unlinked_ids:
            event_manager.track_plex_unlinked(
                media_id=media_id,
                connection_name=self.connection_name,
                source=EventSource.SYSTEM,
                source_detail="PlexRefresh",
            )
        # Delete trailer files for Plex-only rows that are being removed
        if app_settings.delete_trailer_connection:
            all_media = media_manager.read_all_by_connection(
                self.connection_id
            )
            ids_to_keep = set(self.media_ids)
            for media in all_media:
                if media.id in ids_to_keep:
                    continue
                await delete_trailers_for_removed_media(media, "Plex library")
        # Delete Plex-only rows that are not in the Plex library anymore
        media_manager.delete_except(self.connection_id, self.media_ids)

    async def refresh(self) -> None:
        """Fetch all Plex libraries and sync them into the database."""
        self._stats_added = 0
        self._stats_updated = 0
        self._stats_linked = 0
        self._stats_sections_scanned = 0
        self._sections_failed = 0
        self.media_ids = []
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
                self._sections_failed += 1
                logger.error(
                    f"Error processing section '{section.title}': {e}"
                )
        # Remove media that disappeared from the Plex library. Skipped
        # when any section failed — a partial sync must not delete media.
        await self._remove_media_deleted_in_plex()
        logger.info(
            f"Plex refresh complete for '{self.connection_name}':"
            f" {self._stats_sections_scanned}/{len(sections)} sections"
            f" scanned, {self._stats_added} added, {self._stats_updated}"
            f" updated, {self._stats_linked} newly linked."
        )
