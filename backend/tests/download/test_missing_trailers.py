"""Tests for the download_missing_trailers function."""

import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from download.pipeline import download_missing_trailers
from db.models.media import MediaRead
from db.models.mediatrailerstatus import TrailerStatusEnum


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
    return _make_media(id=1, monitor=True, downloaded_at=None)


@pytest.fixture
def mock_media_with_trailer():
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

    batch_calls = [0]

    def fake_get_pending_rows(limit=50):
        batch_calls[0] += 1
        if batch_calls[0] == 1:
            return [status_row]
        return []

    with patch(
        "download.pipeline.app_settings"
    ) as mock_settings, patch(
        "download.pipeline.trailer_status_repo.get_pending_rows",
        side_effect=fake_get_pending_rows,
    ), patch(
        "download.pipeline.media_repo.read",
        return_value=media,
    ), patch(
        "download.pipeline.trailer_profile_repo.read",
        return_value=mock_profile,
    ), patch(
        "download.pipeline._is_valid_media",
        return_value=False,
    ), patch(
        "download.pipeline.download_trailer",
    ) as mock_download:
        mock_settings.monitor_enabled = True

        await download_missing_trailers()

        mock_download.assert_not_called()
        assert batch_calls[0] >= 2


@pytest.mark.asyncio
async def test_download_missing_trailers_monitoring_disabled():
    """Test that function exits early when monitoring is disabled."""
    with patch(
        "download.pipeline.app_settings"
    ) as mock_settings, patch(
        "download.pipeline.trailer_status_repo.get_pending_rows",
    ) as mock_get_pending:
        mock_settings.monitor_enabled = False

        await download_missing_trailers()

        mock_get_pending.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_no_profiles():
    """Test that the loop exits immediately when no PENDING rows exist."""
    with patch(
        "download.pipeline.app_settings"
    ) as mock_settings, patch(
        "download.pipeline.trailer_status_repo.get_pending_rows",
        return_value=[],
    ) as mock_get_pending:
        mock_settings.monitor_enabled = True

        await download_missing_trailers()

        assert mock_get_pending.call_count == 1
