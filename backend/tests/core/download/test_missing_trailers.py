"""Tests for the download_missing_trailers function."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.download.trailers.missing import download_missing_trailers
from core.base.database.models.media import MediaRead, MonitorStatus
from core.base.database.models.trailerprofile import TrailerProfileRead


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
        added_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
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
        added_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        downloaded_at="2024-01-01T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_download_missing_trailers_skips_media_with_trailers(
    mock_media_no_trailer, mock_media_with_trailer
):
    """Test that media items with existing trailers are skipped."""
    with patch("core.download.trailers.missing.app_settings") as mock_settings, \
         patch("core.download.trailers.missing.MediaDatabaseManager") as mock_db_manager_class, \
         patch("core.download.trailers.missing.trailerprofile") as mock_trailerprofile, \
         patch("core.download.trailers.missing._process_single_media_item") as mock_process:
        
        # Configure settings
        mock_settings.monitor_enabled = True
        
        # Configure database manager mock
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        
        # First call returns both media items, second call returns empty list
        mock_db_manager.read_all.side_effect = [
            [mock_media_with_trailer, mock_media_no_trailer],  # First iteration
            [mock_media_with_trailer, mock_media_no_trailer],  # Second iteration (after processing first)
        ]
        
        # Configure trailer profiles
        mock_profile = MagicMock()
        mock_profile.enabled = True
        mock_customfilter = MagicMock()
        mock_customfilter.filters = []
        mock_profile.customfilter = mock_customfilter
        mock_trailerprofile.get_trailerprofiles.return_value = [mock_profile]
        
        # Configure process function to return success
        mock_process.return_value = (1, 0)  # 1 download, 0 skips
        
        # Run the function
        await download_missing_trailers()
        
        # Verify that process was called only once (for media without trailer)
        assert mock_process.call_count == 1
        
        # Verify it was called with the correct media (the one without trailer)
        call_args = mock_process.call_args[0]
        assert call_args[0].id == mock_media_no_trailer.id
        assert call_args[0].trailer_exists == False


@pytest.mark.asyncio
async def test_download_missing_trailers_prevents_infinite_loop():
    """Test that the same media item is not processed multiple times in one run."""
    with patch("core.download.trailers.missing.app_settings") as mock_settings, \
         patch("core.download.trailers.missing.MediaDatabaseManager") as mock_db_manager_class, \
         patch("core.download.trailers.missing.trailerprofile") as mock_trailerprofile, \
         patch("core.download.trailers.missing._process_single_media_item") as mock_process:
        
        # Configure settings
        mock_settings.monitor_enabled = True
        
        # Configure database manager mock
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        
        # Create a media item that would normally be reprocessed
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
            added_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            downloaded_at=None,
        )
        
        # Database always returns the same media item
        # This simulates the scenario where download fails and media remains monitored
        mock_db_manager.read_all.return_value = [media]
        
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
        assert mock_db_manager.read_all.call_count >= 2


@pytest.mark.asyncio
async def test_download_missing_trailers_monitoring_disabled():
    """Test that function exits early when monitoring is disabled."""
    with patch("core.download.trailers.missing.app_settings") as mock_settings, \
         patch("core.download.trailers.missing.MediaDatabaseManager") as mock_db_manager_class:
        
        # Configure settings - monitoring disabled
        mock_settings.monitor_enabled = False
        
        # Run the function
        await download_missing_trailers()
        
        # Verify database was never queried since monitoring is disabled
        mock_db_manager_class.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_no_profiles():
    """Test that function exits when no trailer profiles exist."""
    with patch("core.download.trailers.missing.app_settings") as mock_settings, \
         patch("core.download.trailers.missing.MediaDatabaseManager") as mock_db_manager_class, \
         patch("core.download.trailers.missing.trailerprofile") as mock_trailerprofile:
        
        # Configure settings
        mock_settings.monitor_enabled = True
        
        # Configure database manager mock
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        mock_db_manager.read_all.return_value = []
        
        # No profiles
        mock_trailerprofile.get_trailerprofiles.return_value = []
        
        # Run the function
        await download_missing_trailers()
        
        # Function should exit early, so read_all should be called only once
        assert mock_db_manager.read_all.call_count == 1
