"""Tests for the download_missing_trailers function."""

import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.download.trailers.missing import download_missing_trailers
from core.base.database.models.media import MediaRead
from core.base.database.models.mediatrailerstatus import TrailerStatusEnum


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
        studio="Test Studio",
        txdb_id="12345",
        title_slug="test-movie",
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
        downloaded_at=None,
    )
    defaults.update(kwargs)
    return MediaRead(**defaults)


def _make_status_row(id=1, media_id=1, profile_id=1, sequence=1):
    row = MagicMock()
    row.id = id
    row.media_id = media_id
    row.profile_id = profile_id
    row.sequence = sequence
    row.status = TrailerStatusEnum.PENDING
    return row


@pytest.fixture
def mock_media_no_trailer():
    """Create a mock media object without a trailer."""
    return _make_media(id=1, monitor=True, downloaded_at=None)


@pytest.fixture
def mock_media_with_trailer():
    """Create a mock media object with a trailer."""
    return _make_media(
        id=2,
        title="Test Movie 2",
        clean_title="test movie 2",
        txdb_id="12346",
        title_slug="test-movie-2",
        monitor=True,
        downloaded_at=datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    )


@pytest.mark.asyncio
async def test_download_missing_trailers_prevents_infinite_loop():
    """Test that inaccessible media is skipped for the remainder of a run."""
    status_row = _make_status_row(id=1, media_id=1, profile_id=1)
    media = _make_media(id=1, monitor=True, downloaded_at=None)

    mock_profile = MagicMock()
    mock_profile.enabled = True
    mock_profile.custom_folder = "{media_folder}"
    mock_customfilter = MagicMock()
    mock_customfilter.filter_name = "Default"
    mock_profile.customfilter = mock_customfilter

    # First batch returns a row; second batch (after skipping) returns nothing
    batch_calls = [0]

    def fake_get_pending_rows(limit=50):
        batch_calls[0] += 1
        if batch_calls[0] == 1:
            return [status_row]
        return []

    with patch(
        "core.download.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "core.download.trailers.missing.trailer_status_manager.get_pending_rows",
        side_effect=fake_get_pending_rows,
    ), patch(
        "core.download.trailers.missing.media_manager.read",
        return_value=media,
    ), patch(
        "core.download.trailers.missing.trailerprofile_manager.get_trailerprofile",
        return_value=mock_profile,
    ), patch(
        "core.download.trailers.missing._is_valid_media",
        return_value=False,
    ), patch(
        "core.download.trailers.missing.trailer_downloader.download_trailer",
    ) as mock_download:
        mock_settings.monitor_enabled = True

        await download_missing_trailers()

        # download_trailer should never be called since media was inaccessible
        mock_download.assert_not_called()
        # get_pending_rows should be called at least twice (first with row, then empty)
        assert batch_calls[0] >= 2


@pytest.mark.asyncio
async def test_download_missing_trailers_monitoring_disabled():
    """Test that function exits early when monitoring is disabled."""
    with patch(
        "core.download.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "core.download.trailers.missing.trailer_status_manager.get_pending_rows",
    ) as mock_get_pending:
        mock_settings.monitor_enabled = False

        await download_missing_trailers()

        mock_get_pending.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_no_profiles():
    """Test that the loop exits immediately when no PENDING rows exist."""
    with patch(
        "core.download.trailers.missing.app_settings"
    ) as mock_settings, patch(
        "core.download.trailers.missing.trailer_status_manager.get_pending_rows",
        return_value=[],
    ) as mock_get_pending:
        mock_settings.monitor_enabled = True

        await download_missing_trailers()

        # Should exit after the first empty batch
        assert mock_get_pending.call_count == 1
