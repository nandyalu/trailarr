from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.files_handler import FilesHandler
import core.base.connection_manager as connection_manager_module
from core.base.database.models.connection import (
    ArrType,
    ConnectionRead,
    MonitorType,
)
from core.base.database.models.helpers import MediaReadDC
from core.base.database.models.media import MediaRead, MonitorStatus


@pytest.mark.asyncio
async def test_delete_trailers_for_media_inline_and_folder(tmp_path):
    media_dir = tmp_path / "Test Movie (2025)"
    media_dir.mkdir()

    inline_trailer = media_dir / "Test Movie (2025)-trailer.mkv"
    inline_trailer.write_bytes(b"x")

    trailers_dir = media_dir / "Trailers"
    trailers_dir.mkdir()
    (trailers_dir / "Test Movie (2025)-trailer.mkv").write_bytes(b"x")

    deleted = await FilesHandler.delete_trailers_for_media(str(media_dir))

    assert deleted is True
    assert not inline_trailer.exists()
    assert not trailers_dir.exists()


@pytest.mark.asyncio
async def test_delete_trailers_for_media_movie_inline_only(tmp_path):
    """Movie-style folder:
    /movies/Movie (2025)/Movie (2025)-trailer.mkv and main file."""
    media_dir = tmp_path / "Sample Movie (2025)"
    media_dir.mkdir()

    main_file = media_dir / "Sample Movie (2025) [WEBRip-1080p]-Group.mkv"
    main_file.write_bytes(b"x")
    trailer_file = media_dir / "Sample Movie (2025)-trailer.mkv"
    trailer_file.write_bytes(b"x")

    deleted = await FilesHandler.delete_trailers_for_media(str(media_dir))

    assert deleted is True
    assert main_file.exists()
    assert not trailer_file.exists()


@pytest.mark.asyncio
async def test_delete_trailers_for_media_tv_structure(tmp_path):
    """TV-style structure:
    /tv/Show/Trailers/Show (2024)-trailer.mkv
    /tv/Show/Season 1/Show - S01E01 - Episode.mkv"""
    show_dir = tmp_path / "Sample Show"
    show_dir.mkdir()

    trailers_dir = show_dir / "Trailers"
    trailers_dir.mkdir()
    trailer_file = trailers_dir / "Sample Show (2024)-trailer.mkv"
    trailer_file.write_bytes(b"x")

    season_dir = show_dir / "Season 1"
    season_dir.mkdir()
    episode_file = (
        season_dir / "Sample Show - S01E01 - Episode 1 [WEBDL-1080p]-Group.mkv"
    )
    episode_file.write_bytes(b"x")

    deleted = await FilesHandler.delete_trailers_for_media(str(show_dir))

    assert deleted is True
    assert not trailers_dir.exists()
    assert not trailer_file.exists()
    # Ensure episode and season folder are untouched
    assert season_dir.exists()
    assert episode_file.exists()


@pytest.mark.asyncio
async def test_delete_trailers_for_media_nothing_to_delete(tmp_path):
    media_dir = tmp_path / "Empty Movie"
    media_dir.mkdir()

    deleted = await FilesHandler.delete_trailers_for_media(str(media_dir))

    assert deleted is False
    assert media_dir.exists()


class DummyArrManager:
    async def get_system_status(self):
        return "ok"

    async def get_rootfolders(self):
        return []

    async def get_all_media(self):
        return []


class DummyConnectionManager(connection_manager_module.BaseConnectionManager):
    pass


