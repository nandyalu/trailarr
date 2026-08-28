from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.files.files_handler import FilesHandler
import core.base.connection_manager as connection_manager_module
from database.models.connection import (
    ArrType,
    ConnectionRead,
)
from database.models.media import MediaRead


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
async def test_refresh_deletes_trailers_not_enabled(monkeypatch, tmp_path):
    connection = ConnectionRead(
        id=1,
        name="Test Connection",
        arr_type=ArrType.RADARR,
        url="http://example.com",
        api_key="API_KEY",
        monitor_new_media=True,
        added_at=datetime.now(timezone.utc),
        path_mappings=[],
    )

    manager = DummyConnectionManager(
        connection=connection,
        arr_manager=DummyArrManager(),
        parse_media=lambda cid, data: data,  # type: ignore[arg-type]
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
        monitor=False,
        arr_monitored=False,
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
        monitor=False,
        arr_monitored=False,
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

    def fake_delete_except(
        connection_id: int, media_ids: list[int], *, _session=None
    ):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_delete_removed_media_trailers = Mock(return_value=None)

    fake_settings = SimpleNamespace(
        delete_trailer_media=False,
        delete_trailer_connection=False,
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
    monkeypatch.setattr(
        DummyConnectionManager,
        "delete_removed_media_trailers",
        fake_delete_removed_media_trailers,
        raising=False,
    )

    await manager.refresh()

    fake_delete_removed_media_trailers.assert_not_called()
    assert trailer_file.exists()
    assert delete_except_called_with.get("connection_id") == 1
    assert delete_except_called_with.get("media_ids") == [1]


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
        monitor_new_media=True,
        added_at=datetime.now(timezone.utc),
        path_mappings=[],
    )

    manager = DummyConnectionManager(
        connection=connection,
        arr_manager=DummyArrManager(),
        parse_media=lambda cid, data: data,  # type: ignore[arg-type]
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
        monitor=False,
        arr_monitored=False,
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
        monitor=False,
        arr_monitored=False,
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

    def fake_delete_except(
        connection_id: int, media_ids: list[int], *, _session=None
    ):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_media=False,
        delete_trailer_connection=True,
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


@pytest.mark.asyncio
async def test_refresh_deletes_trailers_for_media_removed_from_arr_media_exists(
    monkeypatch, tmp_path
):
    connection = ConnectionRead(
        id=1,
        name="Test Connection",
        arr_type=ArrType.RADARR,
        url="http://example.com",
        api_key="API_KEY",
        monitor_new_media=True,
        added_at=datetime.now(timezone.utc),
        path_mappings=[],
    )

    manager = DummyConnectionManager(
        connection=connection,
        arr_manager=DummyArrManager(),
        parse_media=lambda cid, data: data,  # type: ignore[arg-type]
        is_movie=True,
    )

    media_folder = tmp_path / "Deleted Movie"
    media_folder.mkdir()
    movie_file = media_folder / "Deleted Movie (2025) [WEBRip-1080p]-Group.mkv"
    movie_file.write_bytes(b"x")
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
        monitor=False,
        arr_monitored=False,
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
        monitor=False,
        arr_monitored=False,
        media_exists=False,
        media_filename=str(movie_file),
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

    def fake_delete_except(
        connection_id: int, media_ids: list[int], *, _session=None
    ):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_media=True,
        delete_trailer_connection=True,
    )

    def fake_fileshandler_check_media_exists(path: str) -> bool:
        return True

    monkeypatch.setattr(
        connection_manager_module, "app_settings", fake_settings, raising=False
    )
    monkeypatch.setattr(
        DummyConnectionManager, "_parse_data", fake_parse_data, raising=False
    )
    monkeypatch.setattr(
        connection_manager_module.FilesHandler,
        "check_media_exists",
        fake_fileshandler_check_media_exists,
        raising=False,
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

    assert movie_file.exists()
    assert trailer_file.exists()
    assert delete_except_called_with.get("connection_id") == 1
    assert delete_except_called_with.get("media_ids") == [1]


@pytest.mark.asyncio
async def test_refresh_deletes_trailers_for_media_removed_from_arr_media_deleted(
    monkeypatch, tmp_path
):
    connection = ConnectionRead(
        id=1,
        name="Test Connection",
        arr_type=ArrType.RADARR,
        url="http://example.com",
        api_key="API_KEY",
        monitor_new_media=True,
        added_at=datetime.now(timezone.utc),
        path_mappings=[],
    )

    manager = DummyConnectionManager(
        connection=connection,
        arr_manager=DummyArrManager(),
        parse_media=lambda cid, data: data,  # type: ignore[arg-type]
        is_movie=True,
    )

    media_folder = tmp_path / "Deleted Movie"
    media_folder.mkdir()
    movie_file = media_folder / "Deleted Movie (2025) [WEBRip-1080p]-Group.mkv"
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
        monitor=False,
        arr_monitored=False,
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
        monitor=False,
        arr_monitored=False,
        media_exists=False,
        media_filename=str(movie_file),
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

    def fake_delete_except(
        connection_id: int, media_ids: list[int], *, _session=None
    ):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_media=True,
        delete_trailer_connection=True,
    )

    def fake_fileshandler_check_media_exists(path: str) -> bool:
        return False

    monkeypatch.setattr(
        connection_manager_module, "app_settings", fake_settings, raising=False
    )
    monkeypatch.setattr(
        DummyConnectionManager, "_parse_data", fake_parse_data, raising=False
    )
    monkeypatch.setattr(
        connection_manager_module.FilesHandler,
        "check_media_exists",
        fake_fileshandler_check_media_exists,
        raising=False,
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


class TestCreateFolder:
    """FilesHandler.create_folder — used by the 'Create Missing Folders'
    setting (discussion #641)."""

    def test_creates_missing_folder_with_parents(self, tmp_path):
        target = tmp_path / "movies" / "Some Movie (2026)"
        assert FilesHandler.create_folder(str(target)) is True
        assert target.is_dir()

    def test_existing_folder_is_a_no_op(self, tmp_path):
        target = tmp_path / "already-there"
        target.mkdir()
        assert FilesHandler.create_folder(str(target)) is True
        assert target.is_dir()

    def test_empty_path_is_refused(self):
        assert FilesHandler.create_folder("") is False

    def test_never_creates_when_storage_is_unreachable(self, tmp_path):
        """A disconnected share looks like a missing folder; writing into
        it would hide the real media when it comes back."""
        from unittest.mock import patch

        target = tmp_path / "dead-mount" / "Some Movie (2026)"
        with patch(
            "services.files.files_handler.is_disk_available", return_value=False
        ):
            assert FilesHandler.create_folder(str(target)) is False
        assert not target.exists()

    def test_inherits_permissions_of_nearest_existing_parent(self, tmp_path):
        """Created folders must stay writable for the Trailarr user
        (the PUID/PGID class of problem)."""
        import os
        import stat

        parent = tmp_path / "library"
        parent.mkdir(mode=0o775)
        os.chmod(parent, 0o775)
        target = parent / "New Movie (2026)"

        assert FilesHandler.create_folder(str(target)) is True
        mode = stat.S_IMODE(os.stat(target).st_mode)
        assert mode & 0o700 == 0o700  # owner can read/write/traverse

    def test_failure_is_reported_not_raised(self, tmp_path):
        """A file where the folder should go: report False, never raise."""
        blocker = tmp_path / "blocker"
        blocker.write_text("not a folder")
        assert FilesHandler.create_folder(str(blocker / "child")) is False
