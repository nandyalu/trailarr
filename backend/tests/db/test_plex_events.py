"""Tests for Plex-related event helper functions."""

import pytest
from sqlmodel import Session

import db.repos.event as event_repo
import db.repos.media as media_repo
from db.engine import write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.event import EventSource, EventType
from db.models.media import MediaCreate
from services.event_service import (
    track_plex_linked,
    track_plex_unlinked,
    track_plex_scan_triggered,
)


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


class TestTrackPlexLinked:
    """Tests for track_plex_linked event helper."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()
        result = media_repo.create_or_update_bulk([
            MediaCreate(
                connection_id=self.conn.id,  # type: ignore
                arr_id=1,
                is_movie=True,
                title="Linked Movie",
                tmdb_id="tt8881001",
            )
        ])
        self.media, _, _, _, _ = result[0]

    def test_creates_plex_linked_event(self):
        track_plex_linked(
            media_id=self.media.id,
            connection_name="My Plex",
            plex_rating_key="rk42",
            source=EventSource.SYSTEM,
            source_detail="PlexRefresh",
        )
        events = event_repo.read_by_media_id(self.media.id)
        plex_events = [e for e in events if e.event_type == EventType.PLEX_LINKED]
        assert len(plex_events) == 1
        evt = plex_events[0]
        assert evt.new_value == "My Plex"
        assert evt.old_value == "rk42"
        assert evt.source == EventSource.SYSTEM
        assert evt.source_detail == "PlexRefresh"

    def test_does_not_raise_on_invalid_media_id(self):
        track_plex_linked(
            media_id=99999,
            connection_name="Plex",
            plex_rating_key="rk1",
        )  # should not raise


class TestTrackPlexUnlinked:
    """Tests for track_plex_unlinked event helper."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()
        result = media_repo.create_or_update_bulk([
            MediaCreate(
                connection_id=self.conn.id,  # type: ignore
                arr_id=2,
                is_movie=True,
                title="Unlinked Movie",
                tmdb_id="tt8882001",
            )
        ])
        self.media, _, _, _, _ = result[0]

    def test_creates_plex_unlinked_event(self):
        track_plex_unlinked(
            media_id=self.media.id,
            connection_name="Old Plex",
            source=EventSource.SYSTEM,
            source_detail="ConnectionDeleted",
        )
        events = event_repo.read_by_media_id(self.media.id)
        plex_events = [e for e in events if e.event_type == EventType.PLEX_UNLINKED]
        assert len(plex_events) == 1
        evt = plex_events[0]
        assert evt.old_value == "Old Plex"
        assert evt.source == EventSource.SYSTEM
        assert evt.source_detail == "ConnectionDeleted"

    def test_does_not_raise_on_invalid_media_id(self):
        track_plex_unlinked(media_id=99999, connection_name="Plex")


class TestTrackPlexScanTriggered:
    """Tests for track_plex_scan_triggered event helper."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn = _make_connection()
        result = media_repo.create_or_update_bulk([
            MediaCreate(
                connection_id=self.conn.id,  # type: ignore
                arr_id=3,
                is_movie=True,
                title="Scanned Movie",
                tmdb_id="tt8883001",
            )
        ])
        self.media, _, _, _, _ = result[0]

    def test_creates_plex_scan_triggered_event(self):
        track_plex_scan_triggered(
            media_id=self.media.id,
            scan_path="/plex/media/movies/Scanned Movie",
            source=EventSource.SYSTEM,
            source_detail="TrailerDownloaded",
        )
        events = event_repo.read_by_media_id(self.media.id)
        scan_events = [e for e in events if e.event_type == EventType.PLEX_SCAN_TRIGGERED]
        assert len(scan_events) == 1
        evt = scan_events[0]
        assert evt.new_value == "/plex/media/movies/Scanned Movie"
        assert evt.source_detail == "TrailerDownloaded"

    def test_does_not_raise_on_invalid_media_id(self):
        track_plex_scan_triggered(media_id=99999, scan_path="/some/path")
