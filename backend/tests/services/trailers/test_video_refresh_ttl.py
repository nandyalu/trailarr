"""When the download task asks TMDB — plans/phase-08-tmdb.md decision 3.

A curated list changes rarely, and a library of 1,700 titles would ask
TMDB 1,700 times per run without a rule. So Trailarr asks about a media
item only when it has never asked, or when the last answer is older than
the time to live.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.trailers.trailers.missing import (
    VIDEOS_TTL,
    refresh_videos_if_stale,
)

PKG = "services.trailers.trailers.missing"


def _media(last_refresh):
    media = MagicMock()
    media.id = 1
    media.title = "TTL Movie"
    media.last_videos_refresh = last_refresh
    return media


def _refresher(enabled=True):
    refresher = MagicMock()
    refresher.enabled = enabled
    refresher.refresh_media = AsyncMock(return_value=1)
    return refresher


class TestFreshness:

    @pytest.mark.asyncio
    async def test_an_item_never_asked_about_is_asked_about(self):
        refresher = _refresher()
        with patch(f"{PKG}.media_manager") as manager:
            asked = await refresh_videos_if_stale(_media(None), refresher)

        assert asked is True
        refresher.refresh_media.assert_awaited_once()
        manager.mark_videos_refreshed.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_a_fresh_answer_is_left_alone(self):
        recent = datetime.now(timezone.utc) - timedelta(days=1)
        refresher = _refresher()
        with patch(f"{PKG}.media_manager"):
            asked = await refresh_videos_if_stale(_media(recent), refresher)

        assert asked is False
        refresher.refresh_media.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_an_old_answer_is_asked_about_again(self):
        old = datetime.now(timezone.utc) - (VIDEOS_TTL + timedelta(days=1))
        refresher = _refresher()
        with patch(f"{PKG}.media_manager"):
            asked = await refresh_videos_if_stale(_media(old), refresher)

        assert asked is True

    @pytest.mark.asyncio
    async def test_a_timestamp_without_a_timezone_is_read_as_utc(self):
        """SQLite gives back a naive datetime, and comparing one with an
        aware datetime raises. That would stop the download task."""
        naive = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
            tzinfo=None
        )
        refresher = _refresher()
        with patch(f"{PKG}.media_manager"):
            asked = await refresh_videos_if_stale(_media(naive), refresher)

        assert asked is False

    @pytest.mark.asyncio
    async def test_nothing_happens_without_a_key(self):
        """Wargame W8: the guard is at the entry, not at each call."""
        refresher = _refresher(enabled=False)
        with patch(f"{PKG}.media_manager") as manager:
            asked = await refresh_videos_if_stale(_media(None), refresher)

        assert asked is False
        refresher.refresh_media.assert_not_awaited()
        manager.mark_videos_refreshed.assert_not_called()

    @pytest.mark.asyncio
    async def test_an_item_tmdb_knows_nothing_about_is_still_marked(self):
        """Otherwise every run asks about it again."""
        refresher = _refresher()
        refresher.refresh_media = AsyncMock(return_value=0)
        with patch(f"{PKG}.media_manager") as manager:
            await refresh_videos_if_stale(_media(None), refresher)

        manager.mark_videos_refreshed.assert_called_once_with(1)
