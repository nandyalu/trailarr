"""Comprehensive tests for services/connection_service.py."""

import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from db.models.connection import ArrType, ConnectionBase, ConnectionCreate, ConnectionUpdate, MonitorType
from db.models.issue import EntityType, IssueType
from exceptions import InvalidResponseError, ItemNotFoundError
from services import connection_service


# ─── validate_connection ─────────────────────────────────────────────────────

class TestValidateConnection:

    @pytest.mark.asyncio
    async def test_raises_when_connection_is_none(self):
        with pytest.raises(ItemNotFoundError):
            await connection_service.validate_connection(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_radarr_calls_radarr_manager(self):
        conn = ConnectionBase(name="R", arr_type=ArrType.RADARR, url="http://r", api_key="k", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.arr.radarr.RadarrManager.get_system_status", new_callable=AsyncMock, return_value="7.0") as mock_status:
            result = await connection_service.validate_connection(conn)
        assert result == "7.0"
        mock_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_sonarr_calls_sonarr_manager(self):
        conn = ConnectionBase(name="S", arr_type=ArrType.SONARR, url="http://s", api_key="k", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.arr.sonarr.SonarrManager.get_system_status", new_callable=AsyncMock, return_value="4.0") as mock_status:
            result = await connection_service.validate_connection(conn)
        assert result == "4.0"

    @pytest.mark.asyncio
    async def test_plex_calls_plex_api(self):
        conn = ConnectionBase(name="P", arr_type=ArrType.PLEX, url="http://p", api_key="t", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.plex.client.PlexAPI.get_system_status", new_callable=AsyncMock, return_value="1.0"):
            result = await connection_service.validate_connection(conn)
        assert result == "1.0"

    @pytest.mark.asyncio
    async def test_unknown_arr_type_returns_empty_string(self):
        conn = MagicMock()
        conn.arr_type = "EMBY"
        conn.__bool__ = lambda self: True
        result = await connection_service.validate_connection(conn)
        assert result == ""

    @pytest.mark.asyncio
    async def test_propagates_invalid_response_error(self):
        conn = ConnectionBase(name="R", arr_type=ArrType.RADARR, url="http://r", api_key="k", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.arr.radarr.RadarrManager.get_system_status", new_callable=AsyncMock, side_effect=InvalidResponseError("bad key")):
            with pytest.raises(InvalidResponseError):
                await connection_service.validate_connection(conn)


# ─── get_rootfolders ──────────────────────────────────────────────────────────

class TestGetRootfolders:

    @pytest.mark.asyncio
    async def test_raises_when_connection_is_none(self):
        with pytest.raises(ItemNotFoundError):
            await connection_service.get_rootfolders(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_radarr_returns_rootfolders(self):
        conn = ConnectionBase(name="R", arr_type=ArrType.RADARR, url="http://r", api_key="k", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.arr.radarr.RadarrManager.get_rootfolders", new_callable=AsyncMock, return_value=["/movies"]):
            result = await connection_service.get_rootfolders(conn)
        assert result == ["/movies"]

    @pytest.mark.asyncio
    async def test_sonarr_returns_rootfolders(self):
        conn = ConnectionBase(name="S", arr_type=ArrType.SONARR, url="http://s", api_key="k", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.arr.sonarr.SonarrManager.get_rootfolders", new_callable=AsyncMock, return_value=["/tv"]):
            result = await connection_service.get_rootfolders(conn)
        assert result == ["/tv"]

    @pytest.mark.asyncio
    async def test_plex_returns_library_folders(self):
        conn = ConnectionBase(name="P", arr_type=ArrType.PLEX, url="http://p", api_key="t", monitor=MonitorType.MONITOR_NEW)
        with patch("integrations.plex.client.PlexAPI.get_library_folders", new_callable=AsyncMock, return_value=["/mnt"]):
            result = await connection_service.get_rootfolders(conn)
        assert result == ["/mnt"]

    @pytest.mark.asyncio
    async def test_unknown_type_returns_empty_list(self):
        conn = MagicMock()
        conn.arr_type = "UNKNOWN"
        conn.__bool__ = lambda self: True
        result = await connection_service.get_rootfolders(conn)
        assert result == []


# ─── create ───────────────────────────────────────────────────────────────────

class TestCreate:

    @pytest.mark.asyncio
    async def test_create_radarr_connection_validates_and_saves(self):
        conn_create = ConnectionCreate(
            name="Radarr", arr_type=ArrType.RADARR,
            url="http://r", api_key="k",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[],
        )
        mock_read = MagicMock()
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, return_value="7.0"),
            patch("services.connection_service.connection_repo.save", return_value=1),
            patch("services.connection_service.connection_repo.read", return_value=mock_read),
        ):
            result, new_id = await connection_service.create(conn_create)

        assert result is mock_read
        assert new_id == 1

    @pytest.mark.asyncio
    async def test_create_plex_fetches_machine_identifier(self):
        conn_create = ConnectionCreate(
            name="Plex", arr_type=ArrType.PLEX,
            url="http://p", api_key="t",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[],
        )
        mock_read = MagicMock()
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, return_value="1.0"),
            patch("integrations.plex.client.PlexAPI.get_machine_identifier", new_callable=AsyncMock, return_value="machine-abc"),
            patch("services.connection_service.connection_repo.save", return_value=2) as mock_save,
            patch("services.connection_service.connection_repo.read", return_value=mock_read),
        ):
            result, new_id = await connection_service.create(conn_create)

        # Verify machine_identifier was written to the DB conn object
        saved_obj = mock_save.call_args[0][0]
        assert saved_obj.machine_identifier == "machine-abc"

    @pytest.mark.asyncio
    async def test_validation_failure_raises_before_saving(self):
        conn_create = ConnectionCreate(
            name="Bad", arr_type=ArrType.RADARR,
            url="http://bad", api_key="wrong",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[],
        )
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, side_effect=InvalidResponseError("bad")),
            patch("services.connection_service.connection_repo.save") as mock_save,
        ):
            with pytest.raises(InvalidResponseError):
                await connection_service.create(conn_create)
        mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_path_mappings_trailing_slashes_normalized(self):
        from db.models.connection import PathMappingCRU
        # Paths WITHOUT trailing slashes — normalize_trailing_slash adds them
        pm = PathMappingCRU(path_from="/src", path_to="/dst")
        conn_create = ConnectionCreate(
            name="R", arr_type=ArrType.RADARR,
            url="http://r", api_key="k",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[pm],
        )
        mock_read = MagicMock()
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, return_value="ok"),
            patch("services.connection_service.connection_repo.save", return_value=1) as mock_save,
            patch("services.connection_service.connection_repo.read", return_value=mock_read),
        ):
            await connection_service.create(conn_create)

        saved = mock_save.call_args[0][0]
        # normalize_trailing_slash ensures paths end with a slash
        assert saved.path_mappings[0].path_from.endswith("/")
        assert saved.path_mappings[0].path_to.endswith("/")


