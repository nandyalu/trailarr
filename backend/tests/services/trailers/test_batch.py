"""Tests for the batch download loop."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from quiv import JobCancelledError

from services.trailers.trailers.batch import batch_download_task


def _media(media_id: int) -> MagicMock:
    media = MagicMock()
    media.id = media_id
    media.title = f"Movie {media_id}"
    return media


@pytest.mark.asyncio
async def test_a_job_cancel_stops_the_batch_and_propagates():
    """The broad `except Exception` in the loop must not eat a cancel, and
    the loop must not move on to the next item."""
    profile = MagicMock()
    profile.retry_count = 0
    media_list = [_media(1), _media(2)]

    with (
        patch(
            "services.trailers.trailers.batch.download_trailer",
            new_callable=AsyncMock,
            side_effect=JobCancelledError("yt-dlp was stopped"),
        ) as download_trailer,
        patch(
            "services.trailers.trailers.batch.utils.sleep_between_downloads",
            new_callable=AsyncMock,
        ) as sleep,
    ):
        with pytest.raises(JobCancelledError):
            await batch_download_task(media_list, profile)

    assert download_trailer.await_count == 1
    sleep.assert_not_awaited()

