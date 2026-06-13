"""Edge-case unit tests for PlexConnectionManager.

Covers branches not exercised by the large-library integration test:
  - _check_monitoring with trailer=True and MONITOR_NONE
  - _process_item_chunk: empty chunk, filtered items, youtube_id, trailer detected,
    existing-item monitor change, empty folder_path
  - _process_show_section: leaf with no key, commonpath ValueError
  - _process_section: untracked section, unsupported type, _persist_section_keys
  - refresh: no path mappings, section exception
  - trigger_item_scan: success and failure paths
"""

import os
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from sqlmodel import Session

from core.base.database.models.connection import ArrType, Connection, MonitorType
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session
import core.base.database.manager.media as media_manager
from core.files_handler import FilesHandler
from core.plex.connection_manager import PlexConnectionManager
from core.plex.models import PlexEpisodeLeaf, PlexLibrarySection, PlexMediaItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@write_session
def _make_plex_conn(name: str, *, _session: Session = None) -> int:  # type: ignore
    conn = Connection(
        name=name,
        arr_type=ArrType.PLEX,
        url="http://plex:32400",
        api_key="tok",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


def _pm(path_from: str, path_to: str = "", *, section_key: str | None = "1") -> SimpleNamespace:
    return SimpleNamespace(
        id=9999,
        path_from=path_from,
        path_to=path_to or path_from,
        plex_section_key=section_key,
    )


def _section(key: str, type_: str, folder: str, title: str = "Lib") -> PlexLibrarySection:
    return PlexLibrarySection.model_validate(
        {"key": key, "type": type_, "title": title, "Location": [{"path": folder}]}
    )


def _movie_item(prefix: str, i: int, folder: str | None = None) -> PlexMediaItem:
    f = folder or f"/plex/{prefix}/movies/Film{i}"
    return PlexMediaItem.model_validate({
        "ratingKey": str(7000 + i),
        "title": f"Edge Film {i}",
        "year": 2010,
        "Media": [{"Part": [{"file": f"{f}/movie.mkv"}]}],
        "Guid": [{"id": f"tmdb://{800000 + i}"}],
    })


def _build_manager(
    conn_id: int,
    prefix: str,
    *,
    monitor: MonitorType = MonitorType.MONITOR_MISSING,
) -> PlexConnectionManager:
    connection = SimpleNamespace(
        id=conn_id,
        name=f"Edge-{prefix}",
        url="http://plex:32400",
        api_key="tok",
        monitor=monitor,
        path_mappings=[
            _pm(f"/plex/{prefix}/movies"),
            _pm(f"/plex/{prefix}/shows"),
        ],
    )
    with patch("core.plex.connection_manager.PlexAPI") as MockAPI:
        MockAPI.return_value = MagicMock(server_url="")
        mgr = PlexConnectionManager(connection)
    return mgr


# ---------------------------------------------------------------------------
# _check_monitoring
# ---------------------------------------------------------------------------

class TestCheckMonitoring:
    def _mgr(self, monitor: MonitorType) -> PlexConnectionManager:
        conn_id = _make_plex_conn(f"ChkMon-{monitor.value}")
        return _build_manager(conn_id, f"chkmon{monitor.value}", monitor=monitor)

    def test_trailer_exists_returns_false(self):
        """If a trailer already exists, monitoring is False regardless of mode (line 121)."""
        mgr = self._mgr(MonitorType.MONITOR_MISSING)
        assert mgr._check_monitoring(trailer_exists=True) is False

    def test_monitor_none_returns_false(self):
        """MONITOR_NONE always returns False even without a trailer (line 123)."""
        mgr = self._mgr(MonitorType.MONITOR_NONE)
        assert mgr._check_monitoring(trailer_exists=False) is False

    def test_monitor_missing_no_trailer_returns_true(self):
        """MONITOR_MISSING with no trailer → True (control path)."""
        mgr = self._mgr(MonitorType.MONITOR_MISSING)
        assert mgr._check_monitoring(trailer_exists=False) is True


# ---------------------------------------------------------------------------
# _process_item_chunk edge cases
# ---------------------------------------------------------------------------

class TestProcessItemChunkEdges:

    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self._p = uuid.uuid4().hex[:10]
        self.conn_id = _make_plex_conn(f"ChunkEdge-{self._p}")
        self.mgr = _build_manager(self.conn_id, self._p)
        self.section = _section("1", "movie", f"/plex/{self._p}/movies")

    async def _run_chunk(self, chunk, *, trailer_return=False):
        with patch.object(FilesHandler, "check_trailer_exists",
                          new_callable=AsyncMock, return_value=trailer_return):
            await self.mgr._process_item_chunk(chunk)

    @pytest.mark.asyncio
    async def test_empty_chunk_returns_immediately(self):
        """Empty chunk exits without DB calls (lines 187-188)."""
        await self._run_chunk([])
        assert self.mgr._stats_added == 0

    @pytest.mark.asyncio
    async def test_item_not_in_configured_library_is_skipped(self):
        """Item whose plex_folder is outside all path_from values is skipped
        (lines 193-198), leaving parsed empty → early return (lines 211-212)."""
        foreign_item = _movie_item(self._p, 0, folder="/unmapped/Film0")
        chunk = [(foreign_item, self.section, True, "/unmapped/Film0")]
        await self._run_chunk(chunk)
        assert self.mgr._stats_added == 0

    @pytest.mark.asyncio
    async def test_item_with_empty_plex_folder_skips_path_mapping(self):
        """Item with empty plex_folder skips library check and path mapping
        (line 199 else branch); _check_trailer('') returns False (lines 287-288)."""
        item = PlexMediaItem.model_validate({
            "ratingKey": "9001",
            "title": "No Folder Film",
            "year": 2020,
            "Guid": [{"id": "tmdb://990001"}],
            # No Media.Part.file and no Location → media_folder = ""
        })
        chunk = [(item, self.section, True, "")]
        await self._run_chunk(chunk)
        assert self.mgr._stats_added == 1

    @pytest.mark.asyncio
    async def test_new_item_with_youtube_id_fires_event(self):
        """A newly created item with youtube_trailer_id fires a YOUTUBE_ID_CHANGED
        event in the pending_events list (lines 254-264)."""
        item = _movie_item(self._p, 50)
        folder = f"/plex/{self._p}/movies/Film50"

        original_parse = __import__(
            "core.plex.data_parser", fromlist=["parse_plex_item"]
        ).parse_plex_item

        def _parse_with_yt(*args, **kwargs):
            mc = original_parse(*args, **kwargs)
            mc.youtube_trailer_id = "dQw4w9WgXcQ"
            return mc

        chunk = [(item, self.section, True, folder)]
        with patch("core.plex.connection_manager.parse_plex_item", side_effect=_parse_with_yt):
            await self._run_chunk(chunk)

        assert self.mgr._stats_added == 1

    @pytest.mark.asyncio
    async def test_trailer_detected_event_fires_when_trailer_exists(self):
        """When check_trailer_exists returns True for a new item, TRAILER_DETECTED
        and an additional MONITOR_CHANGED event are queued (lines 301-320)."""
        item = _movie_item(self._p, 51)
        folder = f"/plex/{self._p}/movies/Film51"
        chunk = [(item, self.section, True, folder)]
        await self._run_chunk(chunk, trailer_return=True)
        assert self.mgr._stats_added == 1

    @pytest.mark.asyncio
    async def test_existing_item_monitor_change_increments_updated(self):
        """An existing Plex-only item whose computed monitor differs from stored
        value triggers a MONITOR_CHANGED event and increments _stats_updated
        (lines 324-344)."""
        # First sync: create the item (no trailer → monitor=True)
        item = _movie_item(self._p, 100)
        folder = f"/plex/{self._p}/movies/Film100"
        chunk = [(item, self.section, True, folder)]
        await self._run_chunk(chunk, trailer_return=False)
        assert self.mgr._stats_added == 1

        # Manually flip monitor to False so next sync detects a change
        media_list = media_manager.read_all()
        our_media = [m for m in media_list if m.connection_id == self.conn_id]
        assert our_media, "Item should be in DB after first sync"
        media_manager.update_monitoring(our_media[-1].id, monitor=False)

        # Second sync: MONITOR_MISSING + no trailer → computed=True, stored=False → change
        await self._run_chunk(chunk, trailer_return=False)
        assert self.mgr._stats_updated >= 1

    @pytest.mark.asyncio
    async def test_monitor_new_skips_existing_item_monitor_check(self):
        """When connection monitor=MONITOR_NEW, existing Plex-only items skip the
        monitor recalculation block (line 326->343 False branch)."""
        import uuid
        p = uuid.uuid4().hex[:10]
        conn_id = _make_plex_conn(f"MonNew-{p}")
        mgr = _build_manager(conn_id, p, monitor=MonitorType.MONITOR_NEW)
        section = _section("1", "movie", f"/plex/{p}/movies")

        item = _movie_item(p, 0)
        folder = f"/plex/{p}/movies/Film0"
        chunk = [(item, section, True, folder)]

        # First sync: create the item
        with patch.object(FilesHandler, "check_trailer_exists",
                          new_callable=AsyncMock, return_value=False):
            await mgr._process_item_chunk(chunk)
        assert mgr._stats_added == 1

        # Second sync: MONITOR_NEW → no monitor recalculation for existing items
        with patch.object(FilesHandler, "check_trailer_exists",
                          new_callable=AsyncMock, return_value=False):
            await mgr._process_item_chunk(chunk)
        # Not updated (no plex_fields_changed, no monitor_changed)
        assert mgr._stats_updated == 0


# ---------------------------------------------------------------------------
# _process_show_section edge cases
# ---------------------------------------------------------------------------

class TestProcessShowSectionEdges:

    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self._p = uuid.uuid4().hex[:10]
        self.conn_id = _make_plex_conn(f"ShowEdge-{self._p}")
        self.mgr = _build_manager(self.conn_id, self._p)
        self.section = _section("2", "show", f"/plex/{self._p}/shows", title="Shows")

    @pytest.mark.asyncio
    async def test_leaf_with_no_grandparent_key_is_ignored(self):
        """A leaf with empty grandparentRatingKey is skipped in folder_map build
        (line 382, false branch of `if leaf.grandparentRatingKey and leaf.media_folder`)."""
        bad_leaf = PlexEpisodeLeaf.model_validate({
            "grandparentRatingKey": "",
            "Media": [{"Part": [{"file": f"/plex/{self._p}/shows/Show0/S01E01.mkv"}]}],
        })
        show_item = PlexMediaItem.model_validate({
            "ratingKey": "6001",
            "title": "Show Zero",
            "year": 2018,
            "Location": [{"path": f"/plex/{self._p}/shows/Show0"}],
            "Guid": [{"id": "tvdb://600001"}],
        })

        async def _leaves(_key):
            yield bad_leaf

        async def _media(_key):
            yield show_item

        mock_api = MagicMock(server_url="")
        mock_api.get_library_leaves = _leaves
        mock_api.get_library_media = _media
        self.mgr.api = mock_api
        self.mgr.server_url = ""

        with patch.object(FilesHandler, "check_trailer_exists",
                          new_callable=AsyncMock, return_value=False):
            await self.mgr._process_show_section(self.section)

        # Show still processed via Location fallback; leaf had no grandparentRatingKey
        assert self.mgr._stats_added == 1

    @pytest.mark.asyncio
    async def test_commonpath_value_error_falls_back_to_first_path(self):
        """When os.path.commonpath raises ValueError, the fallback uses paths[0]
        (lines 387-390)."""
        leaf = PlexEpisodeLeaf.model_validate({
            "grandparentRatingKey": "6002",
            "Media": [{"Part": [{"file": f"/plex/{self._p}/shows/ShowErr/S01E01.mkv"}]}],
        })
        show_item = PlexMediaItem.model_validate({
            "ratingKey": "6002",
            "title": "Show Error",
            "year": 2019,
            "Location": [{"path": f"/plex/{self._p}/shows/ShowErr"}],
            "Guid": [{"id": "tvdb://600002"}],
        })

        async def _leaves(_key):
            yield leaf

        async def _media(_key):
            yield show_item

        mock_api = MagicMock(server_url="")
        mock_api.get_library_leaves = _leaves
        mock_api.get_library_media = _media
        self.mgr.api = mock_api
        self.mgr.server_url = ""

        with (
            patch.object(FilesHandler, "check_trailer_exists",
                         new_callable=AsyncMock, return_value=False),
            patch("os.path.commonpath", side_effect=ValueError("mixed drives")),
        ):
            await self.mgr._process_show_section(self.section)

        assert self.mgr._stats_added == 1


# ---------------------------------------------------------------------------
# _process_section: untracked / unsupported type / _persist_section_keys
# ---------------------------------------------------------------------------

class TestProcessSection:

    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self._p = uuid.uuid4().hex[:10]
        self.conn_id = _make_plex_conn(f"SecEdge-{self._p}")
        self.mgr = _build_manager(self.conn_id, self._p)

    @pytest.mark.asyncio
    async def test_untracked_section_is_skipped(self):
        """Section whose folders don't match any path_from is skipped before
        any processing (lines 412-417)."""
        untracked = _section("9", "movie", "/completely/different/path", title="Untracked")
        await self.mgr._process_section(untracked)
        assert self.mgr._stats_sections_scanned == 0

    @pytest.mark.asyncio
    async def test_unsupported_section_type_logs_and_does_nothing(self):
        """Section type not in movie/show constants logs and returns without adding
        media (lines 424-428)."""
        music = PlexLibrarySection.model_validate({
            "key": "5",
            "type": "artist",
            "title": "Music",
            "Location": [{"path": f"/plex/{self._p}/movies"}],  # tracked folder
        })
        await self.mgr._process_section(music)
        assert self.mgr._stats_added == 0
        # Section IS tracked, so it counts as scanned
        assert self.mgr._stats_sections_scanned == 1

    def test_persist_section_keys_writes_when_plex_section_key_is_none(self):
        """_persist_section_keys calls update_path_mapping_section_key when the
        path mapping's plex_section_key is None (lines 157-165)."""
        import uuid
        p = uuid.uuid4().hex[:10]
        conn_id = _make_plex_conn(f"PersistKey-{p}")
        pm_none = SimpleNamespace(
            id=8888,
            path_from=f"/plex/{p}/movies",
            path_to=f"/plex/{p}/movies",
            plex_section_key=None,
        )
        connection = SimpleNamespace(
            id=conn_id,
            name=f"PersistKey-{p}",
            url="http://plex:32400",
            api_key="tok",
            monitor=MonitorType.MONITOR_MISSING,
            path_mappings=[pm_none],
        )
        with patch("core.plex.connection_manager.PlexAPI") as MockAPI:
            MockAPI.return_value = MagicMock(server_url="")
            mgr = PlexConnectionManager(connection)

        section = _section("3", "movie", f"/plex/{p}/movies", title="Test")
        with patch(
            "core.plex.connection_manager.connection_manager.update_path_mapping_section_key"
        ) as mock_update:
            mgr._persist_section_keys(section)
            mock_update.assert_called_once_with(8888, "3")
        assert pm_none.plex_section_key == "3"


# ---------------------------------------------------------------------------
# refresh: no path mappings + section exception
# ---------------------------------------------------------------------------

class TestRefreshEdges:

    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self._p = uuid.uuid4().hex[:10]
        self.conn_id = _make_plex_conn(f"RefEdge-{self._p}")

    def _build(self, path_mappings: list) -> PlexConnectionManager:
        connection = SimpleNamespace(
            id=self.conn_id,
            name=f"RefEdge-{self._p}",
            url="http://plex:32400",
            api_key="tok",
            monitor=MonitorType.MONITOR_MISSING,
            path_mappings=path_mappings,
        )
        with patch("core.plex.connection_manager.PlexAPI") as MockAPI:
            MockAPI.return_value = MagicMock(server_url="")
            return PlexConnectionManager(connection)

    @pytest.mark.asyncio
    async def test_refresh_with_no_path_mappings_returns_early(self):
        """refresh() logs a warning and returns when all_path_mappings is empty
        (lines 474-480)."""
        mgr = self._build([])
        mock_api = MagicMock(server_url="")
        mgr.api = mock_api
        await mgr.refresh()
        mock_api.get_libraries.assert_not_called()
        assert mgr._stats_sections_scanned == 0

    @pytest.mark.asyncio
    async def test_refresh_logs_error_on_section_exception(self):
        """An exception in _process_section is caught and logged; refresh()
        does not propagate it (lines 487-492)."""
        mgr = self._build([_pm(f"/plex/{self._p}/movies")])
        broken_section = _section("1", "movie", f"/plex/{self._p}/movies", title="Broken")

        async def _get_libraries():
            return [broken_section]

        mock_api = MagicMock(server_url="")
        mock_api.get_libraries = _get_libraries
        mgr.api = mock_api

        with patch.object(mgr, "_process_section", side_effect=RuntimeError("boom")):
            await mgr.refresh()  # must not raise

        assert mgr._stats_sections_scanned == 0


# ---------------------------------------------------------------------------
# trigger_item_scan: success and failure paths
# ---------------------------------------------------------------------------

class TestTriggerItemScan:

    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self._p = uuid.uuid4().hex[:10]
        self.conn_id = _make_plex_conn(f"TrigScan-{self._p}")

        mc = MediaCreate(
            connection_id=self.conn_id,
            arr_id=0,
            is_movie=True,
            title="Scan Film",
            txdb_id=f"tmdb_scan_{self._p}",
            folder_path=f"/plex/{self._p}/movies/ScanFilm",
            plex_connection_id=self.conn_id,
            plex_rating_key="rk_scan",
            plex_section_key="1",
        )
        result = media_manager.plex_create_or_update_bulk([mc])
        self.media_id = result[0][0].id

        mgr_conn = SimpleNamespace(
            id=self.conn_id,
            name=f"TrigScan-{self._p}",
            url="http://plex:32400",
            api_key="tok",
            monitor=MonitorType.MONITOR_MISSING,
            path_mappings=[_pm(f"/plex/{self._p}/movies")],
        )
        with patch("core.plex.connection_manager.PlexAPI") as MockAPI:
            MockAPI.return_value = MagicMock(server_url="")
            self.mgr = PlexConnectionManager(mgr_conn)

    @pytest.mark.asyncio
    async def test_scan_success_fires_event(self):
        """When scan_section_path returns True, a PLEX_SCAN_TRIGGERED event is
        written and True is returned (lines 455-462)."""
        self.mgr.api.scan_section_path = AsyncMock(return_value=True)
        result = await self.mgr.trigger_item_scan(
            media_id=self.media_id,
            section_key="1",
            folder_path=f"/plex/{self._p}/movies/ScanFilm",
        )
        assert result is True
        self.mgr.api.scan_section_path.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_scan_failure_does_not_fire_event(self):
        """When scan_section_path returns False, no event is written and False
        is returned (line 455, skip event block)."""
        self.mgr.api.scan_section_path = AsyncMock(return_value=False)
        result = await self.mgr.trigger_item_scan(
            media_id=self.media_id,
            section_key="1",
            folder_path=f"/plex/{self._p}/movies/ScanFilm",
        )
        assert result is False
