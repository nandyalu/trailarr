"""Integration test: PlexConnectionManager with a large library (1500 movies + 160 series).

Verifies that:
 - The sync completes without raising any exceptions (including QueuePool exhaustion).
 - All 1500 movie and 160 series rows are created in the DB.
 - MEDIA_ADDED events are created for every item.
 - A second sync over the same library updates plex fields without re-creating rows.

Uses a per-run UUID path prefix so the persistent test DB never produces false
folder-path collisions with items left over from previous test runs.
"""

import uuid

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from sqlmodel import Session, select

from core.base.database.models.connection import ArrType, Connection, MonitorType
from core.base.database.models.event import Event, EventType
from core.base.database.models.media import Media
from core.base.database.utils.engine import get_session, write_session
from core.files_handler import FilesHandler
from core.plex.api_manager import PlexAPI
from core.plex.connection_manager import PlexConnectionManager
from core.plex.models import PlexEpisodeLeaf, PlexLibrarySection, PlexMediaItem


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

@write_session
def _create_plex_connection(name: str, *, _session: Session = None) -> int:  # type: ignore
    conn = Connection(
        name=name,
        arr_type=ArrType.PLEX,
        url="http://localhost:32400",
        api_key="integration_test_token",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


# ---------------------------------------------------------------------------
# Plex item factory helpers (prefix-aware to avoid cross-run path collisions)
# ---------------------------------------------------------------------------

def _movie(prefix: str, i: int) -> PlexMediaItem:
    """Dummy movie whose folder_path will be /plex/<prefix>/movies/Movie <i>."""
    return PlexMediaItem.model_validate({
        "ratingKey": str(10000 + i),
        "title": f"Plex Movie {i}",
        "year": 2000 + (i % 25),
        "Media": [{"Part": [{"file": f"/plex/{prefix}/movies/Movie {i}/movie.mkv"}]}],
        "Guid": [{"id": f"tmdb://{300000 + i}"}],
    })


def _show(prefix: str, i: int) -> PlexMediaItem:
    """Dummy show whose folder_path will be /plex/<prefix>/shows/Show <i>."""
    return PlexMediaItem.model_validate({
        "ratingKey": str(50000 + i),
        "title": f"Plex Show {i}",
        "year": 2010 + (i % 15),
        "Location": [{"path": f"/plex/{prefix}/shows/Show {i}"}],
        "Guid": [{"id": f"tvdb://{400000 + i}"}],
    })


def _episode(prefix: str, show_i: int, ep: int) -> PlexEpisodeLeaf:
    """Dummy episode leaf used to resolve show-root folder."""
    return PlexEpisodeLeaf.model_validate({
        "grandparentRatingKey": str(50000 + show_i),
        "Media": [{
            "Part": [{"file": f"/plex/{prefix}/shows/Show {show_i}/Season 1/S01E{ep:02d}.mkv"}]
        }],
    })


def _library_section(key: str, type_: str, title: str, folder: str) -> PlexLibrarySection:
    return PlexLibrarySection.model_validate({
        "key": key, "type": type_, "title": title,
        "Location": [{"path": folder}],
    })


# ---------------------------------------------------------------------------
# Integration test class
# ---------------------------------------------------------------------------

class TestPlexLargeLibrarySync:
    """PlexConnectionManager correctly syncs 1500 movies + 160 series without errors."""

    MOVIE_COUNT = 1500
    SHOW_COUNT = 160

    @pytest.fixture(autouse=True)
    def setup(self):
        # Unique path prefix per test instance — prevents folder-path collisions
        # with items from previous test runs that are still in the persistent DB.
        self._prefix = uuid.uuid4().hex[:12]

        self.conn_id = _create_plex_connection(f"LargeSyncTest-{self._prefix}")

        # Identity path mappings (path_from == path_to): Plex paths need no
        # translation, but are recognised as "within the configured library".
        # plex_section_key is pre-set so _persist_section_keys skips DB writes
        # (the SimpleNamespace IDs have no real DB rows).
        self.path_mappings = [
            SimpleNamespace(
                id=9900,
                path_from=f"/plex/{self._prefix}/movies",
                path_to=f"/plex/{self._prefix}/movies",
                plex_section_key="1",
            ),
            SimpleNamespace(
                id=9901,
                path_from=f"/plex/{self._prefix}/shows",
                path_to=f"/plex/{self._prefix}/shows",
                plex_section_key="2",
            ),
        ]

        # PlexConnectionManager reads only these fields from ConnectionRead.
        self.connection = SimpleNamespace(
            id=self.conn_id,
            name=f"LargeSyncTest-{self._prefix}",
            url="http://localhost:32400",
            api_key="integration_test_token",
            monitor=MonitorType.MONITOR_MISSING,
            path_mappings=self.path_mappings,
        )

        # Pre-build all Plex items once — re-used across helper calls in this test.
        p = self._prefix
        self.movies = [_movie(p, i) for i in range(self.MOVIE_COUNT)]
        self.shows = [_show(p, i) for i in range(self.SHOW_COUNT)]
        # Two episode leaves per show so commonpath() resolves the show root correctly.
        self.leaves = [
            _episode(p, show_i, ep)
            for show_i in range(self.SHOW_COUNT)
            for ep in (1, 2)
        ]

        self.movie_section = _library_section("1", "movie", "Movies",
                                               f"/plex/{p}/movies")
        self.show_section = _library_section("2", "show", "Shows",
                                              f"/plex/{p}/shows")

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    async def _run_refresh(self, connection=None) -> PlexConnectionManager:
        """Run PlexConnectionManager.refresh() with mocked Plex API and FS."""
        conn = connection or self.connection
        movies = self.movies
        shows = self.shows
        leaves = self.leaves
        movie_section = self.movie_section
        show_section = self.show_section

        async def get_libraries():
            return [movie_section, show_section]

        async def get_library_media(section_key: str):
            for item in (movies if section_key == "1" else shows):
                yield item

        async def get_library_leaves(_section_key: str):
            for leaf in leaves:
                yield leaf

        mock_api = MagicMock()
        mock_api.server_url = ""
        mock_api.get_libraries = get_libraries
        mock_api.get_library_media = get_library_media
        mock_api.get_library_leaves = get_library_leaves

        with (
            patch("core.plex.connection_manager.PlexAPI", return_value=mock_api),
            patch.object(
                FilesHandler,
                "check_trailer_exists",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            manager = PlexConnectionManager(conn)
            await manager.refresh()

        return manager

    def _query_media(self, conn_id: int):
        """Return (movies_in_db, shows_in_db) for the given connection."""
        with get_session() as session:
            movies = session.exec(
                select(Media).where(
                    Media.connection_id == conn_id,
                    Media.is_movie == True,  # noqa: E712
                )
            ).all()
            shows = session.exec(
                select(Media).where(
                    Media.connection_id == conn_id,
                    Media.is_movie == False,  # noqa: E712
                )
            ).all()
        return movies, shows

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_first_sync_creates_all_media_without_exceptions(self):
        """Initial sync of 1500 movies + 160 series creates all rows, no exceptions."""
        manager = await self._run_refresh()

        assert manager._stats_added == self.MOVIE_COUNT + self.SHOW_COUNT, (
            f"Expected {self.MOVIE_COUNT + self.SHOW_COUNT} added, "
            f"got {manager._stats_added} added / {manager._stats_updated} updated. "
            f"(Path prefix: {self._prefix})"
        )
        assert manager._stats_updated == 0
        assert manager._stats_linked == 0
        assert manager._stats_sections_scanned == 2

        # --- DB: correct row counts ---
        movies_in_db, shows_in_db = self._query_media(self.conn_id)

        assert len(movies_in_db) == self.MOVIE_COUNT, (
            f"Expected {self.MOVIE_COUNT} movies, got {len(movies_in_db)}"
        )
        assert len(shows_in_db) == self.SHOW_COUNT, (
            f"Expected {self.SHOW_COUNT} shows, got {len(shows_in_db)}"
        )

        # All rows are Plex-only (arr_id == 0) linked to this connection
        assert all(m.arr_id == 0 for m in movies_in_db)
        assert all(m.arr_id == 0 for m in shows_in_db)
        assert all(m.plex_connection_id == self.conn_id for m in movies_in_db)
        assert all(m.plex_connection_id == self.conn_id for m in shows_in_db)

        # --- Events: MEDIA_ADDED fired for every item ---
        media_ids = {m.id for m in movies_in_db} | {m.id for m in shows_in_db}
        with get_session() as session:
            media_added = session.exec(
                select(Event).where(
                    Event.media_id.in_(media_ids),  # type: ignore[attr-defined]
                    Event.event_type == EventType.MEDIA_ADDED,
                )
            ).all()

        assert len(media_added) == self.MOVIE_COUNT + self.SHOW_COUNT, (
            f"Expected {self.MOVIE_COUNT + self.SHOW_COUNT} MEDIA_ADDED events, "
            f"got {len(media_added)}"
        )

    @pytest.mark.asyncio
    async def test_second_sync_updates_without_duplicating_rows(self):
        """Second sync over the same library updates plex fields, no new rows created."""
        # First sync: populate the DB
        await self._run_refresh()

        # Second sync: all items already exist
        manager = await self._run_refresh()

        assert manager._stats_added == 0, (
            f"Second sync must not create new rows, got {manager._stats_added} added"
        )
        assert manager._stats_linked == 0

        # Row count must be unchanged
        movies_in_db, shows_in_db = self._query_media(self.conn_id)
        total = len(movies_in_db) + len(shows_in_db)

        assert total == self.MOVIE_COUNT + self.SHOW_COUNT, (
            f"Second sync must not create duplicate rows. "
            f"Expected {self.MOVIE_COUNT + self.SHOW_COUNT}, got {total}"
        )

    @pytest.mark.asyncio
    async def test_plex_linked_event_fires_on_relinking(self):
        """PLEX_LINKED fires when an item's plex_connection_id changes."""
        # First sync: create items linked to self.conn_id
        await self._run_refresh()

        # Second Plex connection covering the same paths — triggers relinking
        conn_id_2 = _create_plex_connection(f"LargeSyncTest2-{self._prefix}")
        p = self._prefix
        connection_2 = SimpleNamespace(
            id=conn_id_2,
            name=f"LargeSyncTest2-{self._prefix}",
            url="http://localhost:32400",
            api_key="integration_test_token_2",
            monitor=MonitorType.MONITOR_MISSING,
            path_mappings=[
                SimpleNamespace(
                    id=9902,
                    path_from=f"/plex/{p}/movies",
                    path_to=f"/plex/{p}/movies",
                    plex_section_key="1",
                ),
                SimpleNamespace(
                    id=9903,
                    path_from=f"/plex/{p}/shows",
                    path_to=f"/plex/{p}/shows",
                    plex_section_key="2",
                ),
            ],
        )

        manager2 = await self._run_refresh(connection=connection_2)

        # All items existed already; none created; all newly linked to conn_id_2
        assert manager2._stats_added == 0
        assert manager2._stats_linked == self.MOVIE_COUNT + self.SHOW_COUNT, (
            f"Expected {self.MOVIE_COUNT + self.SHOW_COUNT} newly linked, "
            f"got {manager2._stats_linked}"
        )

        # PLEX_LINKED events should exist for every item
        with get_session() as session:
            plex_linked = session.exec(
                select(Event).where(
                    Event.event_type == EventType.PLEX_LINKED,
                    Event.new_value == f"LargeSyncTest2-{self._prefix}",
                )
            ).all()

        assert len(plex_linked) == self.MOVIE_COUNT + self.SHOW_COUNT, (
            f"Expected {self.MOVIE_COUNT + self.SHOW_COUNT} PLEX_LINKED events, "
            f"got {len(plex_linked)}"
        )
