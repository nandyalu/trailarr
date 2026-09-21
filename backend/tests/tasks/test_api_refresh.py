"""Tests for the Arr/Plex data refresh task.

One connection that cannot be reached must cost only itself. Before the
guard, an unreachable Plex server stopped the refresh for every connection
after it in the list, and the image refresh never ran — found by driving a
copy of a real library with the connections pointed at a dead address.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tasks.api_refresh import api_refresh

PKG = "tasks.api_refresh"


def _conn(name: str) -> MagicMock:
    c = MagicMock()
    c.name = name
    return c


class TestApiRefreshKeepsGoing:

    @pytest.mark.asyncio
    async def test_one_unreachable_connection_does_not_stop_the_others(self):
        """A failure on the first connection must not skip the rest."""
        conns = [_conn("Plex"), _conn("Radarr"), _conn("Sonarr")]
        seen = []

        async def refresh_one(connection, image_refresh=False, **kw):
            seen.append(connection.name)
            if connection.name == "Plex":
                raise ConnectionError("Cannot connect to host 127.0.0.1:1")

        with (
            patch(f"{PKG}.connection_manager.read_all", return_value=conns),
            patch(f"{PKG}.api_refresh_by_id", side_effect=refresh_one),
            patch(f"{PKG}.refresh_images", new_callable=AsyncMock) as images,
        ):
            await api_refresh()

        assert seen == ["Plex", "Radarr", "Sonarr"]
        # The image refresh sits after the loop; the old code never reached it.
        images.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_every_connection_failing_still_finishes_the_task(self):
        """All connections down is a bad day, not an exception."""
        conns = [_conn("Radarr"), _conn("Sonarr")]

        with (
            patch(f"{PKG}.connection_manager.read_all", return_value=conns),
            patch(
                f"{PKG}.api_refresh_by_id",
                side_effect=ConnectionError("refused"),
            ),
            patch(f"{PKG}.refresh_images", new_callable=AsyncMock) as images,
        ):
            await api_refresh()

        images.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_stop_request_still_stops_the_loop(self):
        """The guard must not swallow a stop event into 'keep going'."""
        conns = [_conn("Radarr"), _conn("Sonarr")]
        stop = MagicMock()
        stop.is_set.return_value = True
        refresh_one = AsyncMock()

        with (
            patch(f"{PKG}.connection_manager.read_all", return_value=conns),
            patch(f"{PKG}.api_refresh_by_id", refresh_one),
            patch(f"{PKG}.refresh_images", new_callable=AsyncMock) as images,
        ):
            await api_refresh(_stop_event=stop)

        refresh_one.assert_not_awaited()
        images.assert_not_awaited()
