"""Tests for download/pipeline.py — Plan 1c and 1f coverage."""

import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from db.models.issue import EntityType, IssueType
from db.models.media import MediaRead
from db.models.mediatrailerstatus import TrailerStatusEnum
from db.models.trailerprofile import VideoType
from download.pipeline import _is_valid_media, download_trailer


def _make_media(**kwargs) -> MediaRead:
    defaults = dict(
        id=1,
        connection_id=1,
        arr_id=1,
        is_movie=True,
        title="Test Movie",
        clean_title="test movie",
        year=2024,
        language="en",
        studio="Studio",
        tmdb_id="12345",
        title_slug="test-movie",
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        downloaded_at=None,
        folder_path="/media/test-movie",
    )
    defaults.update(kwargs)
    return MediaRead(**defaults)


class TestDownloadBroadcastReload:
    """1c — successful download must include trailer_statuses in reload key."""

    @pytest.mark.asyncio
    async def test_success_broadcasts_trailer_statuses(self):
        media = _make_media()
        profile = MagicMock()
        profile.customfilter.filter_name = "Test"
        profile.always_search = False
        profile.skip_if_plex_trailer = False
        profile.remove_silence = False
        profile.stop_monitoring = False
        profile.notify_plex = False
        profile.retry_count = 0
        profile.id = 1
        profile.video_type = VideoType.TRAILER

        with (
            patch("download.pipeline._check_plex_trailer", new_callable=AsyncMock, return_value=False),
            patch("download.pipeline.trailer_search.get_video_id", return_value="yt_abc"),
            patch("download.pipeline._update_media_status"),
            patch("download.pipeline._download_and_verify_trailer", return_value=("/tmp/trailer.mkv", MagicMock())),
            patch("download.pipeline.trailer_file.move_trailer_to_folder", return_value="/final/trailer.mkv"),
            patch("download.pipeline.record_new_trailer_download", new_callable=AsyncMock),
            patch("download.pipeline.trailer_status_repo.read", return_value=None),
            patch("download.pipeline.event_service.track_trailer_downloaded"),
            patch("download.pipeline.ws_manager.broadcast", new_callable=AsyncMock) as mock_broadcast,
        ):
            result = await download_trailer(media, profile, retry_count=0)

        assert result is True
        mock_broadcast.assert_called_once()
        call_kwargs = mock_broadcast.call_args
        reload_value = call_kwargs[1].get("reload") or call_kwargs[0][2]
        assert "trailer_statuses" in reload_value
        assert "media" in reload_value


class TestFolderMissingIssue:
    """1f — FOLDER_MISSING issue created/resolved in _is_valid_media."""

    def test_missing_folder_creates_issue(self):
        media = _make_media(folder_path="/nonexistent/path")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=False),
            patch("download.pipeline.event_service.track_download_skipped"),
            patch("download.pipeline.issue_repo.upsert") as mock_upsert,
            patch("download.pipeline.ws_broadcast") as mock_broadcast,
        ):
            result = _is_valid_media(media, check_folder=True, row_id=42)

        assert result is False
        mock_upsert.assert_called_once()
        call_kwargs = mock_upsert.call_args.kwargs
        assert call_kwargs["issue_type"] == IssueType.FOLDER_MISSING
        assert call_kwargs["entity_type"] == EntityType.MEDIA_TRAILER_STATUS
        assert call_kwargs["entity_id"] == 42
        assert "/nonexistent/path" in call_kwargs["description"]
        assert call_kwargs["details"] == "/nonexistent/path"
        mock_broadcast.assert_called_once_with("", reload="issues")

    def test_missing_folder_creates_issue_with_correct_entity_id(self):
        media = _make_media(folder_path="/missing")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=False),
            patch("download.pipeline.event_service.track_download_skipped"),
            patch("download.pipeline.issue_repo.upsert") as mock_upsert,
            patch("download.pipeline.ws_broadcast"),
        ):
            _is_valid_media(media, check_folder=True, row_id=99)

        assert mock_upsert.call_args.kwargs["entity_id"] == 99

    def test_missing_folder_no_row_id_no_issue(self):
        media = _make_media(folder_path="/missing")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=False),
            patch("download.pipeline.event_service.track_download_skipped"),
            patch("download.pipeline.issue_repo.upsert") as mock_upsert,
            patch("download.pipeline.ws_broadcast") as mock_broadcast,
        ):
            result = _is_valid_media(media, check_folder=True, row_id=None)

        assert result is False
        mock_upsert.assert_not_called()
        mock_broadcast.assert_not_called()

    def test_accessible_folder_resolves_issue(self):
        media = _make_media(folder_path="/exists")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=True),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.issue_repo.resolve", return_value=True) as mock_resolve,
            patch("download.pipeline.issue_repo.upsert"),
            patch("download.pipeline.ws_broadcast") as mock_ws,
        ):
            mock_settings.wait_for_media = False
            result = _is_valid_media(media, check_folder=True, row_id=55)

        assert result is True
        mock_resolve.assert_called_once_with(
            IssueType.FOLDER_MISSING,
            EntityType.MEDIA_TRAILER_STATUS,
            55,
        )
        mock_ws.assert_called_once_with("", reload="issues")

    def test_accessible_folder_resolve_returns_false_no_ws(self):
        media = _make_media(folder_path="/exists")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=True),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.issue_repo.resolve", return_value=False),
            patch("download.pipeline.ws_broadcast") as mock_ws,
        ):
            mock_settings.wait_for_media = False
            result = _is_valid_media(media, check_folder=True, row_id=55)

        assert result is True
        mock_ws.assert_not_called()

    def test_accessible_folder_no_row_id_no_resolve(self):
        media = _make_media(folder_path="/exists")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=True),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.issue_repo.resolve") as mock_resolve,
            patch("download.pipeline.ws_broadcast") as mock_ws,
        ):
            mock_settings.wait_for_media = False
            result = _is_valid_media(media, check_folder=True, row_id=None)

        assert result is True
        mock_resolve.assert_not_called()
        mock_ws.assert_not_called()

    def test_no_folder_path_no_issue(self):
        media = _make_media(folder_path=None)

        with (
            patch("download.pipeline.event_service.track_download_skipped"),
            patch("download.pipeline.issue_repo.upsert") as mock_upsert,
            patch("download.pipeline.ws_broadcast") as mock_broadcast,
        ):
            result = _is_valid_media(media, check_folder=True, row_id=10)

        assert result is False
        mock_upsert.assert_not_called()
        mock_broadcast.assert_not_called()

    def test_wait_for_media_resolves_issue_when_media_present(self):
        media = _make_media(folder_path="/exists")

        with (
            patch("download.pipeline.FilesHandler.check_folder_exists", return_value=True),
            patch("download.pipeline.FilesHandler.check_media_exists", return_value=True),
            patch("download.pipeline.app_settings") as mock_settings,
            patch("download.pipeline.issue_repo.resolve", return_value=True) as mock_resolve,
            patch("download.pipeline.ws_broadcast") as mock_ws,
        ):
            mock_settings.wait_for_media = True
            result = _is_valid_media(media, check_folder=True, row_id=77)

        assert result is True
        mock_resolve.assert_called_once_with(
            IssueType.FOLDER_MISSING,
            EntityType.MEDIA_TRAILER_STATUS,
            77,
        )
        mock_ws.assert_called_once_with("", reload="issues")
