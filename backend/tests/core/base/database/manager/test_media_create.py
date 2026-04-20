"""Tests for media create manager functions."""

import pytest
from sqlmodel import Session

from core.base.database.models.connection import ArrType, Connection, MonitorType
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session
import core.base.database.manager.media as media_manager
from exceptions import ItemNotFoundError


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