# ─── update ───────────────────────────────────────────────────────────────────

class TestUpdate:

    @pytest.mark.asyncio
    async def test_update_radarr_validates_and_calls_repo(self):
        conn_update = ConnectionUpdate(
            arr_type=ArrType.RADARR, url="http://r", api_key="k",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[],
        )
        mock_result = MagicMock()
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, return_value="ok"),
            patch("services.connection_service.connection_repo.update", return_value=mock_result) as mock_update,
        ):
            result = await connection_service.update(3, conn_update)

        assert result is mock_result
        mock_update.assert_called_once_with(3, conn_update, None)

    @pytest.mark.asyncio
    async def test_update_plex_fetches_machine_identifier(self):
        conn_update = ConnectionUpdate(
            arr_type=ArrType.PLEX, url="http://p", api_key="t",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[],
        )
        mock_result = MagicMock()
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, return_value="ok"),
            patch("integrations.plex.client.PlexAPI.get_machine_identifier", new_callable=AsyncMock, return_value="machine-xyz"),
            patch("services.connection_service.connection_repo.update", return_value=mock_result) as mock_update,
        ):
            result = await connection_service.update(7, conn_update)

        mock_update.assert_called_once_with(7, conn_update, "machine-xyz")

    @pytest.mark.asyncio
    async def test_update_propagates_validation_error(self):
        conn_update = ConnectionUpdate(
            arr_type=ArrType.SONARR, url="http://bad", api_key="x",
            monitor=MonitorType.MONITOR_NEW, path_mappings=[],
        )
        with (
            patch("services.connection_service.validate_connection", new_callable=AsyncMock, side_effect=InvalidResponseError("bad")),
            patch("services.connection_service.connection_repo.update") as mock_update,
        ):
            with pytest.raises(InvalidResponseError):
                await connection_service.update(1, conn_update)
        mock_update.assert_not_called()


