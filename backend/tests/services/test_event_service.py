"""Comprehensive tests for services/event_service.py."""

from unittest.mock import MagicMock, call, patch

import pytest

from db.models.event import EventCreate, EventSource, EventType
from services import event_service


class TestFireHelper:
    """Tests for the internal _fire helper — exception suppression."""

    def test_fire_calls_event_repo_create(self):
        event = EventCreate(media_id=1, event_type=EventType.MEDIA_ADDED, source=EventSource.SYSTEM)
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service._fire(event)
        mock_create.assert_called_once_with(event)

    def test_fire_swallows_db_exception(self):
        event = EventCreate(media_id=1, event_type=EventType.MEDIA_ADDED, source=EventSource.SYSTEM)
        with patch("services.event_service.event_repo.create", side_effect=Exception("DB error")):
            # Must NOT raise
            event_service._fire(event)


class TestTrackMediaAdded:

    def test_fires_media_added_and_monitor_changed_no_yt_id(self):
        media = MagicMock()
        media.id = 42
        media.youtube_trailer_id = None
        media.monitor = True

        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_media_added(media, "MyConnection")

        types = [c.args[0].event_type for c in mock_create.call_args_list]
        assert EventType.MEDIA_ADDED in types
        assert EventType.MONITOR_CHANGED in types
        assert EventType.YOUTUBE_ID_CHANGED not in types
        assert len(types) == 2

    def test_fires_three_events_when_yt_id_present(self):
        media = MagicMock()
        media.id = 5
        media.youtube_trailer_id = "abc123"
        media.monitor = False

        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_media_added(media, "TestConn", source=EventSource.USER)

        types = [c.args[0].event_type for c in mock_create.call_args_list]
        assert EventType.MEDIA_ADDED in types
        assert EventType.YOUTUBE_ID_CHANGED in types
        assert EventType.MONITOR_CHANGED in types
        assert len(types) == 3

    def test_media_added_event_carries_connection_name(self):
        media = MagicMock()
        media.id = 10
        media.youtube_trailer_id = None
        media.monitor = False

        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_media_added(media, "RadarrConn")

        added_evt = next(c.args[0] for c in mock_create.call_args_list if c.args[0].event_type == EventType.MEDIA_ADDED)
        assert added_evt.new_value == "RadarrConn"

    def test_monitor_changed_event_carries_monitor_value(self):
        media = MagicMock()
        media.id = 7
        media.youtube_trailer_id = None
        media.monitor = True

        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_media_added(media, "Conn")

        mon_evt = next(c.args[0] for c in mock_create.call_args_list if c.args[0].event_type == EventType.MONITOR_CHANGED)
        assert mon_evt.new_value == "true"
        assert mon_evt.old_value == ""


class TestTrackMonitorChanged:

    def test_fires_monitor_changed_with_correct_values(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_monitor_changed(99, old_monitor=True, new_monitor=False)

        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.MONITOR_CHANGED
        assert evt.old_value == "true"
        assert evt.new_value == "false"
        assert evt.media_id == 99

    def test_source_defaults_to_user(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_monitor_changed(1, False, True)

        evt = mock_create.call_args[0][0]
        assert evt.source == EventSource.USER


class TestTrackYoutubeIdChanged:

    def test_no_event_when_ids_are_the_same(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_youtube_id_changed(1, "abc", "abc")
        mock_create.assert_not_called()

    def test_fires_event_when_ids_differ(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_youtube_id_changed(5, "old", "new")
        mock_create.assert_called_once()
        evt = mock_create.call_args[0][0]
        assert evt.old_value == "old"
        assert evt.new_value == "new"

    def test_fires_event_when_old_is_none(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_youtube_id_changed(3, None, "newid")
        mock_create.assert_called_once()
        evt = mock_create.call_args[0][0]
        assert evt.old_value == ""
        assert evt.new_value == "newid"

    def test_fires_event_when_new_is_none(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_youtube_id_changed(3, "oldid", None)
        mock_create.assert_called_once()
        evt = mock_create.call_args[0][0]
        assert evt.old_value == "oldid"
        assert evt.new_value == ""

    def test_no_event_when_both_none(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_youtube_id_changed(1, None, None)
        mock_create.assert_not_called()


class TestTrackTrailerDownloaded:

    def test_fires_with_yt_id(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_trailer_downloaded(77, "yt123")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.TRAILER_DOWNLOADED
        assert evt.new_value == "yt123"
        assert evt.media_id == 77


class TestTrackTrailerDeleted:

    def test_fires_with_reason(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_trailer_deleted(8, reason="file_not_found")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.TRAILER_DELETED
        assert evt.new_value == "file_not_found"

    def test_fires_with_empty_reason(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_trailer_deleted(8)
        evt = mock_create.call_args[0][0]
        assert evt.new_value == ""


class TestTrackTrailerDetected:

    def test_fires_event(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_trailer_detected(12)
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.TRAILER_DETECTED
        assert evt.media_id == 12


class TestTrackPlexLinked:

    def test_fires_with_connection_name_and_rating_key(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_plex_linked(3, "PlexConn", "rk99")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.PLEX_LINKED
        assert evt.new_value == "PlexConn"
        assert evt.old_value == "rk99"


class TestTrackPlexUnlinked:

    def test_fires_with_connection_name(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_plex_unlinked(4, "PlexConn")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.PLEX_UNLINKED
        assert evt.old_value == "PlexConn"


class TestTrackPlexScanTriggered:

    def test_fires_with_scan_path(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_plex_scan_triggered(9, "/media/movies/Test")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.PLEX_SCAN_TRIGGERED
        assert evt.new_value == "/media/movies/Test"


class TestTrackArrLinked:

    def test_fires_event(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_arr_linked(6, "RadarrConn")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.ARR_LINKED
        assert evt.new_value == "RadarrConn"


class TestTrackArrUnlinked:

    def test_fires_event(self):
        with patch("services.event_service.event_repo.create") as mock_create:
            event_service.track_arr_unlinked(6, "RadarrConn")
        evt = mock_create.call_args[0][0]
        assert evt.event_type == EventType.ARR_UNLINKED
        assert evt.old_value == "RadarrConn"


class TestTrackDownloadSkipped:

    def test_returns_true_when_created(self):
        with patch("services.event_service.event_repo.create_skip_if_not_exists", return_value=(MagicMock(), True)):
            result = event_service.track_download_skipped(1, "no_trailer")
        assert result is True

    def test_returns_false_when_already_exists(self):
        with patch("services.event_service.event_repo.create_skip_if_not_exists", return_value=(MagicMock(), False)):
            result = event_service.track_download_skipped(1, "no_trailer")
        assert result is False

    def test_returns_false_on_exception(self):
        with patch("services.event_service.event_repo.create_skip_if_not_exists", side_effect=Exception("DB error")):
            result = event_service.track_download_skipped(1, "no_trailer")
        assert result is False
