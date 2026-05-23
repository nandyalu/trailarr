from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from services.files_service import FilesHandler, FolderInfo
import services.arr_connection_manager as connection_manager_module
from db.models.connection import (
    ArrType,
    ConnectionRead,
    MonitorType,
)
from db.models.media import MediaRead


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
    show_dir = tmp_path / "Sample Show"
    show_dir.mkdir()

    trailers_dir = show_dir / "Trailers"
    trailers_dir.mkdir()
    trailer_file = trailers_dir / "Sample Show (2024)-trailer.mkv"
    trailer_file.write_bytes(b"x")

    season_dir = show_dir / "Season 1"
    season_dir.mkdir()
    episode_file = season_dir / "Sample Show - S01E01 - Episode 1 [WEBDL-1080p]-Group.mkv"
    episode_file.write_bytes(b"x")

    deleted = await FilesHandler.delete_trailers_for_media(str(show_dir))

    assert deleted is True
    assert not trailers_dir.exists()
    assert not trailer_file.exists()
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
        monitor=MonitorType.MONITOR_MISSING,
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

    def fake_delete_except(connection_id: int, media_ids: list[int], *, _session=None):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_delete_removed_media_trailers = Mock(return_value=None)

    fake_settings = SimpleNamespace(
        delete_trailer_media=False,
        delete_trailer_connection=False,
    )

    monkeypatch.setattr(connection_manager_module, "app_settings", fake_settings, raising=False)
    monkeypatch.setattr(DummyConnectionManager, "_parse_data", fake_parse_data, raising=False)
    monkeypatch.setattr(
        connection_manager_module.media_repo, "read_all_by_connection",
        fake_read_all_by_connection, raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_repo, "delete_except",
        fake_delete_except, raising=False,
    )
    monkeypatch.setattr(
        DummyConnectionManager, "delete_removed_media_trailers",
        fake_delete_removed_media_trailers, raising=False,
    )

    await manager.refresh()

    fake_delete_removed_media_trailers.assert_not_called()
    assert trailer_file.exists()
    assert delete_except_called_with.get("connection_id") == 1
    assert delete_except_called_with.get("media_ids") == [1]


