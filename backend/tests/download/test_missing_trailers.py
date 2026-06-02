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
        tmdb_id="12345",
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


def _make_profile(profile_id=1, enabled=True, for_movies=True, priority=0):
    p = MagicMock()
    p.id = profile_id
    p.enabled = enabled
    p.for_movies = for_movies
    p.priority = priority
    p.custom_folder = "{media_folder}"
    p.max_count = 1
    p.download_season_videos = False
    p.retry_count = 2
    p.stop_monitoring = False
    cf = MagicMock()
    cf.filter_name = "Default"
    cf.filters = []
    p.customfilter = cf
    return p


@pytest.mark.asyncio
async def test_download_missing_trailers_monitoring_disabled():
    """Function exits early when monitoring is disabled."""
    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.media_repo.read_all_generator") as mock_gen,
    ):
        mock_settings.monitor_enabled = False
        await download_missing_trailers()
    mock_gen.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_no_profiles():
    """Function exits early when no enabled profiles exist."""
    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.trailer_profile_repo.read_all", return_value=[]),
        patch("download.pipeline.media_repo.read_all_generator") as mock_gen,
    ):
        mock_settings.monitor_enabled = True
        await download_missing_trailers()
    mock_gen.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_skips_non_matching_media():
    """Media that matches no profile is skipped without attempting a download."""
    media = _make_media(id=1, is_movie=True)
    profile = _make_profile(for_movies=False)  # series profile — won't match a movie

    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.trailer_profile_repo.read_all", return_value=[profile]),
        patch("download.pipeline.media_repo.read_all_generator", return_value=iter([media])),
        patch("download.pipeline.matches_filters", return_value=True),
        patch("download.pipeline.download_trailer") as mock_dl,
    ):
        mock_settings.monitor_enabled = True
        await download_missing_trailers()

    mock_dl.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_skips_invalid_folder():
    """Media whose folder is inaccessible is added to skipped set and not downloaded."""
    media = _make_media(id=1)
    profile = _make_profile()

    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.trailer_profile_repo.read_all", return_value=[profile]),
        patch("download.pipeline.media_repo.read_all_generator", return_value=iter([media])),
        patch("download.pipeline.matches_filters", return_value=True),
        patch("download.pipeline._is_valid_media", return_value=False),
        patch("download.pipeline.trailer_status_repo.get_rows_for_media_and_profiles", return_value={}),
        patch("download.pipeline.download_trailer") as mock_dl,
    ):
        mock_settings.monitor_enabled = True
        await download_missing_trailers()

    mock_dl.assert_not_called()


@pytest.mark.asyncio
async def test_download_missing_trailers_deduplicates_media():
    """The same media ID yielded twice is only processed once."""
    media = _make_media(id=1)
    profile = _make_profile()

    call_count = [0]

    async def fake_download(*args, **kwargs):
        call_count[0] += 1
        return True

    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.trailer_profile_repo.read_all", return_value=[profile]),
        patch("download.pipeline.media_repo.read_all_generator", return_value=iter([media, media])),
        patch("download.pipeline.matches_filters", return_value=True),
        patch("download.pipeline._is_valid_media", return_value=True),
        patch("download.pipeline.trailer_status_repo.get_rows_for_media_and_profiles", return_value={}),
        patch("download.pipeline._should_skip_slot", return_value=False),
        patch("download.pipeline.download_trailer", new_callable=AsyncMock, side_effect=fake_download),
        patch("download.pipeline.utils.sleep_between_downloads", new_callable=AsyncMock),
    ):
        mock_settings.monitor_enabled = True
        await download_missing_trailers()

    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_download_missing_trailers_stop_monitoring_skips_other_profiles():
    """After stop_monitoring fires on one profile, other profiles for that media are skipped."""
    media = _make_media(id=1)
    profile1 = _make_profile(profile_id=1, priority=10)
    profile1.stop_monitoring = True
    profile2 = _make_profile(profile_id=2, priority=5)

    download_calls = []

    async def fake_download(m, p, *args, **kwargs):
        download_calls.append(p.id)
        return True

    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.trailer_profile_repo.read_all", return_value=[profile1, profile2]),
        patch("download.pipeline.media_repo.read_all_generator", return_value=iter([media])),
        patch("download.pipeline.matches_filters", return_value=True),
        patch("download.pipeline._is_valid_media", return_value=True),
        patch("download.pipeline.trailer_status_repo.get_rows_for_media_and_profiles", return_value={}),
        patch("download.pipeline._should_skip_slot", return_value=False),
        patch("download.pipeline.download_trailer", new_callable=AsyncMock, side_effect=fake_download),
        patch("download.pipeline.utils.sleep_between_downloads", new_callable=AsyncMock),
    ):
        mock_settings.monitor_enabled = True
        await download_missing_trailers()

    # Only profile1 (higher priority, stop_monitoring=True) should have been attempted
    assert download_calls == [1]


@pytest.mark.asyncio
async def test_download_missing_trailers_writes_failed_row_on_failure():
    """A DownloadFailedError causes a FAILED status row to be upserted."""
    from exceptions import DownloadFailedError

    media = _make_media(id=1)
    profile = _make_profile()

    with (
        patch("download.pipeline.app_settings") as mock_settings,
        patch("download.pipeline.trailer_profile_repo.read_all", return_value=[profile]),
        patch("download.pipeline.media_repo.read_all_generator", return_value=iter([media])),
        patch("download.pipeline.matches_filters", return_value=True),
        patch("download.pipeline._is_valid_media", return_value=True),
        patch("download.pipeline.trailer_status_repo.get_rows_for_media_and_profiles", return_value={}),
        patch("download.pipeline._should_skip_slot", return_value=False),
        patch("download.pipeline.download_trailer", new_callable=AsyncMock,
              side_effect=DownloadFailedError("fail")),
        patch("download.pipeline.trailer_status_repo.upsert_slot_status") as mock_upsert,
        patch("download.pipeline.utils.sleep_between_downloads", new_callable=AsyncMock),
    ):
        mock_settings.monitor_enabled = True
        await download_missing_trailers()

    mock_upsert.assert_called_once()
    _, _, _, _, status = mock_upsert.call_args[0]
    assert status == TrailerStatusEnum.FAILED
    assert mock_upsert.call_args[1].get("increment_attempt") is True
