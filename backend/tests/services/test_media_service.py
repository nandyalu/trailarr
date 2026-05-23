"""Comprehensive tests for services/media_service.py."""

from unittest.mock import MagicMock, call, patch

import pytest

from db.models.event import EventSource
from services import media_service


class TestToggleMonitor:

    def test_returns_unchanged_tuple_when_nothing_changed(self):
        with (
            patch("services.media_service.media_repo.update_monitoring", return_value=("Already set", False)),
            patch("services.media_service.event_service.track_monitor_changed") as mock_event,
        ):
            msg, changed, updated = media_service.toggle_monitor(1, True)

        assert msg == "Already set"
        assert changed is False
        assert updated is None
        mock_event.assert_not_called()

    def test_fires_event_and_returns_updated_when_changed(self):
        mock_media = MagicMock()
        with (
            patch("services.media_service.media_repo.update_monitoring", return_value=("Updated", True)),
            patch("services.media_service.media_repo.read", return_value=mock_media),
            patch("services.media_service.event_service.track_monitor_changed") as mock_event,
        ):
            msg, changed, updated = media_service.toggle_monitor(7, False)

        assert msg == "Updated"
        assert changed is True
        assert updated is mock_media
        mock_event.assert_called_once_with(
            media_id=7,
            old_monitor=True,  # opposite of new_monitor=False
            new_monitor=False,
            source=EventSource.USER,
            source_detail="API",
        )

    def test_reads_updated_media_after_change(self):
        mock_media = MagicMock()
        with (
            patch("services.media_service.media_repo.update_monitoring", return_value=("OK", True)),
            patch("services.media_service.media_repo.read", return_value=mock_media) as mock_read,
            patch("services.media_service.event_service.track_monitor_changed"),
        ):
            _, _, updated = media_service.toggle_monitor(99, True)

        mock_read.assert_called_once_with(99)
        assert updated is mock_media


class TestBatchToggleMonitor:

    def test_fires_event_for_each_changed_item(self):
        results = {10: ("OK", True), 20: ("OK", True), 30: ("Already", False)}

        def fake_update(media_id, monitor):
            return results[media_id]

        with (
            patch("services.media_service.media_repo.update_monitoring", side_effect=fake_update),
            patch("services.media_service.event_service.track_monitor_changed") as mock_event,
        ):
            media_service.batch_toggle_monitor([10, 20, 30], True)

        assert mock_event.call_count == 2
        called_ids = {c.kwargs["media_id"] for c in mock_event.call_args_list}
        assert called_ids == {10, 20}

    def test_no_events_when_nothing_changed(self):
        with (
            patch("services.media_service.media_repo.update_monitoring", return_value=("No change", False)),
            patch("services.media_service.event_service.track_monitor_changed") as mock_event,
        ):
            media_service.batch_toggle_monitor([1, 2, 3], False)

        mock_event.assert_not_called()

    def test_empty_list_is_no_op(self):
        with (
            patch("services.media_service.media_repo.update_monitoring") as mock_update,
            patch("services.media_service.event_service.track_monitor_changed") as mock_event,
        ):
            media_service.batch_toggle_monitor([], True)

        mock_update.assert_not_called()
        mock_event.assert_not_called()

    def test_source_is_batchapi(self):
        with (
            patch("services.media_service.media_repo.update_monitoring", return_value=("OK", True)),
            patch("services.media_service.event_service.track_monitor_changed") as mock_event,
        ):
            media_service.batch_toggle_monitor([5], True)

        call_kwargs = mock_event.call_args.kwargs
        assert call_kwargs["source_detail"] == "BatchAPI"


class TestUpdateYtId:

    def test_reads_old_id_fires_event_returns_updated(self):
        old_media = MagicMock()
        old_media.youtube_trailer_id = "old_id"
        old_media.title = "Test Movie"
        new_media = MagicMock()

        with (
            patch("services.media_service.media_repo.read", side_effect=[old_media, new_media]),
            patch("services.media_service.media_repo.update_ytid") as mock_update,
            patch("services.media_service.event_service.track_youtube_id_changed") as mock_event,
        ):
            msg, updated = media_service.update_yt_id(5, "new_id")

        mock_update.assert_called_once_with(5, "new_id")
        mock_event.assert_called_once_with(
            media_id=5,
            old_yt_id="old_id",
            new_yt_id="new_id",
            source=EventSource.USER,
            source_detail="API",
        )
        assert updated is new_media
        assert "Test Movie" in msg

    def test_event_fires_even_when_yt_id_is_same(self):
        old_media = MagicMock()
        old_media.youtube_trailer_id = "same_id"
        old_media.title = "Foo"

        with (
            patch("services.media_service.media_repo.read", return_value=old_media),
            patch("services.media_service.media_repo.update_ytid"),
            patch("services.media_service.event_service.track_youtube_id_changed") as mock_event,
        ):
            media_service.update_yt_id(1, "same_id")

        # event_service.track_youtube_id_changed internally skips if old==new,
        # but the service still calls it — event_service is responsible for the guard
        mock_event.assert_called_once()

    def test_reads_media_twice_to_get_fresh_state(self):
        media1 = MagicMock(youtube_trailer_id=None, title="M")
        media2 = MagicMock()

        with (
            patch("services.media_service.media_repo.read", side_effect=[media1, media2]) as mock_read,
            patch("services.media_service.media_repo.update_ytid"),
            patch("services.media_service.event_service.track_youtube_id_changed"),
        ):
            _, updated = media_service.update_yt_id(3, "xyz")

        assert mock_read.call_count == 2
        assert updated is media2
