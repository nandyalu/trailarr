"""Comprehensive tests for services/arr_connection_manager.py."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.models.connection import ArrType, ConnectionRead, MonitorType, PathMappingCRU
from db.models.helpers import MediaReadDC
from services.arr_connection_manager import BaseConnectionManager


def _make_connection(
    conn_id: int = 1,
    monitor: MonitorType = MonitorType.MONITOR_MISSING,
    path_mappings: list | None = None,
) -> ConnectionRead:
    return ConnectionRead(
        id=conn_id,
        name="Test",
        arr_type=ArrType.RADARR,
        url="http://test",
        api_key="key",
        monitor=monitor,
        added_at=datetime.now(timezone.utc),
        path_mappings=path_mappings or [],
    )


class _DummyArr:
    async def get_system_status(self):
        return "ok"

    async def get_rootfolders(self):
        return ["/movies"]

    async def get_all_media(self):
        return []


class _DummyCM(BaseConnectionManager):
    pass


def _make_manager(
    monitor: MonitorType = MonitorType.MONITOR_MISSING,
    path_mappings: list | None = None,
    conn_id: int = 1,
) -> _DummyCM:
    conn = _make_connection(conn_id=conn_id, monitor=monitor, path_mappings=path_mappings)
    return _DummyCM(
        connection=conn,
        arr_manager=_DummyArr(),
        parse_media=lambda cid, data: data,
        is_movie=True,
    )


# ─── get_system_status ────────────────────────────────────────────────────────

class TestGetSystemStatus:
    @pytest.mark.asyncio
    async def test_returns_status_string(self):
        manager = _make_manager()
        result = await manager.get_system_status()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        manager = _make_manager()
        manager.arr_manager = MagicMock()
        manager.arr_manager.get_system_status = AsyncMock(side_effect=Exception("timeout"))
        result = await manager.get_system_status()
        assert result is None


# ─── get_rootfolders ─────────────────────────────────────────────────────────

class TestGetRootfolders:
    @pytest.mark.asyncio
    async def test_returns_rootfolders_without_mappings(self):
        manager = _make_manager()
        result = await manager.get_rootfolders()
        assert result == ["/movies"]

    @pytest.mark.asyncio
    async def test_applies_path_mappings_to_rootfolders(self):
        pm = PathMappingCRU(path_from="/remote/", path_to="/local/")
        manager = _make_manager(path_mappings=[pm])
        manager.arr_manager = MagicMock()
        manager.arr_manager.get_rootfolders = AsyncMock(return_value=["/remote/movies"])
        result = await manager.get_rootfolders()
        assert result == ["/local/movies"]

    @pytest.mark.asyncio
    async def test_exception_returns_empty_list(self):
        manager = _make_manager()
        manager.arr_manager = MagicMock()
        manager.arr_manager.get_rootfolders = AsyncMock(side_effect=Exception("timeout"))
        result = await manager.get_rootfolders()
        assert result == []


# ─── get_media_data ───────────────────────────────────────────────────────────

class TestGetMediaData:
    @pytest.mark.asyncio
    async def test_returns_data(self):
        manager = _make_manager()
        manager.arr_manager = MagicMock()
        manager.arr_manager.get_all_media = AsyncMock(return_value=[{"id": 1}])
        result = await manager.get_media_data()
        assert result == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_exception_returns_empty_list(self):
        manager = _make_manager()
        manager.arr_manager = MagicMock()
        manager.arr_manager.get_all_media = AsyncMock(side_effect=Exception("timeout"))
        result = await manager.get_media_data()
        assert result == []


# ─── _check_monitoring ────────────────────────────────────────────────────────

class TestCheckMonitoring:
    def test_monitor_none_always_false(self):
        m = _make_manager(monitor=MonitorType.MONITOR_NONE)
        assert m._check_monitoring(True, True) is False
        assert m._check_monitoring(False, False) is False

    def test_monitor_missing_always_true(self):
        m = _make_manager(monitor=MonitorType.MONITOR_MISSING)
        assert m._check_monitoring(True, False) is True
        assert m._check_monitoring(False, False) is True

    def test_monitor_new_follows_is_new_flag(self):
        m = _make_manager(monitor=MonitorType.MONITOR_NEW)
        assert m._check_monitoring(True, False) is True
        assert m._check_monitoring(False, True) is False

    def test_monitor_sync_follows_arr_monitored(self):
        m = _make_manager(monitor=MonitorType.MONITOR_SYNC)
        assert m._check_monitoring(False, True) is True
        assert m._check_monitoring(True, False) is False


# ─── _apply_path_mappings ─────────────────────────────────────────────────────

class TestApplyPathMappings:
    def test_no_mappings_leaves_paths_unchanged(self):
        m = _make_manager()
        media = MagicMock()
        media.folder_path = "/movies/Inception"
        m._apply_path_mappings([media])
        assert media.folder_path == "/movies/Inception"

    def test_with_mapping_transforms_folder_path(self):
        pm = PathMappingCRU(path_from="/remote/", path_to="/local/")
        m = _make_manager(path_mappings=[pm])
        media = MagicMock()
        media.folder_path = "/remote/movies/Inception"
        m._apply_path_mappings([media])
        assert media.folder_path == "/local/movies/Inception"

    def test_empty_folder_path_is_skipped(self):
        pm = PathMappingCRU(path_from="/remote/", path_to="/local/")
        m = _make_manager(path_mappings=[pm])
        media = MagicMock()
        media.folder_path = ""
        m._apply_path_mappings([media])
        assert media.folder_path == ""


# ─── _check_trailer ───────────────────────────────────────────────────────────

class TestCheckTrailer:
    @pytest.mark.asyncio
    async def test_delegates_to_fileshandler(self):
        m = _make_manager()
        with patch(
            "services.arr_connection_manager.FilesHandler.check_trailer_exists",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_check:
            result = await m._check_trailer("/media/path")
        mock_check.assert_called_once_with(path="/media/path", check_inline_file=True)
        assert result is True


# ─── create_or_update_bulk ───────────────────────────────────────────────────

def _mock_media_read(media_id: int = 1, monitor: bool = False, arr_monitored: bool = True):
    m = MagicMock()
    m.id = media_id
    m.model_dump.return_value = {
        "id": media_id,
        "folder_path": "/p",
        "arr_monitored": arr_monitored,
        "monitor": monitor,
    }
    return m


class TestCreateOrUpdateBulk:
    def test_fires_media_added_event_for_created_item(self):
        manager = _make_manager()
        mock_media = _mock_media_read(1)
        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, True, False, False, 0)]),
            patch("services.arr_connection_manager.event_service.track_media_added") as mock_event,
            patch("services.trailer_profile_service.create_rows_for_new_media"),
        ):
            manager.create_or_update_bulk([MagicMock()])
        mock_event.assert_called_once()
        assert manager.created_count == 1

    def test_fires_arr_linked_event(self):
        manager = _make_manager()
        mock_media = _mock_media_read(5)
        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, False, False, True, 0)]),
            patch("services.arr_connection_manager.event_service.track_arr_linked") as mock_event,
        ):
            manager.create_or_update_bulk([MagicMock()])
        mock_event.assert_called_once()

    def test_updated_only_fires_no_event(self):
        manager = _make_manager()
        mock_media = _mock_media_read(2)
        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(mock_media, False, True, False, 0)]),
            patch("services.arr_connection_manager.event_service.track_media_added") as mock_added,
            patch("services.arr_connection_manager.event_service.track_arr_linked") as mock_linked,
        ):
            manager.create_or_update_bulk([MagicMock()])
        mock_added.assert_not_called()
        mock_linked.assert_not_called()
        assert manager.updated_count == 1

    def test_accumulates_media_ids(self):
        manager = _make_manager()
        m1, m2 = _mock_media_read(10), _mock_media_read(20)
        with (
            patch("services.arr_connection_manager.media_repo.create_or_update_bulk",
                  return_value=[(m1, True, False, False, 0), (m2, False, True, False, 0)]),
            patch("services.arr_connection_manager.event_service.track_media_added"),
            patch("services.trailer_profile_service.create_rows_for_new_media"),
        ):
            manager.create_or_update_bulk([MagicMock(), MagicMock()])
        assert manager.media_ids == [10, 20]


# ─── delete_trailers_for_media ───────────────────────────────────────────────

class TestDeleteTrailersForMedia:
    @pytest.mark.asyncio
    async def test_no_folder_path_returns_false(self):
        manager = _make_manager()
        media = MagicMock()
        media.folder_path = None
        media.downloads = []
        with patch("services.arr_connection_manager.app_settings") as s:
            s.delete_trailer_media = False
            result = await manager.delete_trailers_for_media(media)
        assert result is False

    @pytest.mark.asyncio
    async def test_guard_skips_when_media_still_on_disk(self):
        manager = _make_manager()
        media = MagicMock()
        media.folder_path = "/movies/kept"
        media.downloads = []
        with (
            patch("services.arr_connection_manager.app_settings") as s,
            patch("services.arr_connection_manager.FilesHandler.check_media_exists", return_value=True),
            patch("services.arr_connection_manager.FilesHandler.delete_trailers_for_media",
                  new_callable=AsyncMock) as mock_del,
        ):
            s.delete_trailer_media = True
            result = await manager.delete_trailers_for_media(media)
        assert result is False
        mock_del.assert_not_called()

    @pytest.mark.asyncio
    async def test_deletes_tracked_download_file(self):
        manager = _make_manager()
        dl = MagicMock()
        dl.file_exists = True
        dl.path = "/movies/film/trailer.mkv"
        media = MagicMock()
        media.folder_path = "/movies/film"
        media.downloads = [dl]
        with (
            patch("services.arr_connection_manager.app_settings") as s,
            patch("services.arr_connection_manager.FilesHandler.delete_file",
                  new_callable=AsyncMock, return_value=True) as mock_del_file,
            patch("services.arr_connection_manager.FilesHandler.delete_trailers_for_media",
                  new_callable=AsyncMock, return_value=False),
        ):
            s.delete_trailer_media = False
            result = await manager.delete_trailers_for_media(media)
        mock_del_file.assert_called_once_with(dl.path)
        assert result is True

    @pytest.mark.asyncio
    async def test_skips_download_without_path(self):
        manager = _make_manager()
        dl = MagicMock()
        dl.file_exists = True
        dl.path = None
        media = MagicMock()
        media.folder_path = "/movies/film"
        media.downloads = [dl]
        with (
            patch("services.arr_connection_manager.app_settings") as s,
            patch("services.arr_connection_manager.FilesHandler.delete_file",
                  new_callable=AsyncMock) as mock_del_file,
            patch("services.arr_connection_manager.FilesHandler.delete_trailers_for_media",
                  new_callable=AsyncMock, return_value=False),
        ):
            s.delete_trailer_media = False
            await manager.delete_trailers_for_media(media)
        mock_del_file.assert_not_called()


# ─── delete_removed_media_trailers ───────────────────────────────────────────

class TestDeleteRemovedMediaTrailers:
    @pytest.mark.asyncio
    async def test_empty_media_ids_is_noop(self):
        manager = _make_manager()
        manager.media_ids = []
        with patch("services.arr_connection_manager.media_repo.read_all_by_connection") as mock_read:
            await manager.delete_removed_media_trailers()
        mock_read.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_delete_only_for_removed_media(self):
        manager = _make_manager()
        manager.media_ids = [1]

        kept = MagicMock()
        kept.id = 1
        removed = MagicMock()
        removed.id = 99

        delete_calls: list[int] = []

        async def fake_delete(media):
            delete_calls.append(media.id)

        manager.delete_trailers_for_media = fake_delete

        with patch("services.arr_connection_manager.media_repo.read_all_by_connection",
                   return_value=[kept, removed]):
            await manager.delete_removed_media_trailers()

        assert delete_calls == [99]


# ─── remove_media_deleted_in_arr_from_db ─────────────────────────────────────

class TestRemoveMediaDeletedInArrFromDb:
    def test_empty_media_ids_is_noop(self):
        manager = _make_manager()
        manager.media_ids = []
        with patch("services.arr_connection_manager.media_repo.demote_arr_items_with_plex_to_plex_only") as m:
            manager.remove_media_deleted_in_arr_from_db()
        m.assert_not_called()

    def test_fires_arr_unlinked_for_each_demoted_id(self):
        manager = _make_manager()
        manager.media_ids = [1, 2, 3]
        with (
            patch("services.arr_connection_manager.media_repo.demote_arr_items_with_plex_to_plex_only",
                  return_value=[55, 66]),
            patch("services.arr_connection_manager.media_repo.delete_except"),
            patch("services.arr_connection_manager.event_service.track_arr_unlinked") as mock_event,
        ):
            manager.remove_media_deleted_in_arr_from_db()
        assert mock_event.call_count == 2
        unlinked_ids = {c.kwargs["media_id"] for c in mock_event.call_args_list}
        assert unlinked_ids == {55, 66}

    def test_calls_delete_except_with_current_ids(self):
        manager = _make_manager()
        manager.media_ids = [1, 2]
        with (
            patch("services.arr_connection_manager.media_repo.demote_arr_items_with_plex_to_plex_only",
                  return_value=[]),
            patch("services.arr_connection_manager.media_repo.delete_except") as mock_del,
            patch("services.arr_connection_manager.event_service.track_arr_unlinked"),
        ):
            manager.remove_media_deleted_in_arr_from_db()
        mock_del.assert_called_once_with(manager.connection_id, [1, 2])


# ─── _process_media_list ─────────────────────────────────────────────────────

class TestProcessMediaList:
    @pytest.mark.asyncio
    async def test_empty_list_is_noop(self):
        manager = _make_manager()
        with patch("services.arr_connection_manager.media_repo.update_monitor_and_trailer_exists_bulk") as mock_upd:
            await manager._process_media_list([])
        mock_upd.assert_not_called()

    @pytest.mark.asyncio
    async def test_fires_monitor_changed_event_when_monitor_flips(self):
        # MONITOR_MISSING → always True; media has monitor=False → event fires
        manager = _make_manager(monitor=MonitorType.MONITOR_MISSING)
        dc = MediaReadDC(id=1, created=True, folder_path="/p", arr_monitored=True, monitor=False)
        with (
            patch.object(manager, "create_or_update_bulk", return_value=[dc]),
            patch("services.arr_connection_manager.media_repo.update_monitor_and_trailer_exists_bulk"),
            patch("services.arr_connection_manager.event_service.track_monitor_changed") as mock_event,
        ):
            await manager._process_media_list([MagicMock()])
        mock_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_event_when_monitor_unchanged(self):
        # MONITOR_MISSING → True; media already has monitor=True → no event
        manager = _make_manager(monitor=MonitorType.MONITOR_MISSING)
        dc = MediaReadDC(id=1, created=True, folder_path="/p", arr_monitored=True, monitor=True)
        with (
            patch.object(manager, "create_or_update_bulk", return_value=[dc]),
            patch("services.arr_connection_manager.media_repo.update_monitor_and_trailer_exists_bulk"),
            patch("services.arr_connection_manager.event_service.track_monitor_changed") as mock_event,
        ):
            await manager._process_media_list([MagicMock()])
        mock_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_update_bulk_with_correct_ids(self):
        manager = _make_manager(monitor=MonitorType.MONITOR_MISSING)
        dc = MediaReadDC(id=7, created=True, folder_path="/p", arr_monitored=True, monitor=False)
        with (
            patch.object(manager, "create_or_update_bulk", return_value=[dc]),
            patch("services.arr_connection_manager.media_repo.update_monitor_and_trailer_exists_bulk") as mock_upd,
            patch("services.arr_connection_manager.event_service.track_monitor_changed"),
        ):
            await manager._process_media_list([MagicMock()])
        mock_upd.assert_called_once()
        update_list = mock_upd.call_args[0][0]
        assert update_list[0][0] == 7


# ─── refresh ─────────────────────────────────────────────────────────────────

class TestRefresh:
    @pytest.mark.asyncio
    async def test_processes_each_chunk_from_parse_data(self):
        manager = _make_manager()
        chunks = [[MagicMock()], [MagicMock()]]
        processed: list = []

        async def fake_parse():
            for c in chunks:
                yield c

        async def fake_process(chunk):
            processed.append(chunk)

        with patch("services.arr_connection_manager.app_settings") as s:
            s.delete_trailer_connection = False
            manager._parse_data = fake_parse
            manager._process_media_list = fake_process
            manager.remove_media_deleted_in_arr_from_db = MagicMock()
            await manager.refresh()

        assert len(processed) == 2

    @pytest.mark.asyncio
    async def test_delete_trailers_called_when_enabled(self):
        manager = _make_manager()
        manager.media_ids = [1]

        async def fake_parse():
            yield []

        async def fake_process(chunk):
            pass

        with (
            patch("services.arr_connection_manager.app_settings") as s,
            patch.object(manager, "delete_removed_media_trailers", new_callable=AsyncMock) as mock_del,
        ):
            s.delete_trailer_connection = True
            manager._parse_data = fake_parse
            manager._process_media_list = fake_process
            manager.remove_media_deleted_in_arr_from_db = MagicMock()
            await manager.refresh()

        mock_del.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_trailers_not_called_when_disabled(self):
        manager = _make_manager()

        async def fake_parse():
            yield []

        async def fake_process(chunk):
            pass

        with (
            patch("services.arr_connection_manager.app_settings") as s,
            patch.object(manager, "delete_removed_media_trailers", new_callable=AsyncMock) as mock_del,
        ):
            s.delete_trailer_connection = False
            manager._parse_data = fake_parse
            manager._process_media_list = fake_process
            manager.remove_media_deleted_in_arr_from_db = MagicMock()
            await manager.refresh()

        mock_del.assert_not_called()

    @pytest.mark.asyncio
    async def test_always_calls_remove_media_deleted_in_arr(self):
        manager = _make_manager()

        async def fake_parse():
            yield []

        async def fake_process(chunk):
            pass

        with patch("services.arr_connection_manager.app_settings") as s:
            s.delete_trailer_connection = False
            manager._parse_data = fake_parse
            manager._process_media_list = fake_process
            remove_mock = MagicMock()
            manager.remove_media_deleted_in_arr_from_db = remove_mock
            await manager.refresh()

        remove_mock.assert_called_once()