# ─── delete ───────────────────────────────────────────────────────────────────

class TestDelete:

    def test_delete_arr_connection_no_plex_events(self):
        conn = MagicMock()
        conn.arr_type = ArrType.RADARR
        with (
            patch("services.connection_service.connection_repo.read", return_value=conn),
            patch("services.connection_service.connection_repo.read_arr_linked_to_plex") as mock_linked,
            patch("services.connection_service.track_plex_unlinked") as mock_track,
            patch("services.connection_service.issue_repo.resolve_all_for_entity", return_value=0),
            patch("services.connection_service.ws_broadcast"),
            patch("services.connection_service.connection_repo.delete", return_value=True),
        ):
            result = connection_service.delete(1)

        assert result is True
        mock_linked.assert_not_called()
        mock_track.assert_not_called()

    def test_delete_plex_connection_fires_unlinked_events_for_arr_linked_media(self):
        conn = MagicMock()
        conn.arr_type = ArrType.PLEX
        conn.name = "MyPlex"
        linked_media = [MagicMock(id=10), MagicMock(id=20)]

        with (
            patch("services.connection_service.connection_repo.read", return_value=conn),
            patch("services.connection_service.connection_repo.read_arr_linked_to_plex", return_value=linked_media),
            patch("services.connection_service.track_plex_unlinked") as mock_track,
            patch("services.connection_service.issue_repo.resolve_all_for_entity", return_value=0),
            patch("services.connection_service.ws_broadcast"),
            patch("services.connection_service.connection_repo.delete", return_value=True),
        ):
            result = connection_service.delete(5)

        assert result is True
        assert mock_track.call_count == 2
        tracked_ids = {c.kwargs["media_id"] for c in mock_track.call_args_list}
        assert tracked_ids == {10, 20}

    def test_delete_plex_with_no_linked_media_no_events(self):
        conn = MagicMock()
        conn.arr_type = ArrType.PLEX
        conn.name = "MyPlex"

        with (
            patch("services.connection_service.connection_repo.read", return_value=conn),
            patch("services.connection_service.connection_repo.read_arr_linked_to_plex", return_value=[]),
            patch("services.connection_service.track_plex_unlinked") as mock_track,
            patch("services.connection_service.issue_repo.resolve_all_for_entity", return_value=0),
            patch("services.connection_service.ws_broadcast"),
            patch("services.connection_service.connection_repo.delete", return_value=True),
        ):
            connection_service.delete(5)

        mock_track.assert_not_called()

    def test_delete_resolves_all_issues_for_connection(self):
        conn = MagicMock()
        conn.arr_type = ArrType.RADARR

        with (
            patch("services.connection_service.connection_repo.read", return_value=conn),
            patch("services.connection_service.issue_repo.resolve_all_for_entity", return_value=2) as mock_resolve,
            patch("services.connection_service.ws_broadcast") as mock_ws,
            patch("services.connection_service.connection_repo.delete", return_value=True),
        ):
            connection_service.delete(7)

        mock_resolve.assert_called_once()
        assert mock_resolve.call_args.args[1] == 7
        mock_ws.assert_called_once()

    def test_delete_no_issues_no_ws_broadcast(self):
        conn = MagicMock()
        conn.arr_type = ArrType.RADARR

        with (
            patch("services.connection_service.connection_repo.read", return_value=conn),
            patch("services.connection_service.issue_repo.resolve_all_for_entity", return_value=0),
            patch("services.connection_service.ws_broadcast") as mock_ws,
            patch("services.connection_service.connection_repo.delete", return_value=True),
        ):
            connection_service.delete(8)

        mock_ws.assert_not_called()

    def test_delete_clears_consecutive_failures_counter(self):
        conn = MagicMock()
        conn.arr_type = ArrType.RADARR
        connection_service._consecutive_failures[99] = 5

        with (
            patch("services.connection_service.connection_repo.read", return_value=conn),
            patch("services.connection_service.issue_repo.resolve_all_for_entity", return_value=0),
            patch("services.connection_service.ws_broadcast"),
            patch("services.connection_service.connection_repo.delete", return_value=True),
        ):
            connection_service.delete(99)

        assert 99 not in connection_service._consecutive_failures


# ─── _is_auth_error ───────────────────────────────────────────────────────────

