"""Tests for library-root guards and the txdb-id fallback in the media
manager folder-path matching.

Regression tests for the bug where a media row stored a library root
(e.g. ``/media/tv``) as its folder. Such a row is a parent of every media
folder in the library, so:
  - read_by_folder_path prefix-matched it for any lookup,
  - a new Arr item adopted it (with all wrongly attributed files), and
  - the Plex upsert prefix-linked new shows onto it.

Covers:
  - base._library_root_paths / base._is_at_or_above_library_root
  - read_by_folder_path: stage-2 winner at/above a root → no match
  - create_or_update_bulk (Arr sync): no adoption of a root row
  - plex_create_or_update_bulk: stage-2 root rejection and the stage-3
    (txdb_id, is_movie) fallback, incl. folder-rename follow for
    Plex-only rows and the exactly-one-candidate rule
"""

import uuid

import pytest
from sqlmodel import Session

import database.manager.media as media_manager
from database.manager.media import base as media_base
from database.models.connection import (
    ArrType,
    Connection,
    PathMapping,
)
from database.models.media import MediaCreate
from database.engine import get_session, write_session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@write_session
def _make_conn(
    name: str,
    arr_type: ArrType,
    root: str | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Create a connection; when *root* is given, add an identity path
    mapping so *root* becomes a known library root."""
    conn = Connection(
        name=name,
        arr_type=arr_type,
        url="http://server:1234",
        api_key="key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    if root:
        _session.add(
            PathMapping(
                connection_id=conn.id, path_from=root, path_to=root
            )
        )
        _session.commit()
    return conn.id  # type: ignore


def _mc(
    conn_id: int,
    folder: str | None,
    *,
    arr_id: int = 0,
    is_movie: bool = False,
    txdb_id: str | None = None,
    title: str = "Item",
    plex_rating_key: str | None = None,
    plex_connection_id: int | None = None,
) -> MediaCreate:
    return MediaCreate(
        connection_id=conn_id,
        arr_id=arr_id,
        is_movie=is_movie,
        title=title,
        txdb_id=txdb_id or uuid.uuid4().hex[:12],
        folder_path=folder,
        plex_rating_key=plex_rating_key,
        plex_connection_id=plex_connection_id,
    )


# ---------------------------------------------------------------------------
# base helpers
# ---------------------------------------------------------------------------

class TestLibraryRootHelpers:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.root = f"/guard/{self._p}/tv"
        _make_conn(f"Helpers-{self._p}", ArrType.PLEX, self.root + "/")

    def test_library_root_paths_are_normalized(self):
        with get_session() as session:
            roots = media_base._library_root_paths(session)
        # Stored with a trailing slash, returned without
        assert self.root in roots

    def test_root_itself_detected(self):
        assert media_base._is_at_or_above_library_root(
            self.root, {self.root}
        )

    def test_parent_of_root_detected(self):
        assert media_base._is_at_or_above_library_root(
            f"/guard/{self._p}", {self.root}
        )

    def test_deeper_folder_not_detected(self):
        assert not media_base._is_at_or_above_library_root(
            f"{self.root}/Show", {self.root}
        )

    def test_sibling_folder_not_detected(self):
        # '/guard/<p>/tv' must not match '/guard/<p>/tv-4k' (no
        # startswith false positive)
        assert not media_base._is_at_or_above_library_root(
            f"{self.root}-4k", {self.root}
        )

    def test_empty_path_not_detected(self):
        assert not media_base._is_at_or_above_library_root(
            "", {self.root}
        )

    def test_trailing_slash_path_detected(self):
        assert media_base._is_at_or_above_library_root(
            self.root + "/", {self.root}
        )


# ---------------------------------------------------------------------------
# read_by_folder_path: stage-2 root guard
# ---------------------------------------------------------------------------

class TestReadByFolderPathRootGuard:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.root = f"/guard/{self._p}/tv"
        self.plex_conn = _make_conn(
            f"ReadGuard-{self._p}", ArrType.PLEX, self.root
        )

    def test_root_row_never_prefix_matches(self):
        """A row whose folder is the library root must not be returned
        for a lookup of a deeper path."""
        media_manager.create(
            _mc(self.plex_conn, self.root, title="Poisoned Root Row")
        )
        found = media_manager.read_by_folder_path(f"{self.root}/Some Show")
        assert found is None

    def test_legit_parent_row_still_wins_over_root_row(self):
        """Longest-match: a real show row beats the root row, so the
        season-subfolder safety net keeps working."""
        show = f"{self.root}/Real Show (2015)"
        media_manager.create(_mc(self.plex_conn, self.root))
        real = media_manager.create(_mc(self.plex_conn, show))
        found = media_manager.read_by_folder_path(f"{show}/Season 1")
        assert found is not None
        assert found.id == real.id

    def test_exact_match_unaffected(self):
        """Stage-1 exact match still works for normal folders."""
        show = f"{self.root}/Exact Show (2016)"
        row = media_manager.create(_mc(self.plex_conn, show))
        found = media_manager.read_by_folder_path(show)
        assert found is not None
        assert found.id == row.id


# ---------------------------------------------------------------------------
# Arr sync adoption (_read_plex_only_by_folder_path via create_or_update_bulk)
# ---------------------------------------------------------------------------

class TestArrAdoptionRootGuard:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.root = f"/guard/{self._p}/tv"
        self.plex_conn = _make_conn(
            f"AdoptGuardPlex-{self._p}", ArrType.PLEX, self.root
        )
        self.arr_conn = _make_conn(
            f"AdoptGuardArr-{self._p}", ArrType.SONARR
        )

    def test_new_arr_item_never_adopts_root_row(self):
        """The second bite of the bug: a new Arr series must not adopt a
        Plex-only row whose folder is the library root."""
        poisoned = media_manager.create(
            _mc(self.plex_conn, self.root, plex_rating_key="58166")
        )
        results = media_manager.create_or_update_bulk(
            [
                _mc(
                    self.arr_conn,
                    f"{self.root}/New Series (2026)",
                    arr_id=901,
                    title="New Series",
                )
            ]
        )
        media_read, created, _updated, arr_linked = results[0]
        assert created is True
        assert arr_linked is False
        assert media_read.id != poisoned.id
        # The poisoned row is untouched
        untouched = media_manager.read(poisoned.id)
        assert untouched.arr_id == 0
        assert untouched.folder_path == self.root

    def test_new_arr_item_adopts_exact_folder_plex_row(self):
        """Sanity: adoption by exact folder match keeps working."""
        folder = f"{self.root}/Adopted Series (2026)"
        plex_row = media_manager.create(
            _mc(self.plex_conn, folder, plex_rating_key="58167")
        )
        results = media_manager.create_or_update_bulk(
            [_mc(self.arr_conn, folder, arr_id=902, title="Adopted")]
        )
        media_read, created, _updated, arr_linked = results[0]
        assert created is False
        assert arr_linked is True
        assert media_read.id == plex_row.id
        assert media_read.arr_id == 902

    def test_new_arr_item_adopts_non_root_parent_plex_row(self):
        """Sanity: prefix adoption of a legitimate (deeper) parent row
        keeps working."""
        parent = f"{self.root}/Parent Show (2026)"
        plex_row = media_manager.create(
            _mc(self.plex_conn, parent, plex_rating_key="58168")
        )
        results = media_manager.create_or_update_bulk(
            [
                _mc(
                    self.arr_conn,
                    f"{parent}/Sub",
                    arr_id=903,
                    title="Sub Series",
                )
            ]
        )
        media_read, created, _updated, arr_linked = results[0]
        assert created is False
        assert arr_linked is True
        assert media_read.id == plex_row.id


# ---------------------------------------------------------------------------
# plex_create_or_update_bulk: stage-2 root guard and stage-3 txdb fallback
# ---------------------------------------------------------------------------

class TestPlexUpsertRootGuard:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.root = f"/guard/{self._p}/tv"
        self.plex_conn = _make_conn(
            f"UpsertGuard-{self._p}", ArrType.PLEX, self.root
        )

    def test_plex_item_never_links_to_root_row(self):
        """A new show must not prefix-link onto a row whose folder is the
        library root."""
        poisoned = media_manager.create(_mc(self.plex_conn, self.root))
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{self.root}/Fresh Show (2026)",
                    plex_rating_key="60001",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, _changed = results[0]
        assert created is True
        assert media_read.id != poisoned.id

    def test_plex_item_links_to_legit_parent_row(self):
        """Sanity: prefix linking onto a legitimate parent row (season
        subfolder case) keeps working."""
        show = f"{self.root}/Prefix Show (2026)"
        row = media_manager.create(_mc(self.plex_conn, show))
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{show}/Book One",
                    plex_rating_key="60002",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, _changed = results[0]
        assert created is False
        assert media_read.id == row.id


class TestPlexUpsertTxdbFallback:

    @pytest.fixture(autouse=True)
    def setup(self):
        self._p = uuid.uuid4().hex[:10]
        self.root = f"/guard/{self._p}/tv"
        self.plex_conn = _make_conn(
            f"TxdbPlex-{self._p}", ArrType.PLEX, self.root
        )
        self.arr_conn = _make_conn(f"TxdbArr-{self._p}", ArrType.SONARR)

    def test_links_by_txdb_when_folder_differs(self):
        """Folder match fails but the txdb id points at exactly one Arr
        row → the Plex data lands on that row. The Arr folder stays."""
        arr_folder = f"{self.root}/Arr Side Show (2026)"
        txdb = uuid.uuid4().hex[:12]
        arr_row = media_manager.create(
            _mc(
                self.arr_conn,
                arr_folder,
                arr_id=910,
                txdb_id=txdb,
                title="Arr Side Show",
            )
        )
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{self.root}/Plex Side Show (2026)",
                    txdb_id=txdb,
                    plex_rating_key="61001",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, linked, _changed = results[0]
        assert created is False
        assert linked is True
        assert media_read.id == arr_row.id
        assert media_read.plex_rating_key == "61001"
        # Arr rows keep the Arr folder
        assert media_read.folder_path == arr_folder

    def test_ambiguous_txdb_creates_new_row(self):
        """Two rows share the txdb id (e.g. two Radarr instances) — the
        fallback must not pick one arbitrarily."""
        txdb = uuid.uuid4().hex[:12]
        arr_conn2 = _make_conn(f"TxdbArr2-{self._p}", ArrType.RADARR)
        row_a = media_manager.create(
            _mc(
                self.arr_conn,
                f"{self.root}/Dup A (2026)",
                arr_id=911,
                is_movie=True,
                txdb_id=txdb,
            )
        )
        row_b = media_manager.create(
            _mc(
                arr_conn2,
                f"{self.root}/Dup B (2026)",
                arr_id=912,
                is_movie=True,
                txdb_id=txdb,
            )
        )
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{self.root}/Dup C (2026)",
                    is_movie=True,
                    txdb_id=txdb,
                    plex_rating_key="61002",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, _changed = results[0]
        assert created is True
        assert media_read.id not in {row_a.id, row_b.id}

    def test_txdb_match_requires_same_media_type(self):
        """A movie row must not match a show item with the same txdb id."""
        txdb = uuid.uuid4().hex[:12]
        movie_row = media_manager.create(
            _mc(
                self.arr_conn,
                f"{self.root}/Movie Type (2026)",
                arr_id=913,
                is_movie=True,
                txdb_id=txdb,
            )
        )
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{self.root}/Show Type (2026)",
                    is_movie=False,
                    txdb_id=txdb,
                    plex_rating_key="61003",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, _changed = results[0]
        assert created is True
        assert media_read.id != movie_row.id

    def test_never_links_to_plex_only_row_of_other_connection(self):
        """A Plex-only row of a different Plex connection must not be
        stolen — the same title on two Plex servers stays two rows."""
        other_plex = _make_conn(f"TxdbPlex2-{self._p}", ArrType.PLEX)
        txdb = uuid.uuid4().hex[:12]
        other_row = media_manager.create(
            _mc(
                other_plex,
                f"{self.root}/Other Server (2026)",
                txdb_id=txdb,
                plex_rating_key="61005",
                plex_connection_id=other_plex,
            )
        )
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{self.root}/This Server (2026)",
                    txdb_id=txdb,
                    plex_rating_key="61006",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, _changed = results[0]
        assert created is True
        assert media_read.id != other_row.id

    def test_never_steals_arr_row_linked_to_other_plex_connection(self):
        """An Arr row already linked to a different Plex connection must
        not be re-linked by txdb id."""
        other_plex = _make_conn(f"TxdbPlex3-{self._p}", ArrType.PLEX)
        txdb = uuid.uuid4().hex[:12]
        arr_row = media_manager.create(
            _mc(
                self.arr_conn,
                f"{self.root}/Linked Arr (2026)",
                arr_id=914,
                txdb_id=txdb,
                plex_rating_key="61007",
                plex_connection_id=other_plex,
            )
        )
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    f"{self.root}/Linked Plex (2026)",
                    txdb_id=txdb,
                    plex_rating_key="61008",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, _changed = results[0]
        assert created is True
        assert media_read.id != arr_row.id
        # The other connection's link is untouched
        untouched = media_manager.read(arr_row.id)
        assert untouched.plex_connection_id == other_plex
        assert untouched.plex_rating_key == "61007"

    def test_plex_only_row_follows_folder_rename(self):
        """A Plex-only row matched by txdb id follows the folder move —
        the row is kept, not recreated."""
        old_folder = f"{self.root}/Old Name (2026)"
        new_folder = f"{self.root}/New Name (2026)"
        txdb = uuid.uuid4().hex[:12]
        row = media_manager.create(
            _mc(
                self.plex_conn,
                old_folder,
                txdb_id=txdb,
                plex_rating_key="61004",
                plex_connection_id=self.plex_conn,
            )
        )
        results = media_manager.plex_create_or_update_bulk(
            [
                _mc(
                    self.plex_conn,
                    new_folder,
                    txdb_id=txdb,
                    plex_rating_key="61004",
                    plex_connection_id=self.plex_conn,
                )
            ]
        )
        media_read, created, _linked, changed = results[0]
        assert created is False
        assert media_read.id == row.id
        assert changed is True
        assert media_read.folder_path == new_folder
