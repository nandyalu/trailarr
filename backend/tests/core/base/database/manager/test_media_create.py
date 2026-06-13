"""Tests for media create manager functions."""

import pytest
from sqlmodel import Session

from core.base.database.models.connection import ArrType, Connection, MonitorType
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session
import core.base.database.manager.media as media_manager
from exceptions import ItemNotFoundError


@write_session
def _make_plex_connection(name: str = "Plex", *, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=name,
        arr_type=ArrType.PLEX,
        url="http://plex:32400",
        api_key="plex_key",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


@write_session
def _make_connection(
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    conn = Connection(
        name="Test Connection",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


class TestMediaCreate:
    """Tests for media_manager.create (single-item creation)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()

    def test_creates_media_with_valid_connection(self):
        """Creates and returns a MediaRead when connection_id is valid."""
        media_data = MediaCreate(
            connection_id=self.conn.id,  # type: ignore
            arr_id=1,
            is_movie=True,
            title="New Movie",
            txdb_id="tt9991001",
        )
        created = media_manager.create(media_data)
        assert created.id is not None
        assert created.title == "New Movie"
        assert created.connection_id == self.conn.id

    def test_raises_when_connection_does_not_exist(self):
        """Raises ItemNotFoundError when connection_id is invalid."""
        media_data = MediaCreate(
            connection_id=99999,
            arr_id=1,
            is_movie=True,
            title="Ghost Movie",
            txdb_id="tt9991002",
        )
        with pytest.raises(ItemNotFoundError):
            media_manager.create(media_data)

    def test_created_media_readable_from_db(self):
        """Newly created media can be read back by id."""
        media_data = MediaCreate(
            connection_id=self.conn.id,  # type: ignore
            arr_id=2,
            is_movie=False,
            title="New Show",
            txdb_id="tt9991003",
        )
        created = media_manager.create(media_data)
        fetched = media_manager.read(created.id)
        assert fetched.id == created.id
        assert fetched.title == "New Show"
        assert fetched.is_movie is False

    def test_plex_trailer_defaults_to_none(self):
        """plex_trailer field is None on a freshly created media row."""
        media_data = MediaCreate(
            connection_id=self.conn.id,  # type: ignore
            arr_id=3,
            is_movie=True,
            title="Another Movie",
            txdb_id="tt9991004",
        )
        created = media_manager.create(media_data)
        assert created.plex_trailer is None


class TestCreateOrUpdateBulkUpdatePaths:
    """Covers update/counter branches of create_or_update_bulk (lines 69-72)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()

    def _mc(self, txdb_id: str, title: str = "Film", yt_id: str | None = None) -> MediaCreate:
        return MediaCreate(
            connection_id=self.conn.id,  # type: ignore
            arr_id=100,
            is_movie=True,
            title=title,
            txdb_id=txdb_id,
            youtube_trailer_id=yt_id,
        )

    def test_update_existing_item_increments_updated_count(self):
        """Updating an existing row increments updated_count (lines 71-72) and
        returns created=False.

        has_updated detects a change when the DB has a non-default value for a
        field that is NOT explicitly set in the new MediaCreate (so
        sqlmodel_update leaves the DB value alone, but model_dump() returns the
        field's default — different from the DB value).
        """
        # Create with arr_monitored=True explicitly set
        mc = MediaCreate(
            connection_id=self.conn.id,  # type: ignore
            arr_id=100,
            is_movie=True,
            title="Film",
            txdb_id="tt_upd_001_v2",
            arr_monitored=True,
        )
        result1 = media_manager.create_or_update_bulk([mc])
        _, created, _, _ = result1[0]
        assert created is True

        # Second call does NOT set arr_monitored → stays False (default).
        # sqlmodel_update skips it (exclude_unset), so DB keeps True.
        # has_updated sees True (DB) vs False (default model_dump) → updated.
        mc2 = self._mc("tt_upd_001_v2", title="Film")
        result2 = media_manager.create_or_update_bulk([mc2])
        _, created2, updated2, _ = result2[0]
        assert created2 is False  # covers 69->71 (created=False branch)
        assert updated2 is True   # covers line 72 (updated_count += 1)

    def test_unchanged_existing_item_returns_not_updated(self):
        """Updating with identical data returns created=False, updated=False."""
        mc = self._mc("tt_upd_002", title="Same Title")
        media_manager.create_or_update_bulk([mc])
        result2 = media_manager.create_or_update_bulk([mc])
        _, created2, updated2, _ = result2[0]
        assert created2 is False
        assert updated2 is False

    def test_youtube_id_added_counts_as_updated(self):
        """Adding a youtube_id to an existing item triggers youtube_id change path
        (lines 239-249) and returns updated=True."""
        mc = self._mc("tt_upd_003", title="YT Movie", yt_id=None)
        media_manager.create_or_update_bulk([mc])

        mc2 = self._mc("tt_upd_003", title="YT Movie", yt_id="dQw4w9WgXcQ")
        result2 = media_manager.create_or_update_bulk([mc2])
        _, created2, updated2, _ = result2[0]
        assert created2 is False
        assert updated2 is True

    def test_invalid_connection_raises(self):
        """_check_connection_exists_bulk raises when connection_id is invalid (line 193)."""
        mc = MediaCreate(
            connection_id=99998,
            arr_id=1,
            is_movie=True,
            title="Ghost",
            txdb_id="tt_inv_001",
        )
        with pytest.raises(ItemNotFoundError):
            media_manager.create_or_update_bulk([mc])


class TestPlexCreateOrUpdateBulk:
    """Edge cases for plex_create_or_update_bulk and _read_plex_only_by_folder_path."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.plex = _make_plex_connection("PlexBulkTest")
        self.radarr = _make_connection()

    def _plex_mc(self, txdb_id: str, folder_path: str, *, title: str = "Film",
                  rating_key: str = "rk1") -> MediaCreate:
        return MediaCreate(
            connection_id=self.plex.id,  # type: ignore
            arr_id=0,
            is_movie=True,
            title=title,
            txdb_id=txdb_id,
            folder_path=folder_path,
            plex_connection_id=self.plex.id,  # type: ignore
            plex_rating_key=rating_key,
            plex_section_key="1",
        )

    def _arr_mc(self, txdb_id: str, folder_path: str, *, title: str = "Film") -> MediaCreate:
        return MediaCreate(
            connection_id=self.radarr.id,  # type: ignore
            arr_id=999,
            is_movie=True,
            title=title,
            txdb_id=txdb_id,
            folder_path=folder_path,
        )

    # ---- empty-list fast-path (line 103) -----------------------------------

    def test_empty_list_returns_empty(self):
        """plex_create_or_update_bulk([]) returns [] without touching the DB."""
        result = media_manager.plex_create_or_update_bulk([])
        assert result == []

    # ---- invalid connection raises (line 193 via _check_connection_exists_bulk)

    def test_invalid_connection_raises(self):
        mc = MediaCreate(
            connection_id=99997,
            arr_id=0,
            is_movie=True,
            title="Ghost",
            txdb_id="tt_ghost",
            plex_connection_id=99997,
            plex_rating_key="rk0",
            plex_section_key="1",
        )
        with pytest.raises(ItemNotFoundError):
            media_manager.plex_create_or_update_bulk([mc])

    # ---- Stage 2 prefix match with forward slash (lines 135-136) -----------

    def test_stage2_forward_slash_prefix_match(self):
        """Stage 2 finds an existing row when stored path is a parent directory
        of the new path (separated by '/')."""
        # Store a show-root folder path
        show_mc = self._plex_mc("tvdb_show_001", "/plex/shows/GreatShow", title="Great Show", rating_key="rk_gs")
        media_manager.plex_create_or_update_bulk([show_mc])

        # New item with episode-level subfolder path — should match via Stage 2
        ep_mc = self._plex_mc("tvdb_show_001b", "/plex/shows/GreatShow/Season 1",
                               title="Great Show (ep)", rating_key="rk_gs_ep")
        result = media_manager.plex_create_or_update_bulk([ep_mc])
        _, created, _, _ = result[0]
        assert created is False  # found via Stage 2 prefix match

    # ---- Stage 2 prefix match with backslash (norm + "\\") -----------------

    def test_stage2_backslash_prefix_match(self):
        """Stage 2 hits the backslash branch when stored path uses Windows separators."""
        win_mc = self._plex_mc("tmdb_win_001", r"C:\Movies\WinFilm", title="Win Film", rating_key="rk_win")
        media_manager.plex_create_or_update_bulk([win_mc])

        # Child path with backslash separator → norm + "\\" branch
        child_mc = self._plex_mc("tmdb_win_001b", r"C:\Movies\WinFilm\extras",
                                  title="Win Film Extras", rating_key="rk_win_e")
        result = media_manager.plex_create_or_update_bulk([child_mc])
        _, created, _, _ = result[0]
        assert created is False  # found via Stage 2 backslash branch

    # ---- Stage 2 with empty-string path in DB (line 130 continue) ----------

    def test_stage2_skips_empty_folder_path_rows(self):
        """Stage 2 skips DB rows where folder_path is an empty string (line 130 continue)."""
        # Create a Plex item with no folder_path (empty string stored in DB)
        no_path_mc = MediaCreate(
            connection_id=self.plex.id,  # type: ignore
            arr_id=0,
            is_movie=True,
            title="No Path Film",
            txdb_id="tmdb_nopath_001",
            folder_path="",
            plex_connection_id=self.plex.id,  # type: ignore
            plex_rating_key="rk_np",
            plex_section_key="1",
        )
        media_manager.plex_create_or_update_bulk([no_path_mc])

        # New item with a real path — Stage 2 should skip the empty-path row
        real_mc = self._plex_mc("tmdb_nopath_002", "/plex/movies/SomeFilm", rating_key="rk_sf")
        result = media_manager.plex_create_or_update_bulk([real_mc])
        _, created, _, _ = result[0]
        assert created is True  # no false match against the empty-path row

    # ---- plex fields changed (not changed) ----------------------------------

    def test_plex_fields_unchanged_returns_not_changed(self):
        """Second sync with identical plex fields: changed=False (no DB write)."""
        mc = self._plex_mc("tmdb_unch_001", "/plex/movies/StableFilm", rating_key="rk_sf2")
        media_manager.plex_create_or_update_bulk([mc])
        result2 = media_manager.plex_create_or_update_bulk([mc])
        _, created2, newly_linked2, changed2 = result2[0]
        assert created2 is False
        assert newly_linked2 is False
        assert changed2 is False

    # ---- arr_linked: _read_plex_only_by_folder_path exact match (line 298) -

    def test_arr_adopts_plex_only_row_exact_path(self):
        """Arr create_or_update_bulk adopts an existing Plex-only row at the exact
        same folder_path (arr_linked=True, line 298 exact match)."""
        plex_mc = self._plex_mc("tmdb_adopt_001", "/plex/movies/AdoptMe", rating_key="rk_adopt")
        media_manager.plex_create_or_update_bulk([plex_mc])

        arr_mc = self._arr_mc("tmdb_adopt_arr_001", "/plex/movies/AdoptMe", title="AdoptMe")
        result = media_manager.create_or_update_bulk([arr_mc])
        _, created, _, arr_linked = result[0]
        assert created is False
        assert arr_linked is True

    # ---- arr_linked via Stage-2 prefix (lines 309-316, 319) ----------------

    def test_arr_adopts_plex_only_row_via_prefix_match(self):
        """Arr create_or_update_bulk adopts a Plex-only row via Stage-2 prefix match
        (lines 309-316 loop body, line 319 return)."""
        show_mc = self._plex_mc("tvdb_adopt_002", "/plex/shows/AdoptShow",
                                 title="Adopt Show", rating_key="rk_adshow")
        media_manager.plex_create_or_update_bulk([show_mc])

        # Arr item's folder is a subfolder of the Plex-only show root
        arr_mc = self._arr_mc("tvdb_adopt_arr_002", "/plex/shows/AdoptShow/Season 1",
                               title="Adopt Show Arr")
        result = media_manager.create_or_update_bulk([arr_mc])
        _, created, _, arr_linked = result[0]
        assert created is False
        assert arr_linked is True
