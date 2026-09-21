"""Tests for the video refresh task — plans/phase-08-tmdb.md decision 3.

The task runs ahead of the download task so the Known videos list is
filled in before anyone waits for a download. Wargame W4 is the point of
the limit: a library of 1,700 items must not send 1,700 requests at once.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tasks.videos_refresh import MAX_ITEMS_PER_RUN, refresh_media_videos

PKG = "tasks.videos_refresh"


def _pending(*media_ids):
    summary = MagicMock()
    summary.items = [MagicMock(media_id=i) for i in media_ids]
    return summary


class TestRefreshTask:

    @pytest.mark.asyncio
    async def test_nothing_happens_without_a_key(self):
        with patch(f"{PKG}.TMDBRefresher") as refresher_cls:
            refresher_cls.return_value.enabled = False
            with patch(f"{PKG}.compute_library_pending") as pending:
                await refresh_media_videos()

        pending.assert_not_called()

    @pytest.mark.asyncio
    async def test_only_the_waiting_items_are_asked_about(self):
        with patch(f"{PKG}.TMDBRefresher") as refresher_cls:
            refresher_cls.return_value.enabled = True
            with patch(f"{PKG}.compute_library_pending", return_value=_pending(4, 7)):
                with patch(f"{PKG}.media_manager") as media_manager:
                    with patch(
                        f"{PKG}.refresh_videos_if_stale", new=AsyncMock(return_value=True)
                    ) as refresh:
                        await refresh_media_videos()

        assert refresh.await_count == 2
        assert [c.args[0] for c in media_manager.read.call_args_list] == [4, 7]

    @pytest.mark.asyncio
    async def test_a_run_stops_at_the_limit(self):
        """Wargame W4: a first run over a large library is spread out."""
        many = _pending(*range(MAX_ITEMS_PER_RUN + 50))
        with patch(f"{PKG}.TMDBRefresher") as refresher_cls:
            refresher_cls.return_value.enabled = True
            with patch(f"{PKG}.compute_library_pending", return_value=many):
                with patch(f"{PKG}.media_manager"):
                    with patch(
                        f"{PKG}.refresh_videos_if_stale", new=AsyncMock(return_value=True)
                    ) as refresh:
                        with patch(f"{PKG}.asyncio.sleep", new=AsyncMock()):
                            await refresh_media_videos()

        assert refresh.await_count == MAX_ITEMS_PER_RUN

    @pytest.mark.asyncio
    async def test_a_fresh_item_does_not_count_against_the_limit(self):
        """Skipping costs no request, so a library that is already fresh
        moves through in one run."""
        with patch(f"{PKG}.TMDBRefresher") as refresher_cls:
            refresher_cls.return_value.enabled = True
            with patch(f"{PKG}.compute_library_pending", return_value=_pending(*range(10))):
                with patch(f"{PKG}.media_manager"):
                    with patch(
                        f"{PKG}.refresh_videos_if_stale",
                        new=AsyncMock(return_value=False),
                    ) as refresh:
                        await refresh_media_videos()

        assert refresh.await_count == 10

    @pytest.mark.asyncio
    async def test_a_stop_ends_the_run(self):
        stop = MagicMock()
        stop.is_set.return_value = True
        with patch(f"{PKG}.TMDBRefresher") as refresher_cls:
            refresher_cls.return_value.enabled = True
            with patch(f"{PKG}.compute_library_pending", return_value=_pending(1, 2, 3)):
                with patch(f"{PKG}.media_manager"):
                    with patch(
                        f"{PKG}.refresh_videos_if_stale", new=AsyncMock()
                    ) as refresh:
                        await refresh_media_videos(_stop_event=stop)

        refresh.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_key_refused_mid_run_ends_the_run(self):
        """Wargame W1: the refresher turns itself off, and the task notices."""
        refresher = MagicMock()
        refresher.enabled = True

        async def refresh_then_disable(media, r):
            refresher.enabled = False
            return True

        with patch(f"{PKG}.TMDBRefresher", return_value=refresher):
            with patch(f"{PKG}.compute_library_pending", return_value=_pending(1, 2, 3)):
                with patch(f"{PKG}.media_manager"):
                    with patch(
                        f"{PKG}.refresh_videos_if_stale",
                        new=AsyncMock(side_effect=refresh_then_disable),
                    ) as refresh:
                        with patch(f"{PKG}.asyncio.sleep", new=AsyncMock()):
                            await refresh_media_videos()

        assert refresh.await_count == 1