@pytest.mark.asyncio
async def test_process_media_list_deletes_trailer_when_media_missing(monkeypatch):
    connection = ConnectionRead(
        id=1,
        name="Test Connection",
        arr_type=ArrType.RADARR,
        url="http://example.com",
        api_key="API_KEY",
        monitor=MonitorType.MONITOR_MISSING,
        added_at=datetime.now(timezone.utc),
        path_mappings=[],
    )

    manager = DummyConnectionManager(
        connection=connection,
        arr_manager=DummyArrManager(),
        parse_media=lambda cid, data: data,
        is_movie=True,
    )

    media_dc = MediaReadDC(
        id=1,
        created=False,
        folder_path="/some/folder",
        arr_monitored=True,
        monitor=False,
        status=MonitorStatus.MONITORED,
        trailer_exists=True,
        media_exists=False,
    )

    async def fake_delete_trailers_for_media(path: str) -> bool:
        fake_delete_trailers_for_media.called_with = path  # type: ignore[attr-defined]
        return True

    fake_delete_trailers_for_media.called_with = None  # type: ignore[attr-defined]

    def fake_create_or_update_bulk(media_data):
        return [media_dc]

    updates: list[MediaReadDC] = []

    def fake_update_media_status_bulk(update_list):
        updates.extend(update_list)

    fake_settings = SimpleNamespace(
        delete_trailer_after_all_media_deleted=True,
    )

    monkeypatch.setattr(
        connection_manager_module, "app_settings", fake_settings, raising=False
    )
    monkeypatch.setattr(
        manager,
        "create_or_update_bulk",
        fake_create_or_update_bulk,
        raising=False,
    )
    monkeypatch.setattr(
        manager,
        "update_media_status_bulk",
        fake_update_media_status_bulk,
        raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.FilesHandler,
        "delete_trailers_for_media",
        fake_delete_trailers_for_media,
        raising=False,
    )

    await manager._process_media_list([SimpleNamespace(folder_path="/some/folder")])

    assert fake_delete_trailers_for_media.called_with == "/some/folder"
    assert len(updates) == 1
    assert updates[0].id == 1
    assert updates[0].trailer_exists is False


@pytest.mark.asyncio
async def test_refresh_deletes_trailers_for_media_removed_from_arr(
    monkeypatch, tmp_path
):
    connection = ConnectionRead(
        id=1,
        name="Test Connection",
        arr_type=ArrType.RADARR,
        url="http://example.com",
        api_key="API_KEY",
        monitor=MonitorType.MONITOR_MISSING,
        added_at=datetime.now(timezone.utc),
        path_mappings=[],
    )

    manager = DummyConnectionManager(
        connection=connection,
        arr_manager=DummyArrManager(),
        parse_media=lambda cid, data: data,
        is_movie=True,
    )

    media_folder = tmp_path / "Deleted Movie"
    media_folder.mkdir()
    trailer_file = media_folder / "Deleted Movie (2025)-trailer.mkv"
    trailer_file.write_bytes(b"x")

    manager.media_ids = [1]

    media_kept = MediaRead(
        id=1,
        connection_id=1,
        arr_id=1,
        is_movie=True,
        title="Kept",
        clean_title="kept",
        year=2025,
        language="en",
        studio="Studio",
        txdb_id="tx1",
        title_slug="kept",
        trailer_exists=False,
        monitor=False,
        arr_monitored=False,
        status=MonitorStatus.MONITORED,
        media_exists=True,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        downloaded_at=None,
        folder_path=str(tmp_path / "Kept Movie"),
        overview=None,
        poster_url=None,
        fanart_url=None,
        poster_path=None,
        fanart_path=None,
        youtube_trailer_id=None,
        imdb_id=None,
    )

    media_deleted = MediaRead(
        id=2,
        connection_id=1,
        arr_id=2,
        is_movie=True,
        title="Deleted",
        clean_title="deleted",
        year=2025,
        language="en",
        studio="Studio",
        txdb_id="tx2",
        title_slug="deleted",
        trailer_exists=True,
        monitor=False,
        arr_monitored=False,
        status=MonitorStatus.MONITORED,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        downloaded_at=None,
        folder_path=str(media_folder),
        overview=None,
        poster_url=None,
        fanart_url=None,
        poster_path=None,
        fanart_path=None,
        youtube_trailer_id=None,
        imdb_id=None,
    )

    async def fake_parse_data(self):
        yield []

    def fake_read_all_by_connection(connection_id: int):
        return [media_kept, media_deleted]

    delete_except_called_with = {}

    def fake_delete_except(connection_id: int, media_ids: list[int], *, _session=None):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_after_all_media_deleted=True,
    )

    monkeypatch.setattr(
        connection_manager_module, "app_settings", fake_settings, raising=False
    )
    monkeypatch.setattr(
        DummyConnectionManager, "_parse_data", fake_parse_data, raising=False
    )
    monkeypatch.setattr(
        connection_manager_module.media_manager,
        "read_all_by_connection",
        fake_read_all_by_connection,
        raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_manager,
        "delete_except",
        fake_delete_except,
        raising=False,
    )

    await manager.refresh()

    assert not trailer_file.exists()
    assert delete_except_called_with.get("connection_id") == 1
    assert delete_except_called_with.get("media_ids") == [1]