@pytest.mark.asyncio
async def test_refresh_deletes_trailers_for_media_removed_from_arr(monkeypatch, tmp_path):
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

    def fake_delete_except(connection_id: int, media_ids: list[int], *, _session=None):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_media=False,
        delete_trailer_connection=True,
    )

    monkeypatch.setattr(connection_manager_module, "app_settings", fake_settings, raising=False)
    monkeypatch.setattr(DummyConnectionManager, "_parse_data", fake_parse_data, raising=False)
    monkeypatch.setattr(
        connection_manager_module.media_repo, "read_all_by_connection",
        fake_read_all_by_connection, raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_repo, "delete_except",
        fake_delete_except, raising=False,
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
        monitor=MonitorType.MONITOR_MISSING,
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

    def fake_delete_except(connection_id: int, media_ids: list[int], *, _session=None):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_media=True,
        delete_trailer_connection=True,
    )

    def fake_fileshandler_check_media_exists(path: str) -> bool:
        return True

    monkeypatch.setattr(connection_manager_module, "app_settings", fake_settings, raising=False)
    monkeypatch.setattr(DummyConnectionManager, "_parse_data", fake_parse_data, raising=False)
    monkeypatch.setattr(
        connection_manager_module.FilesHandler,
        "check_media_exists",
        fake_fileshandler_check_media_exists,
        raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_repo, "read_all_by_connection",
        fake_read_all_by_connection, raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_repo, "delete_except",
        fake_delete_except, raising=False,
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
        monitor=MonitorType.MONITOR_MISSING,
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

    def fake_delete_except(connection_id: int, media_ids: list[int], *, _session=None):
        delete_except_called_with["connection_id"] = connection_id
        delete_except_called_with["media_ids"] = media_ids

    fake_settings = SimpleNamespace(
        delete_trailer_media=True,
        delete_trailer_connection=True,
    )

    def fake_fileshandler_check_media_exists(path: str) -> bool:
        return False

    monkeypatch.setattr(connection_manager_module, "app_settings", fake_settings, raising=False)
    monkeypatch.setattr(DummyConnectionManager, "_parse_data", fake_parse_data, raising=False)
    monkeypatch.setattr(
        connection_manager_module.FilesHandler,
        "check_media_exists",
        fake_fileshandler_check_media_exists,
        raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_repo, "read_all_by_connection",
        fake_read_all_by_connection, raising=False,
    )
    monkeypatch.setattr(
        connection_manager_module.media_repo, "delete_except",
        fake_delete_except, raising=False,
    )

    await manager.refresh()

    assert not trailer_file.exists()
    assert delete_except_called_with.get("connection_id") == 1
    assert delete_except_called_with.get("media_ids") == [1]


# ─── FilesHandler unit tests ──────────────────────────────────────────────────

class TestConvertFileSize:
    def test_bytes(self):
        assert FilesHandler._convert_file_size(512) == "512.00 B"

    def test_kilobytes(self):
        assert FilesHandler._convert_file_size(1024) == "1.00 KB"

    def test_megabytes(self):
        assert FilesHandler._convert_file_size(1024 * 1024) == "1.00 MB"

    def test_gigabytes(self):
        assert FilesHandler._convert_file_size(1024 ** 3) == "1.00 GB"

    def test_zero(self):
        assert FilesHandler._convert_file_size(0) == "0.00 B"


class TestFolderInfoLt:
    def test_same_type_sorts_alphabetically(self):
        a = FolderInfo(name="Apple", path="/a", created="")
        b = FolderInfo(name="Banana", path="/b", created="")
        assert a < b
        assert not (b < a)

    def test_folder_sorts_before_file(self):
        f = FolderInfo(type="file", name="a_file.mkv", path="/a", created="")
        d = FolderInfo(type="folder", name="z_folder", path="/z", created="")
        assert d < f

    def test_symlink_and_folder_have_equal_order(self):
        # both map to type_value 1 — neither is considered less than the other
        sym = FolderInfo(type="symlink", name="aaa", path="/a", created="")
        fol = FolderInfo(type="folder", name="bbb", path="/b", created="")
        assert not (sym < fol)
        assert not (fol < sym)

    def test_unknown_type_falls_back_to_name(self):
        a = FolderInfo(type="other", name="aaa", path="/a", created="")
        b = FolderInfo(type="other", name="bbb", path="/b", created="")
        assert a < b


class TestIsVideoFile:
    def test_mkv(self):
        assert FilesHandler.is_video_file("movie.mkv") is True

    def test_mp4(self):
        assert FilesHandler.is_video_file("clip.mp4") is True

    def test_avi(self):
        assert FilesHandler.is_video_file("old.avi") is True

    def test_webm(self):
        assert FilesHandler.is_video_file("web.webm") is True

    def test_jpg_not_video(self):
        assert FilesHandler.is_video_file("cover.jpg") is False

    def test_empty_string(self):
        assert FilesHandler.is_video_file("") is False

    def test_case_insensitive(self):
        assert FilesHandler.is_video_file("MOVIE.MKV") is True


class TestIsTrailerFile:
    def test_non_video_returns_false(self):
        assert FilesHandler.is_trailer_file("trailer.jpg") is False

    def test_video_without_trailer_keyword(self):
        assert FilesHandler.is_trailer_file("movie.mkv") is False

    def test_season_episode_pattern_excluded(self):
        assert FilesHandler.is_trailer_file("Show S01E01-trailer.mkv") is False

    def test_trailer_in_name_returns_true(self):
        assert FilesHandler.is_trailer_file("Movie-trailer.mkv") is True

    def test_trailer_case_insensitive(self):
        assert FilesHandler.is_trailer_file("Movie-TRAILER.mkv") is True

    def test_trailer_over_size_limit_returns_false(self):
        too_big = FilesHandler.TRAILER_MAX_SIZE_BYTES + 1
        assert FilesHandler.is_trailer_file("Movie-trailer.mkv", too_big) is False

    def test_trailer_under_size_limit_returns_true(self):
        small = 10 * 1024 * 1024
        assert FilesHandler.is_trailer_file("Movie-trailer.mkv", small) is True

    def test_no_size_arg_returns_true(self):
        assert FilesHandler.is_trailer_file("Movie-trailer.mkv", None) is True


class TestCheckFolderExists:
    def test_existing_dir(self, tmp_path):
        assert FilesHandler.check_folder_exists(str(tmp_path)) is True

    def test_nonexistent_path(self, tmp_path):
        assert FilesHandler.check_folder_exists(str(tmp_path / "nope")) is False

    def test_file_not_folder(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        assert FilesHandler.check_folder_exists(str(f)) is False


class TestCheckMediaExists:
    def test_nonexistent_path(self, tmp_path):
        assert FilesHandler.check_media_exists(str(tmp_path / "missing")) is False

    def test_non_video_file_returns_false(self, tmp_path):
        (tmp_path / "cover.jpg").write_bytes(b"x")
        assert FilesHandler.check_media_exists(str(tmp_path)) is False

    def test_video_over_threshold_returns_true(self):
        entry = MagicMock()
        entry.is_dir.return_value = False
        entry.is_file.return_value = True
        entry.name = "movie.mkv"
        entry.stat.return_value = MagicMock(st_size=200 * 1024 * 1024)
        with (
            patch("services.files_service.os.path.isdir", return_value=True),
            patch("services.files_service.os.scandir", return_value=[entry]),
        ):
            assert FilesHandler.check_media_exists("/fake/path") is True

    def test_video_under_threshold_returns_false(self):
        entry = MagicMock()
        entry.is_dir.return_value = False
        entry.is_file.return_value = True
        entry.name = "movie.mkv"
        entry.stat.return_value = MagicMock(st_size=50 * 1024 * 1024)
        with (
            patch("services.files_service.os.path.isdir", return_value=True),
            patch("services.files_service.os.scandir", return_value=[entry]),
        ):
            assert FilesHandler.check_media_exists("/fake/path") is False


class TestGetTrailerFolders:
    def test_always_includes_trailer_and_trailers(self):
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value=set()):
            folders = FilesHandler.get_trailer_folders()
        assert "trailer" in folders
        assert "trailers" in folders

    def test_includes_custom_folders_lowercased(self):
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value={"Extras", " Featurettes "}):
            folders = FilesHandler.get_trailer_folders()
        assert "extras" in folders
        assert "featurettes" in folders


