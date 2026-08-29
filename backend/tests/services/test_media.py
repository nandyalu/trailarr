"""Tests for services/media.py.

This logic sat inside the api/v1/media.py handlers, mixed with websocket
broadcasts, so it had no tests. Phase 7 Stage B moved it into a service that
reports what happened and leaves the broadcasting to the handler.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import media as media_service

PKG = "services.media"


def _media(media_id=42, title="Film", folder_path="/media/Film", monitor=False, yt_id=""):
    return SimpleNamespace(
        id=media_id,
        title=title,
        folder_path=folder_path,
        monitor=monitor,
        youtube_trailer_id=yt_id,
    )


def _download(download_id, path, file_exists=True):
    return SimpleNamespace(id=download_id, path=path, file_exists=file_exists)


class TestDeleteTrailers:

    @pytest.mark.asyncio
    async def test_media_without_a_folder_is_refused(self):
        with patch(f"{PKG}.media_manager.read", return_value=_media(folder_path="")):
            result = await media_service.delete_trailers(42)

        assert result.ok is False
        assert "has no folder path" in result.message
        assert result.reload is None

    @pytest.mark.asyncio
    async def test_no_live_files_is_refused(self):
        """Rows marked deleted are not files on disk any more."""
        with (
            patch(f"{PKG}.media_manager.read", return_value=_media()),
            patch(
                f"{PKG}.download_manager.read_by_media_id",
                return_value=[_download(1, "/gone.mkv", file_exists=False)],
            ),
            patch(f"{PKG}.FilesHandler.delete_file", AsyncMock()) as mock_delete,
        ):
            result = await media_service.delete_trailers(42)

        assert result.ok is False
        assert "No trailer files found" in result.message
        mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_every_live_file_is_deleted_and_marked(self):
        downloads = [
            _download(1, "/a.mkv"),
            _download(2, "/b.mkv"),
            _download(3, "/gone.mkv", file_exists=False),
        ]
        with (
            patch(f"{PKG}.media_manager.read", return_value=_media()),
            patch(
                f"{PKG}.download_manager.read_by_media_id", return_value=downloads
            ),
            patch(f"{PKG}.FilesHandler.delete_file", AsyncMock()) as mock_delete,
            patch(f"{PKG}.download_manager.mark_as_deleted") as mock_mark,
            patch(f"{PKG}.event_manager.track_trailer_deleted") as mock_event,
        ):
            result = await media_service.delete_trailers(42)

        assert result.ok is True
        assert result.reload == "media"
        # Only the live ones
        assert [c.args[0] for c in mock_delete.await_args_list] == [
            "/a.mkv",
            "/b.mkv",
        ]
        assert [c.args[0] for c in mock_mark.call_args_list] == [1, 2]
        # One event for the media item, not one per file
        assert mock_event.call_count == 1


class TestSetYoutubeId:

    def test_a_changed_id_is_stored_and_tracked(self):
        with (
            patch(f"{PKG}.media_manager.read", return_value=_media(yt_id="old")),
            patch(f"{PKG}.media_manager.update_ytid") as mock_update,
            patch(f"{PKG}.event_manager.track_youtube_id_changed") as mock_event,
        ):
            msg = media_service.set_youtube_id(42, "newvalue123")

        mock_update.assert_called_once_with(42, "newvalue123")
        assert mock_event.call_count == 1
        assert "has been updated" in msg

    def test_the_same_id_is_stored_but_not_tracked(self):
        """Re-saving the same id is not a change worth an event."""
        with (
            patch(f"{PKG}.media_manager.read", return_value=_media(yt_id="same")),
            patch(f"{PKG}.media_manager.update_ytid") as mock_update,
            patch(f"{PKG}.event_manager.track_youtube_id_changed") as mock_event,
        ):
            media_service.set_youtube_id(42, "same")

        mock_update.assert_called_once_with(42, "same")
        mock_event.assert_not_called()


class TestSetMonitoring:

    def test_a_successful_change_is_tracked(self):
        with (
            patch(f"{PKG}.media_manager.read", return_value=_media(monitor=False)),
            patch(
                f"{PKG}.media_manager.update_monitoring",
                return_value=("Now monitored", True),
            ),
            patch(f"{PKG}.event_manager.track_monitor_changed") as mock_event,
        ):
            result = media_service.set_monitoring(42, True)

        assert result.ok is True
        assert result.message == "Now monitored"
        assert result.reload == "media"
        assert mock_event.call_count == 1

    def test_a_failed_change_is_not_tracked(self):
        with (
            patch(f"{PKG}.media_manager.read", return_value=_media(monitor=False)),
            patch(
                f"{PKG}.media_manager.update_monitoring",
                return_value=("Could not monitor", False),
            ),
            patch(f"{PKG}.event_manager.track_monitor_changed") as mock_event,
        ):
            result = media_service.set_monitoring(42, True)

        assert result.ok is False
        mock_event.assert_not_called()
