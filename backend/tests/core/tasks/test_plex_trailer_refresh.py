"""Tests for refresh_plex_trailer_flags in core/tasks/plex_trailer_refresh.py"""

import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.tasks.plex_trailer_refresh import refresh_plex_trailer_flags


def _make_connection(conn_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=conn_id,
        url="http://plex.local:32400",
        api_key="fake-token",
        arr_type="plex",
    )


def _make_media(
    media_id: int = 1,
    plex_connection_id: int = 1,
    plex_rating_key: str = "42",
    title: str = "Test Movie",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        plex_connection_id=plex_connection_id,
        plex_rating_key=plex_rating_key,
        title=title,
    )


def _make_extra(subtype: str = "trailer", guid: str = "http://remote") -> SimpleNamespace:
    return SimpleNamespace(subtype=subtype, guid=guid)


class TestRefreshPlexTrailerFlags:

    @pytest.mark.asyncio
    async def test_no_plex_connections_exits_early(self):
        """When no Plex connections exist, the media manager is never queried."""
        from core.base.database.models.connection import ArrType

        non_plex = SimpleNamespace(id=1, arr_type=ArrType.RADARR)
        with (
            patch(
                "core.tasks.plex_trailer_refresh.connection_manager.read_all",
                return_value=[non_plex],
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.read_all_generator"
            ) as mock_gen,
        ):
            await refresh_plex_trailer_flags()
            mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_event_terminates_promptly(self):
        """When the stop event is set before the first item, no Plex API calls or DB writes occur."""
        from core.base.database.models.connection import ArrType

        conn = SimpleNamespace(id=1, arr_type=ArrType.PLEX, url="http://plex.local", api_key="tok")
        stop = threading.Event()
        stop.set()

        mock_api = AsyncMock()

        with (
            patch(
                "core.tasks.plex_trailer_refresh.connection_manager.read_all",
                return_value=[conn],
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.read_all_generator",
                return_value=iter([_make_media()]),
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.update_plex_trailer_bulk"
            ) as mock_bulk,
            patch("core.tasks.plex_trailer_refresh.PlexAPI", return_value=mock_api),
        ):
            await refresh_plex_trailer_flags(_stop_event=stop)
            # Cache is built upfront, but no item-level API calls or DB writes should occur.
            mock_api.get_library_item_extras.assert_not_called()
            mock_bulk.assert_not_called()

    @pytest.mark.asyncio
    async def test_per_item_errors_do_not_abort_run(self):
        """An API error on one item does not stop processing of subsequent items."""
        from core.base.database.models.connection import ArrType

        conn = SimpleNamespace(id=1, arr_type=ArrType.PLEX, url="http://plex.local", api_key="tok")
        media1 = _make_media(media_id=1, plex_rating_key="1")
        media2 = _make_media(media_id=2, plex_rating_key="2")

        mock_api = AsyncMock()
        mock_api.get_library_item_extras.side_effect = [
            Exception("Plex API error"),
            [_make_extra("trailer", "http://remote")],
        ]

        with (
            patch(
                "core.tasks.plex_trailer_refresh.connection_manager.read_all",
                return_value=[conn],
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.read_all_generator",
                return_value=iter([media1, media2]),
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.update_plex_trailer_bulk"
            ) as mock_bulk,
            patch(
                "core.tasks.plex_trailer_refresh.PlexAPI",
                return_value=mock_api,
            ),
        ):
            await refresh_plex_trailer_flags()
            # media2 must still be included despite media1 raising
            mock_bulk.assert_called_once_with([(2, True)])

    @pytest.mark.asyncio
    async def test_plex_linked_items_get_db_update(self):
        """For valid items, update_plex_trailer_bulk is called with the correct flags."""
        from core.base.database.models.connection import ArrType

        conn = SimpleNamespace(id=1, arr_type=ArrType.PLEX, url="http://plex.local", api_key="tok")
        media_with_trailer = _make_media(media_id=10, plex_rating_key="10")
        media_no_trailer = _make_media(media_id=11, plex_rating_key="11")

        mock_api = AsyncMock()
        mock_api.get_library_item_extras.side_effect = [
            [_make_extra("trailer", "http://remote")],   # has remote trailer
            [_make_extra("trailer", "file:///local")],   # local file → not counted
        ]

        with (
            patch(
                "core.tasks.plex_trailer_refresh.connection_manager.read_all",
                return_value=[conn],
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.read_all_generator",
                return_value=iter([media_with_trailer, media_no_trailer]),
            ),
            patch(
                "core.tasks.plex_trailer_refresh.media_manager.update_plex_trailer_bulk"
            ) as mock_bulk,
            patch(
                "core.tasks.plex_trailer_refresh.PlexAPI",
                return_value=mock_api,
            ),
        ):
            await refresh_plex_trailer_flags()
            mock_bulk.assert_called_once_with([(10, True), (11, False)])