class TestIsTrailerFolder:
    def test_matching_default_name(self):
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value=set()):
            assert FilesHandler.is_trailer_folder("Trailers") is True

    def test_non_matching_name(self):
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value=set()):
            assert FilesHandler.is_trailer_folder("Season 1") is False

    def test_empty_string(self):
        assert FilesHandler.is_trailer_folder("") is False


class TestCheckTrailerExists:
    @pytest.mark.asyncio
    async def test_nonexistent_dir_returns_false(self, tmp_path):
        result = await FilesHandler.check_trailer_exists(str(tmp_path / "nope"))
        assert result is False

    @pytest.mark.asyncio
    async def test_finds_trailer_in_subfolder(self, tmp_path):
        media_dir = tmp_path / "Movie"
        media_dir.mkdir()
        trailers_dir = media_dir / "Trailers"
        trailers_dir.mkdir()
        (trailers_dir / "Movie-trailer.mkv").write_bytes(b"x")
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value=set()):
            result = await FilesHandler.check_trailer_exists(str(media_dir))
        assert result is True

    @pytest.mark.asyncio
    async def test_inline_trailer_found_with_flag(self, tmp_path):
        media_dir = tmp_path / "Movie"
        media_dir.mkdir()
        (media_dir / "Movie-trailer.mkv").write_bytes(b"x")
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value=set()):
            result = await FilesHandler.check_trailer_exists(str(media_dir), check_inline_file=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_inline_trailer_not_found_without_flag(self, tmp_path):
        media_dir = tmp_path / "Movie"
        media_dir.mkdir()
        (media_dir / "Movie-trailer.mkv").write_bytes(b"x")
        with patch("db.repos.trailer_profile.get_trailer_folders", return_value=set()):
            result = await FilesHandler.check_trailer_exists(str(media_dir), check_inline_file=False)
        assert result is False


class TestDeleteFile:
    @pytest.mark.asyncio
    async def test_too_few_path_segments_returns_false(self):
        result = await FilesHandler.delete_file("/a/b.mkv")
        assert result is False

    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        f = tmp_path / "a" / "b" / "trailer.mkv"
        f.parent.mkdir(parents=True)
        f.write_bytes(b"x")
        result = await FilesHandler.delete_file(str(f))
        assert result is True
        assert not f.exists()

    @pytest.mark.asyncio
    async def test_file_not_found_returns_false(self, tmp_path):
        result = await FilesHandler.delete_file(str(tmp_path / "a" / "b" / "c.mkv"))
        assert result is False

    @pytest.mark.asyncio
    async def test_generic_exception_returns_false(self):
        with patch("services.files_service.aiofiles.os.remove", new_callable=AsyncMock, side_effect=OSError("io")):
            result = await FilesHandler.delete_file("/a/b/c/file.mkv")
        assert result is False


class TestDeleteFolder:
    @pytest.mark.asyncio
    async def test_empty_path_returns_false(self):
        assert await FilesHandler.delete_folder("") is False

    @pytest.mark.asyncio
    async def test_root_path_returns_false(self):
        assert await FilesHandler.delete_folder("/") is False

    @pytest.mark.asyncio
    async def test_too_few_segments_returns_false(self):
        assert await FilesHandler.delete_folder("/a/b") is False

    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        folder = tmp_path / "a" / "b" / "Trailers"
        folder.mkdir(parents=True)
        result = await FilesHandler.delete_folder(str(folder))
        assert result is True
        assert not folder.exists()

    @pytest.mark.asyncio
    async def test_folder_not_found_returns_false(self, tmp_path):
        result = await FilesHandler.delete_folder(str(tmp_path / "a" / "b" / "missing"))
        assert result is False

    @pytest.mark.asyncio
    async def test_generic_exception_returns_false(self):
        with patch("services.files_service.shutil.rmtree", side_effect=OSError("busy")):
            result = await FilesHandler.delete_folder("/a/b/c/d")
        assert result is False


class TestDeleteFileFol:
    @pytest.mark.asyncio
    async def test_directory_is_deleted(self, tmp_path):
        folder = tmp_path / "a" / "b" / "c"
        folder.mkdir(parents=True)
        result = await FilesHandler.delete_file_fol(str(folder))
        assert result is True
        assert not folder.exists()

    @pytest.mark.asyncio
    async def test_file_is_deleted(self, tmp_path):
        f = tmp_path / "a" / "b" / "file.mkv"
        f.parent.mkdir(parents=True)
        f.write_bytes(b"x")
        result = await FilesHandler.delete_file_fol(str(f))
        assert result is True
        assert not f.exists()


class TestRenameFileFol:
    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        src = tmp_path / "old.txt"
        dst = tmp_path / "new.txt"
        src.write_bytes(b"content")
        result = await FilesHandler.rename_file_fol(str(src), str(dst))
        assert result is True
        assert dst.exists()
        assert not src.exists()

    @pytest.mark.asyncio
    async def test_not_found_returns_false(self, tmp_path):
        result = await FilesHandler.rename_file_fol(
            str(tmp_path / "missing.txt"), str(tmp_path / "new.txt")
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_generic_exception_returns_false(self):
        with patch("services.files_service.aiofiles.os.rename", new_callable=AsyncMock, side_effect=OSError("busy")):
            result = await FilesHandler.rename_file_fol("/a/old.txt", "/a/new.txt")
        assert result is False


class TestComputeFileHash:
    def test_returns_sha256_hex(self, tmp_path):
        import hashlib
        content = b"hello world"
        f = tmp_path / "data.bin"
        f.write_bytes(content)
        assert FilesHandler.compute_file_hash(str(f)) == hashlib.sha256(content).hexdigest()

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            FilesHandler.compute_file_hash(str(tmp_path / "missing.bin"))

    def test_no_read_permission_raises(self, tmp_path):
        f = tmp_path / "locked.bin"
        f.write_bytes(b"x")
        with patch("services.files_service.os.access", return_value=False):
            with pytest.raises(PermissionError):
                FilesHandler.compute_file_hash(str(f))
