"""Tests for media read repo functions."""

import pytest
from sqlmodel import Session

import db.repos.media as media_repo
from db.engine import write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.media import MediaCreate


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
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


def _make_media(connection_id: int, tmdb_id: str, folder_path: str | None = None) -> MediaCreate:
    return MediaCreate(
        connection_id=connection_id,
        arr_id=1,
        is_movie=True,
        title=f"Media {tmdb_id}",
        tmdb_id=tmdb_id,
        folder_path=folder_path,
    )


class TestReadByFolderPath:
    """Tests for media_repo.read_by_folder_path."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()
        cid = self.conn.id
        self.movie_path = f"/media/movies/Movie{cid} (2020)"
        self.show_path = f"/media/tv/Show{cid}"
        result = media_repo.create_or_update_bulk([
            _make_media(cid, f"tt000{cid}1", self.movie_path),
            _make_media(cid, f"tt000{cid}2", self.show_path),
        ])
        self.movie, _, _, _, _ = result[0]
        self.show, _, _, _, _ = result[1]

    def test_exact_match_returns_media(self):
        found = media_repo.read_by_folder_path(self.movie_path)
        assert found is not None
        assert found.id == self.movie.id

    def test_prefix_match_finds_parent_path(self):
        found = media_repo.read_by_folder_path(f"{self.show_path}/Season 01")
        assert found is not None
        assert found.id == self.show.id

    def test_prefix_match_finds_deeply_nested_path(self):
        found = media_repo.read_by_folder_path(
            f"{self.show_path}/Season 02/Episode 03"
        )
        assert found is not None
        assert found.id == self.show.id

    def test_returns_none_when_no_match(self):
        found = media_repo.read_by_folder_path("/media/movies/DoesNotExistXYZ")
        assert found is None

    def test_exact_match_takes_priority_over_prefix(self):
        found = media_repo.read_by_folder_path(self.movie_path)
        assert found is not None
        assert found.id == self.movie.id

    def test_returns_none_for_empty_path(self):
        found = media_repo.read_by_folder_path("")
        assert found is None


class TestReadArrLinkedToPlexConnection:
    """Tests for media_repo.read_arr_linked_to_plex_connection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.radarr_conn = _make_connection("Radarr", ArrType.RADARR)
        self.plex_conn = _make_connection("Plex", ArrType.PLEX)

        result = media_repo.create_or_update_bulk([
            _make_media(self.radarr_conn.id, "tt1111111", "/media/movies/Linked"),
        ])
        self.arr_media, _, _, _, _ = result[0]
        media_repo.update_plex_fields(
            media_id=self.arr_media.id,
            plex_rating_key="rk1",
            plex_section_key="1",
            plex_connection_id=self.plex_conn.id,
        )

        result2 = media_repo.create_or_update_bulk([
            _make_media(self.plex_conn.id, "tt2222222", "/media/movies/PlexOnly"),
        ])
        self.plex_only, _, _, _, _ = result2[0]
        media_repo.update_plex_fields(
            media_id=self.plex_only.id,
            plex_rating_key="rk2",
            plex_section_key="1",
            plex_connection_id=self.plex_conn.id,
        )

    def test_returns_arr_linked_rows(self):
        rows = media_repo.read_arr_linked_to_plex_connection(self.plex_conn.id)
        ids = [r.id for r in rows]
        assert self.arr_media.id in ids

    def test_excludes_plex_only_rows(self):
        rows = media_repo.read_arr_linked_to_plex_connection(self.plex_conn.id)
        ids = [r.id for r in rows]
        assert self.plex_only.id not in ids

    def test_returns_empty_for_unknown_connection(self):
        rows = media_repo.read_arr_linked_to_plex_connection(99999)
        assert rows == []
