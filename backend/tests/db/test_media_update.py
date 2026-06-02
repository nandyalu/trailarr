"""Tests for media update repo functions."""

import pytest
from sqlmodel import Session

import db.repos.media as media_repo
from db.engine import write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.media import MediaCreate


@write_session
def _create_test_connection(
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    connection = Connection(
        name="Test Plex Connection",
        arr_type=ArrType.PLEX,
        url="http://localhost:32400",
        api_key="test-token",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(connection)
    _session.commit()
    _session.refresh(connection)
    return connection


class TestUpdatePlexTrailer:
    """Tests for media_repo.update_plex_trailer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.connection = _create_test_connection()
        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=1,
            is_movie=True,
            title="Test Movie",
            tmdb_id="tt9999999",
        )
        result = media_repo.create_or_update_bulk([media_data])
        self.media, _, _, _, _ = result[0]

    def test_sets_plex_trailer_true(self):
        media_repo.update_plex_trailer(self.media.id, True)
        updated = media_repo.read(self.media.id)
        assert updated.plex_trailer is True

    def test_sets_plex_trailer_false(self):
        media_repo.update_plex_trailer(self.media.id, False)
        updated = media_repo.read(self.media.id)
        assert updated.plex_trailer is False

    def test_sets_plex_trailer_none(self):
        media_repo.update_plex_trailer(self.media.id, True)
        media_repo.update_plex_trailer(self.media.id, None)
        updated = media_repo.read(self.media.id)
        assert updated.plex_trailer is None

    def test_plex_trailer_defaults_to_none_on_create(self):
        assert self.media.plex_trailer is None

    def test_update_does_not_touch_other_fields(self):
        original_title = self.media.title
        original_year = self.media.year
        media_repo.update_plex_trailer(self.media.id, True)
        updated = media_repo.read(self.media.id)
        assert updated.title == original_title
        assert updated.year == original_year
