"""Tests for refresh_plex_trailer_flags in services/plex_service.py"""

import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.plex_service import refresh_plex_trailer_flags


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
        from db.models.connection import ArrType

        non_plex = SimpleNamespace(id=1, arr_type=ArrType.RADARR)
        with (
            patch(
                "services.plex_service.connection_repo.read_all",
                return_value=[non_plex],
            ),
            patch(
                "services.plex_service.media_repo.read_all_generator"
            ) as mock_gen,
        ):
            await refresh_plex_trailer_flags()
            mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_event_terminates_promptly(self):
        from db.models.connection import ArrType

        conn = SimpleNamespace(id=1, arr_type=ArrType.PLEX, url="http://plex.local", api_key="tok")
        stop = threading.Event()
        stop.set()

        mock_api = AsyncMock()

        with (
            patch(
                "services.plex_service.connection_repo.read_all",
                return_value=[conn],
            ),
            patch(
                "services.plex_service.media_repo.read_all_generator",
                return_value=iter([_make_media()]),
            ),
            patch(
                "services.plex_service.media_repo.update_plex_trailer_bulk"
            ) as mock_bulk,
            patch("services.plex_service.PlexAPI", return_value=mock_api),
        ):
            await refresh_plex_trailer_flags(_stop_event=stop)
            mock_api.get_library_item_extras.assert_not_called()
            mock_bulk.assert_not_called()

    @pytest.mark.asyncio
    async def test_per_item_errors_do_not_abort_run(self):
        from db.models.connection import ArrType

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
                "services.plex_service.connection_repo.read_all",
                return_value=[conn],
            ),
            patch(
                "services.plex_service.media_repo.read_all_generator",
                return_value=iter([media1, media2]),
            ),
            patch(
                "services.plex_service.media_repo.update_plex_trailer_bulk"
            ) as mock_bulk,
            patch(
                "services.plex_service.PlexAPI",
                return_value=mock_api,
            ),
        ):
            await refresh_plex_trailer_flags()
            mock_bulk.assert_called_once_with([(2, True)])

    @pytest.mark.asyncio
    async def test_plex_linked_items_get_db_update(self):
        from db.models.connection import ArrType

        conn = SimpleNamespace(id=1, arr_type=ArrType.PLEX, url="http://plex.local", api_key="tok")
        media_with_trailer = _make_media(media_id=10, plex_rating_key="10")
        media_no_trailer = _make_media(media_id=11, plex_rating_key="11")

        mock_api = AsyncMock()
        mock_api.get_library_item_extras.side_effect = [
            [_make_extra("trailer", "http://remote")],
            [_make_extra("trailer", "file:///local")],
        ]

        with (
            patch(
                "services.plex_service.connection_repo.read_all",
                return_value=[conn],
            ),
            patch(
                "services.plex_service.media_repo.read_all_generator",
                return_value=iter([media_with_trailer, media_no_trailer]),
            ),
            patch(
                "services.plex_service.media_repo.update_plex_trailer_bulk"
            ) as mock_bulk,
            patch(
                "services.plex_service.PlexAPI",
                return_value=mock_api,
            ),
        ):
            await refresh_plex_trailer_flags()
            mock_bulk.assert_called_once_with([(10, True), (11, False)])
