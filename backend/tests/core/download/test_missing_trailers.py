"""Tests for the download_missing_trailers function."""

import datetime
import pytest
from unittest.mock import MagicMock, patch
from core.download.trailers.missing import download_missing_trailers
from core.base.database.models.media import MediaRead, MonitorStatus


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
        trailer_exists=False,
        monitor=True,
        arr_monitored=True,
        status=MonitorStatus.MONITORED,
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
        trailer_exists=True,  # Has trailer
        monitor=True,
        arr_monitored=True,
        status=MonitorStatus.DOWNLOADED,
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
    with patch(
        "core.download.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "core.download.trailers.missing.media_manager.read_all_generator"
    ) as mock_db_manager_read_all, patch(
        "core.download.trailers.missing.trailerprofile"
    ) as mock_trailerprofile, patch(
        "core.download.trailers.missing._process_single_media_item"
    ) as mock_process:

        # Configure settings
        mock_settings.monitor_enabled = True

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
            trailer_exists=False,  # No trailer
            monitor=True,  # Still monitored
            arr_monitored=True,
            status=MonitorStatus.MONITORED,  # Still MONITORED status
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

        # Database should always yield the same media item
        # This simulates the scenario where download fails and media remains monitored
        def fake_media_generator(monitored_only=False):
            yield media

        mock_db_manager_read_all.side_effect = fake_media_generator

        # Configure trailer profiles
        mock_profile = MagicMock()
        mock_profile.enabled = True
        mock_customfilter = MagicMock()
        mock_customfilter.filters = []
        mock_profile.customfilter = mock_customfilter
        mock_trailerprofile.get_trailerprofiles.return_value = [mock_profile]

        # Configure process function to return a failure (0 downloads, 1 skip)
        mock_process.return_value = (0, 1)

        # Run the function
        await download_missing_trailers()

        # Verify that process was called exactly once despite media remaining monitored
        assert mock_process.call_count == 1

        # Verify read_all was called at least twice (to confirm loop ran multiple times)
        assert mock_db_manager_read_all.call_count >= 2


@pytest.mark.asyncio
async def test_download_missing_trailers_monitoring_disabled():
    """Test that function exits early when monitoring is disabled."""
    with patch(
        "core.download.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "core.download.trailers.missing.media_manager.read_all"
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
        "core.download.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "core.download.trailers.missing.media_manager.read_all_generator"
    ) as mock_db_manager_read_all, patch(
        "core.download.trailers.missing.trailerprofile"
    ) as mock_trailerprofile:

        # Configure settings
        mock_settings.monitor_enabled = True

        # Configure database manager mock
        def fake_media_generator(monitored_only=False):
            yield from []

        mock_db_manager_read_all.side_effect = fake_media_generator

        # No profiles
        mock_trailerprofile.get_trailerprofiles.return_value = []

        # Run the function
        await download_missing_trailers()

        # Function should exit early, so read_all should be called only once
        assert mock_db_manager_read_all.call_count == 1
