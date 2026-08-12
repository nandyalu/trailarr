"""Tests for show-folder derivation and library-root guards in
PlexConnectionManager.

Regression tests for the bug where a show with episodes in more than one
folder (e.g. a stale duplicate folder) made ``os.path.commonpath`` collapse
to the library root. The root folder was stored as the media folder, so the
row matched every media item under the root and adopted all their files
and trailers.

Covers:
  - _is_at_or_above_library_root: root, parent-of-root, deeper, sibling
  - _derive_show_folder: common-path primary, majority-vote fallback,
    no-safe-folder result, commonpath ValueError fallback
  - _process_item_chunk: skip items whose folder is at/above a library root
  - _process_show_section: end-to-end derivation with a stale duplicate
    folder (links to the existing Arr row, no bogus row created)
"""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

import core.base.database.manager.media as media_manager
from core.base.database.models.connection import ArrType, Connection
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session
from core.plex.connection_manager import PlexConnectionManager
from core.plex.models import (
    PlexEpisodeLeaf,
    PlexLibrarySection,
    PlexMediaItem,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@write_session
def _make_conn(
    name: str, arr_type: ArrType, *, _session: Session = None  # type: ignore
) -> int:
    conn = Connection(
        name=name,
        arr_type=arr_type,
        url="http://server:1234",
        api_key="tok",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


def _pm(path_from: str, path_to: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        id=9999,
        path_from=path_from,
        path_to=path_to or path_from,
        plex_section_key="1",
    )


def _build_manager(conn_id: int, prefix: str) -> PlexConnectionManager:
    connection = SimpleNamespace(
        id=conn_id,
        name=f"Derive-{prefix}",
        url="http://plex:32400",
        api_key="tok",
        monitor_new_media=True,
        path_mappings=[
            _pm(f"/plex/{prefix}/movies"),
            _pm(f"/plex/{prefix}/shows"),
        ],
    )
    with patch("core.plex.connection_manager.PlexAPI") as MockAPI:
        MockAPI.return_value = MagicMock(server_url="")
        return PlexConnectionManager(connection)


def _leaf(show_key: str, season: int, file: str) -> PlexEpisodeLeaf:
    return PlexEpisodeLeaf.model_validate({
        "grandparentRatingKey": show_key,
        "parentIndex": season,
        "Media": [{"Part": [{"file": file}]}],
    })


def _show_item(key: str, title: str, tvdb_id: int) -> PlexMediaItem:
    return PlexMediaItem.model_validate({
        "ratingKey": key,
        "title": title,
        "year": 2015,
        "type": "show",
        "Guid": [{"id": f"tvdb://{tvdb_id}"}],
    })


def _show_section(prefix: str) -> PlexLibrarySection:
    return PlexLibrarySection.model_validate({
        "key": "1",
        "type": "show",
        "title": "Shows",
        "Location": [{"path": f"/plex/{prefix}/shows"}],
    })


def _async_gen(items):
    async def gen(*args, **kwargs):
        for item in items:
            yield item

    return gen


# ---------------------------------------------------------------------------
# _is_at_or_above_library_root
# ---------------------------------------------------------------------------

class TestIsAtOrAboveLibraryRoot:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.mgr = _build_manager(90001, self._p)
        self.root = f"/plex/{self._p}/shows"

    def test_library_root_itself(self):
        assert self.mgr._is_at_or_above_library_root(self.root) is True

    def test_parent_of_library_root(self):
        assert (
            self.mgr._is_at_or_above_library_root(f"/plex/{self._p}") is True
        )

    def test_folder_below_root(self):
        assert (
            self.mgr._is_at_or_above_library_root(f"{self.root}/Show")
            is False
        )

    def test_unrelated_sibling_folder(self):
        assert (
            self.mgr._is_at_or_above_library_root(f"/plex/{self._p}-other")
            is False
        )

    def test_empty_folder(self):
        assert self.mgr._is_at_or_above_library_root("") is False

    def test_trailing_slash_on_root(self):
        assert self.mgr._is_at_or_above_library_root(self.root + "/") is True


# ---------------------------------------------------------------------------
# _derive_show_folder
# ---------------------------------------------------------------------------

class TestDeriveShowFolder:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.mgr = _build_manager(90002, self._p)
        self.root = f"/plex/{self._p}/shows"

    def test_seasonal_layout(self):
        paths = [
            f"{self.root}/Show (2015)/Season 1",
            f"{self.root}/Show (2015)/Season 2",
        ]
        assert (
            self.mgr._derive_show_folder(paths, "Show")
            == f"{self.root}/Show (2015)"
        )

    def test_flat_layout(self):
        paths = [f"{self.root}/Show (2015)"]
        assert (
            self.mgr._derive_show_folder(paths, "Show")
            == f"{self.root}/Show (2015)"
        )

    def test_single_season_folder_stripped(self):
        paths = [f"{self.root}/Show (2015)/Season 1"]
        assert (
            self.mgr._derive_show_folder(paths, "Show")
            == f"{self.root}/Show (2015)"
        )

    def test_stale_duplicate_folder_majority_vote(self):
        """The Daredevil case: a stale duplicate folder collapses the
        common path to the library root — the majority folder must win."""
        real = f"{self.root}/Show (2015) {{tvdb-1}}"
        stale = f"{self.root}/Show (Show (2015))"
        paths = [
            f"{real}/Season 1",
            f"{real}/Season 2",
            f"{real}/Season 3",
            f"{stale}/Season 1",
        ]
        assert self.mgr._derive_show_folder(paths, "Show") == real

    def test_majority_vote_counts_episodes_not_seasons(self):
        """Majority is per episode directory entry, so the folder with
        more episodes wins even with fewer distinct season folders."""
        a = f"{self.root}/Show A"
        b = f"{self.root}/Show B"
        paths = [
            f"{a}/Season 1",
            f"{a}/Season 1",
            f"{a}/Season 1",
            f"{b}/Season 1",
            f"{b}/Season 2",
        ]
        assert self.mgr._derive_show_folder(paths, "Show") == a

    def test_all_episodes_in_library_root_returns_empty(self):
        """Episode files directly in the library root: no safe folder."""
        paths = [self.root, self.root]
        assert self.mgr._derive_show_folder(paths, "Show") == ""

    def test_commonpath_valueerror_falls_back_to_first_path(self):
        """Mixed absolute/relative paths raise ValueError in commonpath —
        the first path is used instead."""
        paths = [f"{self.root}/Show (2015)/Season 1", "relative/other"]
        assert (
            self.mgr._derive_show_folder(paths, "Show")
            == f"{self.root}/Show (2015)"
        )


# ---------------------------------------------------------------------------
# _process_item_chunk: library-root guard
# ---------------------------------------------------------------------------

class TestProcessItemChunkRootGuard:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.conn_id = _make_conn(f"RootGuard-{self._p}", ArrType.PLEX)
        self.mgr = _build_manager(self.conn_id, self._p)
        self.section = PlexLibrarySection.model_validate({
            "key": "1",
            "type": "movie",
            "title": "Movies",
            "Location": [{"path": f"/plex/{self._p}/movies"}],
        })

    def _our_media(self):
        return [
            m
            for m in media_manager.read_all()
            if m.connection_id == self.conn_id
        ]

    @pytest.mark.asyncio
    async def test_item_at_library_root_is_skipped(self):
        """A movie file directly in the library root derives the root as
        its folder — the item must be skipped, not stored."""
        root = f"/plex/{self._p}/movies"
        item = PlexMediaItem.model_validate({
            "ratingKey": "91001",
            "title": "Loose File Movie",
            "year": 2020,
            "Media": [{"Part": [{"file": f"{root}/movie.mkv"}]}],
            "Guid": [{"id": "tmdb://910001"}],
        })
        await self.mgr._process_item_chunk([(item, self.section, True, root)])
        assert self.mgr._stats_added == 0
        assert self._our_media() == []

    @pytest.mark.asyncio
    async def test_item_below_root_still_processed(self):
        """Sanity: a normal folder below the root is created as usual."""
        folder = f"/plex/{self._p}/movies/Film1"
        item = PlexMediaItem.model_validate({
            "ratingKey": "91002",
            "title": "Normal Movie",
            "year": 2020,
            "Media": [{"Part": [{"file": f"{folder}/movie.mkv"}]}],
            "Guid": [{"id": "tmdb://910002"}],
        })
        await self.mgr._process_item_chunk(
            [(item, self.section, True, folder)]
        )
        assert self.mgr._stats_added == 1
        assert [m.folder_path for m in self._our_media()] == [folder]


# ---------------------------------------------------------------------------
# _process_show_section: end-to-end derivation
# ---------------------------------------------------------------------------

class TestProcessShowSectionDerivation:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.plex_conn_id = _make_conn(f"ShowSec-{self._p}", ArrType.PLEX)
        self.sonarr_conn_id = _make_conn(
            f"ShowSecArr-{self._p}", ArrType.SONARR
        )
        self.mgr = _build_manager(self.plex_conn_id, self._p)
        self.section = _show_section(self._p)
        self.root = f"/plex/{self._p}/shows"

    def _media_at(self, folder: str):
        return [
            m for m in media_manager.read_all() if m.folder_path == folder
        ]

    def _plex_rows(self):
        return [
            m
            for m in media_manager.read_all()
            if m.connection_id == self.plex_conn_id
        ]

    @pytest.mark.asyncio
    async def test_stale_duplicate_links_to_arr_row(self):
        """Daredevil regression: with a stale duplicate folder the show
        must still link to the existing Arr row — no root-folder row."""
        real = f"{self.root}/Dare (2015) {{tvdb-1}}"
        stale = f"{self.root}/Dare (Dare (2015))"
        tvdb = uuid.uuid4().int % 10**9
        arr_row = media_manager.create(
            MediaCreate(
                connection_id=self.sonarr_conn_id,
                arr_id=85,
                is_movie=False,
                title="Dare",
                txdb_id=str(tvdb),
                folder_path=real,
            )
        )
        leaves = (
            [_leaf("58166", 1, f"{real}/Season 1/e{i}.mkv") for i in range(4)]
            + [_leaf("58166", 1, f"{stale}/Season 1/e9.mkv")]
        )
        self.mgr.api.get_library_leaves = _async_gen(leaves)
        self.mgr.api.get_library_media = _async_gen(
            [_show_item("58166", "Dare", tvdb)]
        )
        await self.mgr._process_show_section(self.section)

        # Plex data landed on the Arr row; no new Plex-only row was made
        assert self._plex_rows() == []
        linked = media_manager.read(arr_row.id)
        assert linked.plex_rating_key == "58166"
        assert linked.folder_path == real
        assert self._media_at(self.root) == []

    @pytest.mark.asyncio
    async def test_episodes_only_in_library_root_skips_show(self):
        """All episode files directly in the library root: the show is
        skipped, no row is created."""
        leaves = [
            _leaf("77001", 1, f"{self.root}/e{i}.mkv") for i in range(3)
        ]
        self.mgr.api.get_library_leaves = _async_gen(leaves)
        self.mgr.api.get_library_media = _async_gen(
            [_show_item("77001", "Rootless", uuid.uuid4().int % 10**9)]
        )
        await self.mgr._process_show_section(self.section)
        assert self._plex_rows() == []

    @pytest.mark.asyncio
    async def test_show_without_leaves_uses_location_path(self):
        """A show with no episode files falls back to its Location path."""
        folder = f"{self.root}/Empty Show (2020)"
        item = PlexMediaItem.model_validate({
            "ratingKey": "77002",
            "title": "Empty Show",
            "year": 2020,
            "type": "show",
            "Guid": [{"id": f"tvdb://{uuid.uuid4().int % 10**9}"}],
            "Location": [{"path": folder}],
        })
        self.mgr.api.get_library_leaves = _async_gen([])
        self.mgr.api.get_library_media = _async_gen([item])
        await self.mgr._process_show_section(self.section)
        assert [m.folder_path for m in self._plex_rows()] == [folder]