class TestIsAuthError:

    def test_recognizes_unauthorized(self):
        assert connection_service._is_auth_error(Exception("Unauthorized access")) is True

    def test_recognizes_access_restricted(self):
        assert connection_service._is_auth_error(Exception("Access restricted to this resource")) is True

    def test_recognizes_api_key(self):
        assert connection_service._is_auth_error(Exception("Invalid API key provided")) is True

    def test_case_insensitive(self):
        assert connection_service._is_auth_error(Exception("UNAUTHORIZED")) is True

    def test_recognizes_plex_authentication_failed(self):
        assert connection_service._is_auth_error(
            Exception("Plex authentication failed — invalid token")
        ) is True

    def test_recognizes_authentication_failed_generic(self):
        assert connection_service._is_auth_error(Exception("authentication failed")) is True

    def test_recognizes_invalid_token_standalone(self):
        assert connection_service._is_auth_error(Exception("invalid token provided")) is True

    def test_generic_error_is_not_auth(self):
        assert connection_service._is_auth_error(Exception("Connection timed out")) is False

    def test_network_error_is_not_auth(self):
        assert connection_service._is_auth_error(Exception("Cannot connect to host")) is False


# ─── refresh_connection ───────────────────────────────────────────────────────

class TestRefreshConnection:

    def _make_conn(self, arr_type: ArrType, conn_id: int = 1) -> MagicMock:
        conn = MagicMock()
        conn.id = conn_id
        conn.arr_type = arr_type
        conn.name = f"Conn-{conn_id}"
        return conn

    @pytest.mark.asyncio
    async def test_success_clears_failure_count_and_resolves_issues(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=10)
        connection_service._consecutive_failures[10] = 5

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh", new_callable=AsyncMock),
            patch("services.connection_service.issue_repo.resolve") as mock_resolve,
            patch("services.connection_service.ws_broadcast"),
        ):
            await connection_service.refresh_connection(conn)

        assert 10 not in connection_service._consecutive_failures
        assert mock_resolve.call_count == 2
        resolved_types = {c.args[0] for c in mock_resolve.call_args_list}
        assert IssueType.CONNECTION_FAILED in resolved_types
        assert IssueType.TOKEN_INVALID in resolved_types

    @pytest.mark.asyncio
    async def test_auth_error_upserts_token_invalid_issue(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=20)
        connection_service._consecutive_failures.pop(20, None)

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh",
                  new_callable=AsyncMock, side_effect=Exception("Unauthorized: bad token")),
            patch("services.connection_service.issue_repo.upsert") as mock_upsert,
            patch("services.connection_service.issue_repo.resolve"),
            patch("services.connection_service.ws_broadcast"),
        ):
            await connection_service.refresh_connection(conn)

        mock_upsert.assert_called_once()
        assert mock_upsert.call_args.kwargs["issue_type"] == IssueType.TOKEN_INVALID

    @pytest.mark.asyncio
    async def test_failure_below_threshold_does_not_upsert_connection_failed(self):
        conn = self._make_conn(ArrType.SONARR, conn_id=30)
        connection_service._consecutive_failures.pop(30, None)

        with (
            patch("integrations.arr.sonarr.SonarrConnectionManager.refresh",
                  new_callable=AsyncMock, side_effect=Exception("generic error")),
            patch("services.connection_service.issue_repo.upsert") as mock_upsert,
            patch("services.connection_service.ws_broadcast"),
        ):
            await connection_service.refresh_connection(conn)

        # 1 failure < threshold (3), no upsert
        mock_upsert.assert_not_called()
        assert connection_service._consecutive_failures.get(30) == 1

    @pytest.mark.asyncio
    async def test_failure_at_threshold_upserts_connection_failed(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=40)
        connection_service._consecutive_failures[40] = 2  # next failure hits threshold 3

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh",
                  new_callable=AsyncMock, side_effect=Exception("network error")),
            patch("services.connection_service.issue_repo.upsert") as mock_upsert,
            patch("services.connection_service.ws_broadcast"),
        ):
            await connection_service.refresh_connection(conn)

        mock_upsert.assert_called_once()
        assert mock_upsert.call_args.kwargs["issue_type"] == IssueType.CONNECTION_FAILED
        assert connection_service._consecutive_failures[40] == 3

    @pytest.mark.asyncio
    async def test_failure_accumulates_across_calls(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=50)
        connection_service._consecutive_failures.pop(50, None)

        for _ in range(2):
            with (
                patch("integrations.arr.radarr.RadarrConnectionManager.refresh",
                      new_callable=AsyncMock, side_effect=Exception("error")),
                patch("services.connection_service.issue_repo.upsert"),
                patch("services.connection_service.ws_broadcast"),
            ):
                await connection_service.refresh_connection(conn)

        assert connection_service._consecutive_failures[50] == 2

    @pytest.mark.asyncio
    async def test_plex_uses_plex_manager(self):
        conn = self._make_conn(ArrType.PLEX, conn_id=60)
        connection_service._consecutive_failures.pop(60, None)

        with (
            patch("integrations.plex.sync.PlexConnectionManager.refresh", new_callable=AsyncMock) as mock_refresh,
            patch("services.connection_service.issue_repo.resolve", return_value=False),
            patch("services.connection_service.ws_broadcast"),
        ):
            await connection_service.refresh_connection(conn)

        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_arr_type_returns_without_refresh(self):
        conn = MagicMock()
        conn.id = 99
        conn.arr_type = "EMBY"
        conn.name = "Emby"

        with patch("services.connection_service.issue_repo.resolve") as mock_resolve:
            await connection_service.refresh_connection(conn)

        mock_resolve.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_after_previous_failures_resolves_both_issue_types(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=70)
        connection_service._consecutive_failures[70] = 5

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh", new_callable=AsyncMock),
            patch("services.connection_service.issue_repo.resolve", return_value=False) as mock_resolve,
            patch("services.connection_service.ws_broadcast"),
        ):
            await connection_service.refresh_connection(conn)

        assert mock_resolve.call_count == 2
        resolved_types = {c.args[0] for c in mock_resolve.call_args_list}
        assert IssueType.CONNECTION_FAILED in resolved_types
        assert IssueType.TOKEN_INVALID in resolved_types
        assert 70 not in connection_service._consecutive_failures

    @pytest.mark.asyncio
    async def test_auth_error_broadcasts_issues_reload(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=80)
        connection_service._consecutive_failures.pop(80, None)

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh",
                  new_callable=AsyncMock, side_effect=Exception("Unauthorized")),
            patch("services.connection_service.issue_repo.upsert"),
            patch("services.connection_service.ws_broadcast") as mock_broadcast,
        ):
            await connection_service.refresh_connection(conn)

        mock_broadcast.assert_called_once_with("", reload="issues")

    @pytest.mark.asyncio
    async def test_connection_failed_broadcasts_issues_reload(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=81)
        connection_service._consecutive_failures[81] = 2  # next hit → threshold

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh",
                  new_callable=AsyncMock, side_effect=Exception("network error")),
            patch("services.connection_service.issue_repo.upsert"),
            patch("services.connection_service.ws_broadcast") as mock_broadcast,
        ):
            await connection_service.refresh_connection(conn)

        mock_broadcast.assert_called_once_with("", reload="issues")

    @pytest.mark.asyncio
    async def test_failure_below_threshold_does_not_broadcast(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=82)
        connection_service._consecutive_failures.pop(82, None)

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh",
                  new_callable=AsyncMock, side_effect=Exception("network error")),
            patch("services.connection_service.issue_repo.upsert"),
            patch("services.connection_service.ws_broadcast") as mock_broadcast,
        ):
            await connection_service.refresh_connection(conn)

        # 1 failure < threshold (3) → no upsert → no broadcast
        mock_broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_no_prior_issues_does_not_broadcast(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=83)
        connection_service._consecutive_failures.pop(83, None)

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh", new_callable=AsyncMock),
            patch("services.connection_service.issue_repo.resolve", return_value=False),
            patch("services.connection_service.ws_broadcast") as mock_broadcast,
        ):
            await connection_service.refresh_connection(conn)

        mock_broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_with_resolved_issue_broadcasts(self):
        conn = self._make_conn(ArrType.RADARR, conn_id=84)
        connection_service._consecutive_failures[84] = 3

        with (
            patch("integrations.arr.radarr.RadarrConnectionManager.refresh", new_callable=AsyncMock),
            patch("services.connection_service.issue_repo.resolve", return_value=True),
            patch("services.connection_service.ws_broadcast") as mock_broadcast,
        ):
            await connection_service.refresh_connection(conn)

        mock_broadcast.assert_called_once_with("", reload="issues")
