"""Tests for the download_missing_trailers function."""

import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from config.settings import app_settings
from services.trailers.trailers.missing import download_missing_trailers
from database.models.media import MediaRead


@pytest.fixture
def mock_media_no_trailer():
    """Create a mock media object without a trailer."""
    return MediaRead(
        id=1,
        connection_id=1,
        arr_id=1,
        is_movie=True,
        title="Test Movie",
        clean_title="test movie",
        year=2024,
        language="en",
        studio="Test Studio",
        txdb_id="12345",
        title_slug="test-movie",
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        updated_at=datetime.datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        downloaded_at=None,
    )


@pytest.fixture
def mock_media_with_trailer():
    """Create a mock media object with a trailer."""
    return MediaRead(
        id=2,
        connection_id=1,
        arr_id=2,
        is_movie=True,
        title="Test Movie 2",
        clean_title="test movie 2",
        year=2024,
        language="en",
        studio="Test Studio",
        txdb_id="12346",
        title_slug="test-movie-2",
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        updated_at=datetime.datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        downloaded_at=datetime.datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
    )


@pytest.mark.asyncio
async def test_download_missing_trailers_prevents_infinite_loop():
    """Test that the same media item is not processed multiple times in one run."""
    with (
        patch("services.trailers.trailers.missing.app_settings") as mock_settings,
        patch(
            "services.trailers.trailers.missing.downloads_ready",
            return_value=True,
        ),
        patch(
            "services.trailers.trailers.missing.attempt_manager"
        ) as mock_attempts,
        patch(
            "services.trailers.trailers.missing.media_manager.read_all_generator"
        ) as mock_media_generator,
        patch(
            "services.trailers.trailers.missing.media_manager.read"
        ) as mock_media_read,
        patch(
            "services.trailers.trailers.missing.trailerprofile"
        ) as mock_trailerprofile,
        patch(
            "services.trailers.trailers.missing._process_single_media_item",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        mock_settings.monitor_enabled = True
        mock_settings.downloads_enabled = True
        mock_attempts.prune_for_missing_profiles.return_value = 0
        mock_attempts.read_all.return_value = []
        mock_attempts.read_for_media.return_value = []
        media = MediaRead(
            id=1,
            connection_id=1,
            arr_id=1,
            is_movie=True,
            title="Test Movie",
            clean_title="test movie",
            year=2024,
            language="en",
            studio="Test Studio",
            txdb_id="12345",
            title_slug="test-movie",
            monitor=True,  # Still monitored
            arr_monitored=True,
            media_exists=False,
            media_filename="",
            season_count=0,
            runtime=120,
            added_at=datetime.datetime(
                2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
            updated_at=datetime.datetime(
                2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
            downloaded_at=None,
        )

        def fake_media_generator(monitored_only=False):
            yield media

        mock_media_generator.side_effect = fake_media_generator
        mock_media_read.return_value = media
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.priority = 100
        mock_profile.enabled = True
        mock_customfilter = MagicMock()
        mock_customfilter.filters = []
        mock_profile.customfilter = mock_customfilter
        mock_trailerprofile.get_trailerprofiles.return_value = [mock_profile]
        mock_process.return_value = (0, 1)

        await download_missing_trailers()

        assert mock_process.await_count == 1
        assert mock_media_generator.call_count == 2


@pytest.mark.asyncio
async def test_download_missing_trailers_monitoring_disabled():
    """Test that function exits early when monitoring is disabled."""
    with patch(
        "services.trailers.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "services.trailers.trailers.missing.media_manager.read_all"
    ) as mock_db_manager_read_all:

        # Configure settings - monitoring disabled
        mock_settings.monitor_enabled = False

        # Run the function
        await download_missing_trailers()

        # Verify database was never queried since monitoring is disabled
        mock_db_manager_read_all.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_no_profiles():
    """Test that function exits when no trailer profiles exist."""
    with patch(
        "services.trailers.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "services.trailers.trailers.missing.downloads_ready", return_value=True
    ), patch(
        "services.trailers.trailers.missing.attempt_manager"
    ) as mock_attempts, patch(
        "services.trailers.trailers.missing.media_manager.read_all_generator"
    ) as mock_db_manager_read_all, patch(
        "services.trailers.trailers.missing.trailerprofile"
    ) as mock_trailerprofile:

        # Configure settings
        mock_settings.monitor_enabled = True
        mock_attempts.prune_for_missing_profiles.return_value = 0

        # Configure database manager mock
        def fake_media_generator(monitored_only=False):
            yield from []

        mock_db_manager_read_all.side_effect = fake_media_generator

        # No profiles
        mock_trailerprofile.get_trailerprofiles.return_value = []

        # Run the function
        await download_missing_trailers()

        mock_db_manager_read_all.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_preview_mode():
    """Phase 3: downloads_enabled=False runs the preview pass and downloads
    nothing — the media generator is never even opened."""
    from unittest.mock import AsyncMock

    with patch(
        "services.trailers.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "services.trailers.trailers.missing.downloads_ready", return_value=True
    ), patch(
        "services.trailers.trailers.missing._run_preview_pass",
        new_callable=AsyncMock,
    ) as mock_preview, patch(
        "services.trailers.trailers.missing.media_manager.read_all_generator"
    ) as mock_read_all:
        mock_settings.monitor_enabled = True
        mock_settings.downloads_enabled = False

        await download_missing_trailers()

        mock_preview.assert_awaited_once()
        mock_read_all.assert_not_called()


@pytest.mark.asyncio
async def test_preview_pass_publishes_would_download_list():
    """The preview pass logs/broadcasts the pending summary and never
    touches the downloader."""
    from unittest.mock import AsyncMock
    from services.trailers.trailers.missing import _run_preview_pass
    from services.trailers.trailers.pending import (
        PendingSummary,
        PendingSummaryItem,
    )

    summary = PendingSummary(
        total_media=1,
        pending_pairs=1,
        backoff_pairs=0,
        items=[
            PendingSummaryItem(
                media_id=2,
                title="Preview Movie",
                is_movie=True,
                profile_id=1,
                profile_name="Movie Trailers",
                reason="pending",
                next_eligible_at=None,
            )
        ],
        limit=1000,
        offset=0,
    )
    with patch(
        "services.trailers.trailers.pending.compute_library_pending",
        return_value=summary,
    ) as mock_compute, patch(
        "api.v1.websockets.ws_manager.broadcast", new_callable=AsyncMock
    ) as mock_broadcast:
        await _run_preview_pass()

        mock_compute.assert_called_once()
        assert mock_broadcast.await_count == 1
        message = mock_broadcast.await_args[0][0]
        assert "Preview mode" in message
        assert "1 trailer(s)" in message


class TestIsValidMediaStorageGuard:
    """Storage-reachability guard: unreachable storage must be a SKIP
    (never a failed download attempt), distinct from a genuinely missing
    folder."""

    def _media(self, mock_media_no_trailer):
        mock_media_no_trailer.folder_path = "/mnt/media/Test Movie"
        return mock_media_no_trailer

    def test_folder_missing_storage_down_skips_as_unreachable(
        self, mock_media_no_trailer
    ):
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.is_disk_available",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            assert _is_valid_media(media) is False
            skip_reason = mock_events.track_download_skipped.call_args.kwargs[
                "skip_reason"
            ]
            assert skip_reason == "Storage unreachable"

    def test_folder_missing_storage_up_skips_as_missing_folder(
        self, mock_media_no_trailer
    ):
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.is_disk_available",
            return_value=True,
        ), patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            assert _is_valid_media(media) is False
            skip_reason = mock_events.track_download_skipped.call_args.kwargs[
                "skip_reason"
            ]
            assert skip_reason == "Folder does not exist"

    def test_missing_folder_is_created_when_setting_is_on(
        self, mock_media_no_trailer
    ):
        """Discussion #641: with 'Create Missing Folders' on, a genuinely
        missing folder is created instead of skipping the download."""
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.is_disk_available",
            return_value=True,
        ), patch(
            "services.trailers.trailers.missing.FilesHandler.create_folder",
            return_value=True,
        ) as mock_create, patch(
            "services.trailers.trailers.missing.os.listdir", return_value=[]
        ), patch.object(
            type(app_settings), "create_missing_folders", True
        ), patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            assert _is_valid_media(media) is True
            mock_create.assert_called_once_with("/mnt/media/Test Movie")
            mock_events.track_download_skipped.assert_not_called()

    def test_unreachable_storage_never_creates_a_folder(
        self, mock_media_no_trailer
    ):
        """The setting must not defeat the dead-mount guard: writing into
        a disconnected share would hide the real media."""
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.is_disk_available",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.FilesHandler.create_folder"
        ) as mock_create, patch.object(
            type(app_settings), "create_missing_folders", True
        ), patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            assert _is_valid_media(media) is False
            mock_create.assert_not_called()
            assert (
                mock_events.track_download_skipped.call_args.kwargs[
                    "skip_reason"
                ]
                == "Storage unreachable"
            )

    def test_failed_creation_skips_with_its_own_reason(
        self, mock_media_no_trailer
    ):
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=False,
        ), patch(
            "services.trailers.trailers.missing.is_disk_available",
            return_value=True,
        ), patch(
            "services.trailers.trailers.missing.FilesHandler.create_folder",
            return_value=False,
        ), patch.object(
            type(app_settings), "create_missing_folders", True
        ), patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            assert _is_valid_media(media) is False
            assert (
                mock_events.track_download_skipped.call_args.kwargs[
                    "skip_reason"
                ]
                == "Could not create folder"
            )

    def test_folder_exists_but_unreadable_skips_as_unreachable(
        self, mock_media_no_trailer
    ):
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=True,
        ), patch(
            "services.trailers.trailers.missing.os.listdir",
            side_effect=OSError(112, "Host is down"),
        ), patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            assert _is_valid_media(media) is False
            skip_reason = mock_events.track_download_skipped.call_args.kwargs[
                "skip_reason"
            ]
            assert skip_reason == "Storage unreachable"

    def test_folder_exists_and_readable_passes(self, mock_media_no_trailer):
        from services.trailers.trailers.missing import _is_valid_media

        media = self._media(mock_media_no_trailer)
        with patch(
            "services.trailers.trailers.missing.FilesHandler.check_folder_exists",
            return_value=True,
        ), patch(
            "services.trailers.trailers.missing.os.listdir",
            return_value=[],
        ), patch(
            "services.trailers.trailers.missing.app_settings"
        ) as mock_settings, patch(
            "services.trailers.trailers.missing.event_manager"
        ) as mock_events:
            mock_settings.wait_for_media = False
            assert _is_valid_media(media) is True
            mock_events.track_download_skipped.assert_not_called()
