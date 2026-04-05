"""Tests for the Event manager."""

import pytest
from sqlmodel import Session

from core.base.database.models.connection import (
    ArrType,
    Connection,
    MonitorType,
)
from core.base.database.utils.engine import write_session
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.event import (
    EventCreate,
    EventSource,
    EventType,
)
from core.base.database.models.media import MediaCreate
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


class TestEventManager:
    """Tests for Event manager CRUD operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Create a test connection directly (without async validation)
        self.connection = _create_test_connection()

        # Create a test media item
        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=1,
            is_movie=True,
            title="Test Movie",
            txdb_id="tt1234567",
        )
        result = media_manager.create_or_update_bulk([media_data])
        self.media, _, _ = result[0]

    def test_create_event(self):
        """Test creating a new event."""
        event_data = EventCreate(
            media_id=self.media.id,
            event_type=EventType.MEDIA_ADDED,
            source=EventSource.USER,
            new_value="Radarr",
        )
        event = event_manager.create(event_data)

        assert event.id is not None
        assert event.media_id == self.media.id
        assert event.event_type == EventType.MEDIA_ADDED
        assert event.source == EventSource.USER
        assert event.new_value == "Radarr"
        assert event.created_at is not None

    def test_read_event(self):
        """Test reading an event by ID."""
        event_data = EventCreate(
            media_id=self.media.id,
            event_type=EventType.TRAILER_DOWNLOADED,
            source=EventSource.SYSTEM,
            source_detail="DownloadTask",
            new_value="abcdefghijk",
        )
        created_event = event_manager.create(event_data)

        read_event = event_manager.read(created_event.id)

        assert read_event.id == created_event.id
        assert read_event.event_type == EventType.TRAILER_DOWNLOADED
        assert read_event.source_detail == "DownloadTask"

    def test_read_event_not_found(self):
        """Test reading a non-existent event raises error."""
        with pytest.raises(ItemNotFoundError):
            event_manager.read(99999)

    def test_read_all_events(self):
        """Test reading all events with filters."""
        # Create multiple events
        event_manager.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MEDIA_ADDED,
                source=EventSource.SYSTEM,
            )
        )
        event_manager.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MONITOR_CHANGED,
                source=EventSource.USER,
            )
        )

        # Get all events
        all_events = event_manager.read_all()
        assert len(all_events) >= 2

        # Filter by event type
        media_added_events = event_manager.read_all(
            event_type=EventType.MEDIA_ADDED
        )
        assert all(
            e.event_type == EventType.MEDIA_ADDED for e in media_added_events
        )

        # Filter by media_id
        media_events = event_manager.read_all(media_id=self.media.id)
        assert all(e.media_id == self.media.id for e in media_events)

    def test_read_by_media_id(self):
        """Test reading events for a specific media item."""
        event_manager.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.YOUTUBE_ID_CHANGED,
                source=EventSource.USER,
                old_value="",
                new_value="abcdefghijk",
            )
        )

        events = event_manager.read_by_media_id(self.media.id)
        assert len(events) >= 1
        assert all(e.media_id == self.media.id for e in events)

    def test_create_skip_event_if_not_exists(self):
        """Test creating a skip event only once per media with same reason."""
        # First skip event should be created
        event1, created1 = event_manager.create_skip_event_if_not_exists(
            media_id=self.media.id,
            skip_reason="no_folder_path",
            source_detail="DownloadTask",
        )
        assert created1 is True
        assert event1 is not None

        # Second attempt with SAME reason should return None (already exists)
        event2, created2 = event_manager.create_skip_event_if_not_exists(
            media_id=self.media.id,
            skip_reason="no_folder_path",
            source_detail="DownloadTask",
        )
        assert created2 is False
        assert event2 is None

        # Third attempt with DIFFERENT reason should create new event
        event3, created3 = event_manager.create_skip_event_if_not_exists(
            media_id=self.media.id,
            skip_reason="different_reason",
            source_detail="DownloadTask",
        )
        assert created3 is True
        assert event3 is not None
        assert event3.new_value == "different_reason"

    def test_has_skip_event(self):
        """Test checking if a skip event exists."""
        # Initially no skip event
        assert event_manager.has_skip_event(self.media.id) is False

        # Create skip event
        event_manager.create_skip_event_if_not_exists(
            media_id=self.media.id,
            skip_reason="folder_not_found",
        )

        # Now should return True
        assert event_manager.has_skip_event(self.media.id) is True

    def test_delete_by_media_id(self):
        """Test deleting all events for a media item."""
        # Create multiple events
        event_manager.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MEDIA_ADDED,
                source=EventSource.SYSTEM,
            )
        )
        event_manager.create(
            EventCreate(
                media_id=self.media.id,
                event_type=EventType.MONITOR_CHANGED,
                source=EventSource.USER,
            )
        )

        # Delete all events for the media
        count = event_manager.delete_by_media_id(self.media.id)
        assert count >= 2

        # Verify they're deleted
        events = event_manager.read_by_media_id(self.media.id)
        assert len(events) == 0


class TestEventHelpers:
    """Tests for Event helper functions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Create a test connection directly (without async validation)
        self.connection = _create_test_connection(name="Test Connection 2")

        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=2,
            is_movie=True,
            title="Test Movie 2",
            txdb_id="tt7654321",
        )
        result = media_manager.create_or_update_bulk([media_data])
        self.media, _, _ = result[0]

    def test_track_media_added(self):
        """Test tracking media_added event creates media_added, youtube_id, and monitor events."""
        # Create a media with youtube_id and monitor for testing
        media_data = MediaCreate(
            connection_id=self.connection.id,  # type: ignore
            arr_id=99,
            is_movie=True,
            title="Test Movie For Events",
            txdb_id="tt9999999",
            youtube_trailer_id="test_yt_id",
            monitor=True,
        )
        result = media_manager.create_or_update_bulk([media_data])
        test_media, _, _ = result[0]

        event_manager.track_media_added(
            media=test_media,
            connection_name="Radarr",
            source=EventSource.SYSTEM,
            source_detail="ConnectionRefresh",
        )

        events = event_manager.read_by_media_id(test_media.id)

        # Check media_added event
        media_added_events = [
            e for e in events if e.event_type == EventType.MEDIA_ADDED
        ]
        assert len(media_added_events) >= 1
        assert media_added_events[0].new_value == "Radarr"

        # Check youtube_id_changed event
        yt_events = [
            e for e in events if e.event_type == EventType.YOUTUBE_ID_CHANGED
        ]
        assert len(yt_events) >= 1
        assert yt_events[0].new_value == "test_yt_id"

        # Check monitor_changed event
        monitor_events = [
            e for e in events if e.event_type == EventType.MONITOR_CHANGED
        ]
        assert len(monitor_events) >= 1
        assert monitor_events[0].new_value == "true"

    def test_track_monitor_changed(self):
        """Test tracking monitor_changed event."""
        event_manager.track_monitor_changed(
            media_id=self.media.id,
            old_monitor=False,
            new_monitor=True,
            source=EventSource.USER,
        )

        events = event_manager.read_by_media_id(self.media.id)
        monitor_events = [
            e for e in events if e.event_type == EventType.MONITOR_CHANGED
        ]
        assert len(monitor_events) >= 1
        assert monitor_events[0].old_value == "false"
        assert monitor_events[0].new_value == "true"

    def test_track_youtube_id_changed(self):
        """Test tracking youtube_id_changed event."""
        event_manager.track_youtube_id_changed(
            media_id=self.media.id,
            old_yt_id="oldid123456",
            new_yt_id="newid123456",
            source=EventSource.USER,
        )

        events = event_manager.read_by_media_id(self.media.id)
        yt_events = [
            e for e in events if e.event_type == EventType.YOUTUBE_ID_CHANGED
        ]
        assert len(yt_events) >= 1
        assert yt_events[0].old_value == "oldid123456"
        assert yt_events[0].new_value == "newid123456"

    def test_track_download_skipped_once(self):
        """Test that download_skipped is only tracked once per media with same reason."""
        # First call should create event
        created1 = event_manager.track_download_skipped(
            media_id=self.media.id,
            skip_reason="no_folder_path",
            source_detail="DownloadTask",
        )
        assert created1 is True

        # Second call with SAME reason should not create event
        created2 = event_manager.track_download_skipped(
            media_id=self.media.id,
            skip_reason="no_folder_path",
        )
        assert created2 is False

        # Third call with DIFFERENT reason should create event
        created3 = event_manager.track_download_skipped(
            media_id=self.media.id,
            skip_reason="different_reason",
        )
        assert created3 is True
