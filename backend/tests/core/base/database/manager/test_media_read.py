"""Tests for media read manager functions."""

import math
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import event
from sqlmodel import Session

from core.base.database.models.connection import ArrType, Connection
from core.base.database.models.download import DownloadCreate
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import engine, write_session
from core.base.database.manager.media.read import _MEDIA_BATCH_SIZE
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager


@write_session
def _make_connection(
    name: str = "Test Connection",
    arr_type: ArrType = ArrType.RADARR,
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    conn = Connection(
        name=name,
        arr_type=arr_type,
        url="http://localhost:7878",
        api_key="test_key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


def _make_media(
    connection_id: int,
    txdb_id: str,
    folder_path: str | None = None,
    monitor: bool = False,
) -> MediaCreate:
    return MediaCreate(
        connection_id=connection_id,
        arr_id=1,
        is_movie=True,
        title=f"Media {txdb_id}",
        txdb_id=txdb_id,
        folder_path=folder_path,
        monitor=monitor,
    )


class TestReadByFolderPath:
    """Tests for media_manager.read_by_folder_path."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()
        cid = self.conn.id
        # Embed connection ID in paths so each test fixture has unique paths
        self.movie_path = f"/media/movies/Movie{cid} (2020)"
        self.show_path = f"/media/tv/Show{cid}"
        result = media_manager.create_or_update_bulk([
            _make_media(cid, f"tt000{cid}1", self.movie_path),
            _make_media(cid, f"tt000{cid}2", self.show_path),
        ])
        self.movie, _, _, _ = result[0]
        self.show, _, _, _ = result[1]

    def test_exact_match_returns_media(self):
        """Stage 1: exact folder_path match finds the item."""
        found = media_manager.read_by_folder_path(self.movie_path)
        assert found is not None
        assert found.id == self.movie.id

    def test_prefix_match_finds_parent_path(self):
        """Stage 2: Plex gives season subfolder; DB has show root — prefix match."""
        found = media_manager.read_by_folder_path(f"{self.show_path}/Season 01")
        assert found is not None
        assert found.id == self.show.id

    def test_prefix_match_finds_deeply_nested_path(self):
        """Prefix match works for paths nested more than one level deep."""
        found = media_manager.read_by_folder_path(
            f"{self.show_path}/Season 02/Episode 03"
        )
        assert found is not None
        assert found.id == self.show.id

    def test_returns_none_when_no_match(self):
        """Returns None when no exact or prefix match exists."""
        found = media_manager.read_by_folder_path("/media/movies/DoesNotExistXYZ")
        assert found is None

    def test_exact_match_takes_priority_over_prefix(self):
        """Stage 1 fires first; an exact match is returned even if a prefix would also match."""
        found = media_manager.read_by_folder_path(self.movie_path)
        assert found is not None
        assert found.id == self.movie.id

    def test_returns_none_for_empty_path(self):
        """Empty string returns None (no stored path is empty)."""
        found = media_manager.read_by_folder_path("")
        assert found is None

    def test_stage2_skips_empty_stored_path(self):
        """Stage 2 skips rows with empty folder_path (line 225 continue).

        A media row with folder_path='' exists in the DB; a lookup for a real
        path must not falsely match it.
        """
        # Create a row with empty folder_path so it lands in all_id_paths
        cid = self.conn.id
        empty_mc = _make_media(cid, f"tt_empty_{cid}", folder_path="")
        media_manager.create_or_update_bulk([empty_mc])

        # Look up a real path — should not match the empty-path row
        found = media_manager.read_by_folder_path(f"/media/movies/Movie{cid}X (2021)")
        assert found is None

    def test_stage2_backslash_separator(self):
        """Stage 2 matches when the stored path uses Windows backslash separators."""
        cid = self.conn.id
        win_path = f"C:\\Media\\Show{cid}"
        win_mc = _make_media(cid, f"tt_win_{cid}", folder_path=win_path)
        media_manager.create_or_update_bulk([win_mc])

        # Child path with backslash separator
        found = media_manager.read_by_folder_path(f"{win_path}\\Season 1")
        assert found is not None
        assert found.txdb_id == f"tt_win_{cid}"

    def test_stage2_trailing_slash_on_stored_path(self):
        """Stage 2 normalises trailing slashes before comparing (rstrip)."""
        cid = self.conn.id
        # Store path WITH trailing slash
        trailing_mc = _make_media(cid, f"tt_trail_{cid}", folder_path=f"/media/tv/Trail{cid}/")
        media_manager.create_or_update_bulk([trailing_mc])

        # Child path with forward slash should still match
        found = media_manager.read_by_folder_path(f"/media/tv/Trail{cid}/Season 2")
        assert found is not None
        assert found.txdb_id == f"tt_trail_{cid}"


class TestReadArrLinkedToPlexConnection:
    """Tests for media_manager.read_arr_linked_to_plex_connection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.radarr_conn = _make_connection("Radarr", ArrType.RADARR)
        self.plex_conn = _make_connection("Plex", ArrType.PLEX)

        # Arr-sourced row linked to Plex via folder matching
        result = media_manager.create_or_update_bulk([
            _make_media(self.radarr_conn.id, "tt1111111", "/media/movies/Linked"),
        ])
        self.arr_media, _, _, _ = result[0]
        media_manager.update_plex_fields(
            media_id=self.arr_media.id,
            plex_rating_key="rk1",
            plex_section_key="1",
            plex_connection_id=self.plex_conn.id,
        )

        # Plex-only row (connection_id == plex_connection_id)
        result2 = media_manager.create_or_update_bulk([
            _make_media(self.plex_conn.id, "tt2222222", "/media/movies/PlexOnly"),
        ])
        self.plex_only, _, _, _ = result2[0]
        media_manager.update_plex_fields(
            media_id=self.plex_only.id,
            plex_rating_key="rk2",
            plex_section_key="1",
            plex_connection_id=self.plex_conn.id,
        )

    def test_returns_arr_linked_rows(self):
        """Returns Arr-sourced rows that are linked to the Plex connection."""
        rows = media_manager.read_arr_linked_to_plex_connection(self.plex_conn.id)
        ids = [r.id for r in rows]
        assert self.arr_media.id in ids

    def test_excludes_plex_only_rows(self):
        """Does not return rows where connection_id == plex_connection_id."""
        rows = media_manager.read_arr_linked_to_plex_connection(self.plex_conn.id)
        ids = [r.id for r in rows]
        assert self.plex_only.id not in ids

    def test_returns_empty_for_unknown_connection(self):
        """Returns empty list for a connection id with no linked media."""
        rows = media_manager.read_arr_linked_to_plex_connection(99999)
        assert rows == []


class TestReadAllGeneratorSessionLifecycle:
    """Verify that the finally: _session.close() in read_all_generator works.

    @read_session on a generator function closes the session *before* the body
    runs (it just gets the generator object back, then exits). When the body
    eventually runs it re-acquires a connection. The finally block is the only
    thing that returns that connection to the pool.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection("GenLifecycleConn")

    def test_session_closed_when_generator_exhausted(self):
        """finally block fires when the generator is fully consumed via iteration."""
        close_calls = 0
        real_close = Session.close

        def spy(self_s):
            nonlocal close_calls
            close_calls += 1
            real_close(self_s)

        with patch.object(Session, "close", spy):
            before = close_calls
            list(media_manager.read_all_generator())  # exhaust the generator
            after = close_calls

        # At minimum 2 closes:
        #   1. decorator's get_session() exits before body runs
        #   2. finally: _session.close() after body exits
        assert after - before >= 2

    def test_session_closed_when_generator_closed_early(self):
        """finally block fires when .close() is called mid-iteration.

        This is the pattern used by download_missing_trailers: find the first
        matching item, call db_media_list.close(), then process it. Without the
        finally block the re-acquired connection would leak.
        """
        # Seed a real row so the generator has something to yield and pause at.
        # (close() on a never-started generator skips the body; next() must be
        # called first to enter the try block and reach the yield.)
        media_manager.create_or_update_bulk([
            _make_media(self.conn.id, "tt_gen_early_close_lifecycle")
        ])

        close_calls = 0
        real_close = Session.close

        def spy(self_s):
            nonlocal close_calls
            close_calls += 1
            real_close(self_s)

        with patch.object(Session, "close", spy):
            gen = media_manager.read_all_generator()
            next(gen)               # enters the body, pauses at the yield
            before_close = close_calls
            gen.close()             # GeneratorExit → finally: _session.close()
            after_close = close_calls

        # The finally block must have added exactly one more close call
        assert after_close == before_close + 1

    def test_monitored_generator_eager_loads_downloads_in_bounded_queries(
        self,
    ):
        """The monitored scan loads downloads without one query per row.

        The assertion is a bound relative to the rows actually returned,
        not an exact count: this suite shares one database, so any other
        test that adds monitored media changes how many batches the scan
        needs."""
        row_count = 24
        created = media_manager.create_or_update_bulk(
            [
                _make_media(
                    self.conn.id,
                    f"tt_gen_eager_{index}",
                    monitor=True,
                )
                for index in range(row_count)
            ]
        )
        media_id = created[0][0].id
        now = datetime.now(timezone.utc)
        download_manager.create(
            DownloadCreate(
                media_id=media_id,
                path="/trailers/test.mkv",
                file_name="test.mkv",
                file_hash="hash",
                size=1,
                resolution=1080,
                file_format="mkv",
                video_format="h264",
                audio_format="aac",
                profile_id=7,
                added_at=now,
                updated_at=now,
            )
        )
        select_count = 0

        def count_selects(*args):
            nonlocal select_count
            statement = args[2]
            if statement.lstrip().upper().startswith("SELECT"):
                select_count += 1

        event.listen(engine, "before_cursor_execute", count_selects)
        try:
            rows = list(media_manager.read_all_generator(monitored_only=True))
        finally:
            event.remove(engine, "before_cursor_execute", count_selects)

        created_ids = {item[0].id for item in created}
        created_rows = [row for row in rows if row.id in created_ids]
        assert len(created_rows) == row_count
        row_with_download = next(
            row for row in created_rows if row.id == media_id
        )
        assert row_with_download.downloads[0].profile_id == 7

        # One media query and one downloads query per batch. Lazy loading
        # would instead cost one query per row.
        batches = math.ceil(len(rows) / _MEDIA_BATCH_SIZE)
        assert select_count <= 2 * batches + 1
        assert select_count < len(rows)
