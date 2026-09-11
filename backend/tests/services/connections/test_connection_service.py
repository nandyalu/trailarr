"""Tests for the create and update order of work.

Phase 7 Stage B moved this out of the database layer. What matters here is
the order: probe the server first, write the row only after that succeeds.
"""

from unittest.mock import patch

import pytest

import database.manager.connection as connection_db
from database.models.connection import (
    ArrType,
    ConnectionCreate,
    ConnectionUpdate,
)
from exceptions import InvalidResponseError, ItemNotFoundError
from services.connections import service

PKG = "services.connections.service"


def _new_connection(arr_type: ArrType = ArrType.RADARR) -> ConnectionCreate:
    return ConnectionCreate(
        name="Service Test",
        arr_type=arr_type,
        url="http://example.com",
        api_key="API_KEY",
        monitor_new_media=True,
        path_mappings=[],
    )


class TestCreate:

    @pytest.mark.asyncio
    async def test_create_validates_then_saves(self):
        with patch(
            f"{PKG}.probe.validate_connection", return_value="Radarr 5.0"
        ) as mock_validate:
            status, conn_id = await service.create(_new_connection())

        assert status == "Radarr 5.0"
        assert mock_validate.await_count == 1
        # The row is really there
        assert connection_db.read(conn_id).name == "Service Test"

    @pytest.mark.asyncio
    async def test_a_failed_probe_writes_nothing(self):
        """The whole point of the split: no row when the server rejects us."""
        before = len(connection_db.read_all())
        with patch(
            f"{PKG}.probe.validate_connection",
            side_effect=InvalidResponseError("bad key"),
        ):
            with pytest.raises(InvalidResponseError):
                await service.create(_new_connection())

        assert len(connection_db.read_all()) == before

    @pytest.mark.asyncio
    async def test_plex_create_stores_the_machine_identifier(self):
        with (
            patch(f"{PKG}.probe.validate_connection", return_value="Plex 1.0"),
            patch(
                f"{PKG}.probe.get_machine_identifier", return_value="machine-1"
            ) as mock_id,
        ):
            _, conn_id = await service.create(_new_connection(ArrType.PLEX))

        assert mock_id.await_count == 1
        assert connection_db.read(conn_id).machine_identifier == "machine-1"

    @pytest.mark.asyncio
    async def test_arr_create_does_not_ask_for_a_machine_identifier(self):
        with (
            patch(f"{PKG}.probe.validate_connection", return_value="Radarr"),
            patch(f"{PKG}.probe.get_machine_identifier") as mock_id,
        ):
            await service.create(_new_connection(ArrType.RADARR))

        mock_id.assert_not_called()


class TestUpdate:

    @pytest.mark.asyncio
    async def test_update_validates_the_merged_connection(self):
        """The probe must see the NEW url, not the stored one."""
        with patch(f"{PKG}.probe.validate_connection", return_value="ok"):
            _, conn_id = await service.create(_new_connection())

        with patch(
            f"{PKG}.probe.validate_connection", return_value="ok"
        ) as mock_validate:
            await service.update(
                conn_id,
                ConnectionUpdate(
                    url="http://changed.example.com", path_mappings=[]
                ),
            )

        probed = mock_validate.await_args.args[0]
        assert probed.url == "http://changed.example.com"
        # Fields the update left out still come from the stored row
        assert probed.api_key == "API_KEY"
        assert probed.arr_type == ArrType.RADARR

    @pytest.mark.asyncio
    async def test_a_failed_probe_leaves_the_row_alone(self):
        with patch(f"{PKG}.probe.validate_connection", return_value="ok"):
            _, conn_id = await service.create(_new_connection())

        with patch(
            f"{PKG}.probe.validate_connection",
            side_effect=InvalidResponseError("unreachable"),
        ):
            with pytest.raises(InvalidResponseError):
                await service.update(
                    conn_id,
                    ConnectionUpdate(
                        url="http://changed.example.com", path_mappings=[]
                    ),
                )

        assert connection_db.read(conn_id).url == "http://example.com"

    @pytest.mark.asyncio
    async def test_unknown_id_raises_before_any_probe(self):
        with patch(f"{PKG}.probe.validate_connection") as mock_validate:
            with pytest.raises(ItemNotFoundError):
                await service.update(
                    1_000, ConnectionUpdate(path_mappings=[])
                )

        mock_validate.assert_not_called()
