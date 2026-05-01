"""Tests for media update manager functions."""

import pytest
from sqlmodel import Session

from core.base.database.models.connection import ArrType, Connection, MonitorType
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session
import core.base.database.manager.media as media_manager


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
    """Tests for media_manager.update_plex_trailer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.connection = _create_test_connection()
        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=1,
            is_movie=True,
            title="Test Movie",
            txdb_id="tt9999999",
        )
        result = media_manager.create_or_update_bulk([media_data])
        self.media, _, _, _ = result[0]

    def test_sets_plex_trailer_true(self):
        """Sets plex_trailer to True on a media row."""
        media_manager.update_plex_trailer(self.media.id, True)
        updated = media_manager.read(self.media.id)
        assert updated.plex_trailer is True

    def test_sets_plex_trailer_false(self):
        """Sets plex_trailer to False on a media row."""
        media_manager.update_plex_trailer(self.media.id, False)
        updated = media_manager.read(self.media.id)
        assert updated.plex_trailer is False

    def test_sets_plex_trailer_none(self):
        """Resets plex_trailer to None (unknown state)."""
        # First set it to True, then reset
        media_manager.update_plex_trailer(self.media.id, True)
        media_manager.update_plex_trailer(self.media.id, None)
        updated = media_manager.read(self.media.id)
        assert updated.plex_trailer is None

    def test_plex_trailer_defaults_to_none_on_create(self):
        """New media rows have plex_trailer=None by default."""
        assert self.media.plex_trailer is None

    def test_update_does_not_touch_other_fields(self):
        """update_plex_trailer only changes plex_trailer, not title or status."""
        original_title = self.media.title
        original_status = self.media.status
        media_manager.update_plex_trailer(self.media.id, True)
        updated = media_manager.read(self.media.id)
        assert updated.title == original_title
        assert updated.status == original_status
