"""Tests for the Event repository and event_service helpers."""

import pytest
from sqlmodel import Session

import db.repos.event as event_repo
import db.repos.media as media_repo
from db.engine import write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.event import EventCreate, EventSource, EventType
from db.models.media import MediaCreate
from exceptions import ItemNotFoundError


@write_session
def _create_test_connection(
    name: str = "Test Connection",
    *,
    _session: Session = None,  # type: ignore
) -> Connection:
    """Create a test connection directly in the database (bypasses async validation)."""
    connection = Connection(
        name=name,
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_api_key",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(connection)
    _session.commit()
    _session.refresh(connection)
    return connection


class TestEventRepo:
    """Tests for Event repo CRUD operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.connection = _create_test_connection()
        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=1,
            is_movie=True,
            title="Test Movie",
            txdb_id="tt1234567",
        )
        result = media_repo.create_or_update_bulk([media_data])
        self.media, _, _, _ = result[0]

    def test_create_event(self):
        event_data = EventCreate(
            media_id=self.media.id,
            event_type=EventType.MEDIA_ADDED,
            source=EventSource.USER,
            new_value="Radarr",
        )
        event = event_repo.create(event_data)

        assert event.id is not None
        assert event.media_id == self.media.id
        assert event.event_type == EventType.MEDIA_ADDED
        assert event.source == EventSource.USER
        assert event.new_value == "Radarr"
        assert event.created_at is not None

    def test_read_event(self):
        event_data = EventCreate(
            media_id=self.media.id,
            event_type=EventType.TRAILER_DOWNLOADED,
            source=EventSource.SYSTEM,
            source_detail="DownloadTask",
            new_value="abcdefghijk",
        )
        created_event = event_repo.create(event_data)
        read_event = event_repo.read(created_event.id)

        assert read_event.id == created_event.id
        assert read_event.event_type == EventType.TRAILER_DOWNLOADED
        assert read_event.source_detail == "DownloadTask"

    def test_read_event_not_found(self):
        with pytest.raises(ItemNotFoundError):
            event_repo.read(99999)

    def test_read_all_events(self):
        event_repo.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MEDIA_ADDED,
                source=EventSource.SYSTEM,
            )
        )
        event_repo.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MONITOR_CHANGED,
                source=EventSource.USER,
            )
        )

        all_events = event_repo.read_all()
        assert len(all_events) >= 2

        media_added_events = event_repo.read_all(event_type=EventType.MEDIA_ADDED)
        assert all(e.event_type == EventType.MEDIA_ADDED for e in media_added_events)

        media_events = event_repo.read_all(media_id=self.media.id)
        assert all(e.media_id == self.media.id for e in media_events)

    def test_read_by_media_id(self):
        event_repo.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.YOUTUBE_ID_CHANGED,
                source=EventSource.USER,
                old_value="",
                new_value="abcdefghijk",
            )
        )

        events = event_repo.read_by_media_id(self.media.id)
        assert len(events) >= 1
        assert all(e.media_id == self.media.id for e in events)

    def test_create_skip_event_if_not_exists(self):
        event1, created1 = event_repo.create_skip_if_not_exists(
            media_id=self.media.id,
            skip_reason="no_folder_path",
            source_detail="DownloadTask",
        )
        assert created1 is True
        assert event1 is not None

        event2, created2 = event_repo.create_skip_if_not_exists(
            media_id=self.media.id,
            skip_reason="no_folder_path",
            source_detail="DownloadTask",
        )
        assert created2 is False
        assert event2 is None

        event3, created3 = event_repo.create_skip_if_not_exists(
            media_id=self.media.id,
            skip_reason="different_reason",
            source_detail="DownloadTask",
        )
        assert created3 is True
        assert event3 is not None
        assert event3.new_value == "different_reason"

    def test_has_skip_event(self):
        assert event_repo.has_skip_event(self.media.id) is False

        event_repo.create_skip_if_not_exists(
            media_id=self.media.id,
            skip_reason="folder_not_found",
        )

        assert event_repo.has_skip_event(self.media.id) is True

    def test_delete_by_media_id(self):
        event_repo.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MEDIA_ADDED,
                source=EventSource.SYSTEM,
            )
        )
        event_repo.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MONITOR_CHANGED,
                source=EventSource.USER,
            )
        )

        count = event_repo.delete_by_media_id(self.media.id)
        assert count >= 2

        events = event_repo.read_by_media_id(self.media.id)
        assert len(events) == 0


class TestEventServiceHelpers:
    """Tests for event_service helper functions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.connection = _create_test_connection(name="Test Connection 2")

        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=2,
            is_movie=True,
            title="Test Movie 2",
            txdb_id="tt7654321",
        )
        result = media_repo.create_or_update_bulk([media_data])
        self.media, _, _, _ = result[0]

    def test_track_media_added(self):
        from services import event_service

        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=99,
            is_movie=True,
            title="Test Movie For Events",
            txdb_id="tt9999999",
            youtube_trailer_id="test_yt_id",
            monitor=True,
        )
        result = media_repo.create_or_update_bulk([media_data])
        test_media, _, _, _ = result[0]

        event_service.track_media_added(
            media=test_media,
            connection_name="Radarr",
            source=EventSource.SYSTEM,
            source_detail="ConnectionRefresh",
        )

        events = event_repo.read_by_media_id(test_media.id)

        media_added_events = [e for e in events if e.event_type == EventType.MEDIA_ADDED]
        assert len(media_added_events) >= 1
        assert media_added_events[0].new_value == "Radarr"

        yt_events = [e for e in events if e.event_type == EventType.YOUTUBE_ID_CHANGED]
        assert len(yt_events) >= 1
        assert yt_events[0].new_value == "test_yt_id"

        monitor_events = [e for e in events if e.event_type == EventType.MONITOR_CHANGED]
        assert len(monitor_events) >= 1
        assert monitor_events[0].new_value == "true"

    def test_track_monitor_changed(self):
        from services import event_service

        event_service.track_monitor_changed(
            media_id=self.media.id,
            old_monitor=False,
            new_monitor=True,
            source=EventSource.USER,
        )

        events = event_repo.read_by_media_id(self.media.id)
        monitor_events = [e for e in events if e.event_type == EventType.MONITOR_CHANGED]
        assert len(monitor_events) >= 1
        assert monitor_events[0].old_value == "false"
        assert monitor_events[0].new_value == "true"

    def test_track_youtube_id_changed(self):
        from services import event_service

        event_service.track_youtube_id_changed(
            media_id=self.media.id,
            old_yt_id="oldid123456",
            new_yt_id="newid123456",
            source=EventSource.USER,
        )

        events = event_repo.read_by_media_id(self.media.id)
        yt_events = [e for e in events if e.event_type == EventType.YOUTUBE_ID_CHANGED]
        assert len(yt_events) >= 1
        assert yt_events[0].old_value == "oldid123456"
        assert yt_events[0].new_value == "newid123456"

    def test_track_download_skipped_once(self):
        from services import event_service

        created1 = event_service.track_download_skipped(
            media_id=self.media.id,
            skip_reason="no_folder_path",
            source_detail="DownloadTask",
        )
        assert created1 is True

        created2 = event_service.track_download_skipped(
            media_id=self.media.id,
            skip_reason="no_folder_path",
        )
        assert created2 is False

        created3 = event_service.track_download_skipped(
            media_id=self.media.id,
            skip_reason="different_reason",
        )
        assert created3 is True
