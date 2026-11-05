"""The Cleanup Task and storage that is not there (#733).

A Docker bind whose source did not exist when the container started shows
the media folders as an empty folder. The Cleanup Task then marked every
trailer deleted, and nothing set the downloads back when the files were
visible again, so the profiles downloaded the same videos again.

These tests use real folders and real database rows.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlmodel import Session, select

import database.manager.download as download_manager
import database.manager.media as media_manager
from database.engine import engine, write_session
from database.models.connection import ArrType, Connection
from database.models.download import DownloadCreate
from database.models.event import Event, EventType
from database.models.media import MediaCreate
from services.files.files_handler import folder_has_entries
from tasks import startup_passes
from tasks.cleanup import restore_returned_trailers, trailer_cleanup

NOW = datetime(2026, 11, 2, tzinfo=timezone.utc)


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Storage Test {uuid.uuid4().hex[:8]}",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


def _media(folder: Path) -> int:
    media = media_manager.create(
        MediaCreate(
            connection_id=_make_connection().id,  # type: ignore[arg-type]
            arr_id=93001,
            is_movie=True,
            title="Storage Movie",
            txdb_id=f"storage-{uuid.uuid4().hex[:8]}",
            folder_path=str(folder),
        )
    )
    return media.id


def _download(media_id: int, path: Path, size: int = 7, **kw) -> int:
    download = download_manager.create(
        DownloadCreate(
            media_id=media_id,
            path=str(path),
            file_name=path.name,
            file_hash="",
            size=size,
            resolution=1080,
            file_format="mkv",
            video_format="h264",
            audio_format="aac",
            profile_id=0,
            added_at=NOW,
            updated_at=NOW,
            **kw,
        )
    )
    return download.id


def _exists(download_id: int) -> bool:
    return download_manager.read(download_id).file_exists


def _events(media_id: int, event_type: EventType) -> int:
    with Session(engine) as session:
        rows = session.exec(
            select(Event)
            .where(Event.media_id == media_id)
            .where(Event.event_type == event_type)
        ).all()
    return len(rows)


class TestFolderHasEntries:
    def test_a_missing_folder_has_none(self, tmp_path):
        assert folder_has_entries(str(tmp_path / "missing")) is False

    def test_an_empty_folder_has_none(self, tmp_path):
        assert folder_has_entries(str(tmp_path)) is False

    def test_a_folder_with_a_file_has_entries(self, tmp_path):
        (tmp_path / "movie.mkv").write_bytes(b"x")
        assert folder_has_entries(str(tmp_path)) is True

    @pytest.mark.skipif(os.geteuid() == 0, reason="root can list any folder")
    def test_a_folder_that_cannot_be_listed_has_none(self, tmp_path):
        folder = tmp_path / "locked"
        folder.mkdir()
        (folder / "movie.mkv").write_bytes(b"x")
        folder.chmod(0)
        try:
            assert folder_has_entries(str(folder)) is False
        finally:
            folder.chmod(0o755)


class TestStorageGuard:
    @pytest.mark.asyncio
    async def test_an_empty_mount_keeps_the_trailer(self, tmp_path):
        """The case of #733: the share did not mount, so the folder that
        held the media folders is empty."""
        mount = tmp_path / "Films"
        mount.mkdir()
        folder = mount / "Movie (2016)"
        media_id = _media(folder)
        download_id = _download(media_id, folder / "Movie-trailer.mkv")

        await trailer_cleanup()

        assert _exists(download_id) is True
        assert _events(media_id, EventType.TRAILER_DELETED) == 0

    @pytest.mark.asyncio
    async def test_a_trailer_gone_from_a_present_folder_is_deleted(
        self, tmp_path
    ):
        folder = tmp_path / "Movie (2016)"
        folder.mkdir()
        (folder / "Movie.mkv").write_bytes(b"movie")
        media_id = _media(folder)
        download_id = _download(media_id, folder / "Movie-trailer.mkv")

        await trailer_cleanup()

        assert _exists(download_id) is False
        assert _events(media_id, EventType.TRAILER_DELETED) == 1

    @pytest.mark.asyncio
    async def test_a_trailer_gone_from_its_subfolder_is_deleted(
        self, tmp_path
    ):
        """The media folder holds files, so the storage is there, though
        the Trailers folder is now empty."""
        folder = tmp_path / "Movie (2016)"
        (folder / "Trailers").mkdir(parents=True)
        (folder / "Movie.mkv").write_bytes(b"movie")
        media_id = _media(folder)
        download_id = _download(
            media_id, folder / "Trailers" / "Movie-trailer.mkv"
        )

        await trailer_cleanup()

        assert _exists(download_id) is False

    @pytest.mark.asyncio
    async def test_a_custom_folder_is_examined_on_its_own(self, tmp_path):
        """A trailer outside the media folder depends on its own folder,
        not on the media folder."""
        folder = tmp_path / "Movie (2016)"
        folder.mkdir()
        (folder / "Movie.mkv").write_bytes(b"movie")
        media_id = _media(folder)
        gone_mount = tmp_path / "trailers-share" / "Movie"
        kept = _download(media_id, gone_mount / "Movie-trailer.mkv")
        present = tmp_path / "trailers-local"
        present.mkdir()
        (present / "Other-trailer.mkv").write_bytes(b"other")
        deleted = _download(media_id, present / "Movie-trailer.mkv")

        await trailer_cleanup()

        assert _exists(kept) is True
        assert _exists(deleted) is False


class TestRestoreReturnedTrailers:
    @pytest.mark.asyncio
    async def test_a_file_back_on_disk_is_restored(self, tmp_path):
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"7 bytes")
        media_id = _media(tmp_path)
        download_id = _download(media_id, trailer, size=7)
        download_manager.mark_as_deleted(download_id)

        assert await restore_returned_trailers() >= 1

        assert _exists(download_id) is True
        assert _events(media_id, EventType.TRAILER_DETECTED) == 1

    @pytest.mark.asyncio
    async def test_a_missing_file_stays_deleted(self, tmp_path):
        media_id = _media(tmp_path)
        download_id = _download(media_id, tmp_path / "Movie-trailer.mkv")
        download_manager.mark_as_deleted(download_id)

        await restore_returned_trailers()

        assert _exists(download_id) is False

    @pytest.mark.asyncio
    async def test_a_changed_file_that_is_not_a_video_stays_deleted(
        self, tmp_path
    ):
        """Another size: ffprobe examines the file, and it is no video.
        test_restore_matching.py tests an edited video."""
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"a different file")
        media_id = _media(tmp_path)
        download_id = _download(media_id, trailer, size=7)
        download_manager.mark_as_deleted(download_id)

        await restore_returned_trailers()

        assert _exists(download_id) is False

    @pytest.mark.asyncio
    async def test_a_path_with_an_active_download_stays_deleted(
        self, tmp_path
    ):
        """The scan or a new download recorded the file again already."""
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"7 bytes")
        media_id = _media(tmp_path)
        old = _download(media_id, trailer, size=7)
        download_manager.mark_as_deleted(old)
        new = _download(media_id, trailer, size=7)

        await restore_returned_trailers()

        assert _exists(old) is False
        assert _exists(new) is True

    def test_the_restore_checks_again_under_the_write_lock(self, tmp_path):
        """The disk scan recorded the file after the Cleanup Task read the
        deleted downloads: the restore must not make a second active row."""
        trailer = tmp_path / "Movie-trailer.mkv"
        media_id = _media(tmp_path)
        old = _download(media_id, trailer, size=7)
        download_manager.mark_as_deleted(old)
        _download(media_id, trailer, size=7)

        assert download_manager.mark_as_restored(old) is False
        assert _exists(old) is False

    def test_an_active_download_is_not_restored_again(self, tmp_path):
        media_id = _media(tmp_path)
        download_id = _download(media_id, tmp_path / "Movie-trailer.mkv")

        assert download_manager.mark_as_restored(download_id) is False

    @pytest.mark.asyncio
    async def test_a_returned_extra_is_restored_without_an_event(
        self, tmp_path
    ):
        """As in the disk scan: no trailer event for an extra."""
        extra = tmp_path / "Movie-featurette.mkv"
        extra.write_bytes(b"7 bytes")
        media_id = _media(tmp_path)
        download_id = _download(
            media_id, extra, size=7, video_type="featurette"
        )
        download_manager.mark_as_deleted(download_id)

        await restore_returned_trailers()

        assert _exists(download_id) is True
        assert _events(media_id, EventType.TRAILER_DETECTED) == 0

    @pytest.mark.asyncio
    async def test_only_the_newest_row_of_a_path_is_restored(self, tmp_path):
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"7 bytes")
        media_id = _media(tmp_path)
        older = _download(media_id, trailer, size=7)
        newer = _download(media_id, trailer, size=7)
        download_manager.mark_as_deleted(older)
        download_manager.mark_as_deleted(newer)

        await restore_returned_trailers()

        assert _exists(older) is False
        assert _exists(newer) is True


class TestRestorePass:
    def test_the_first_download_waits_for_the_restore(self):
        assert (
            startup_passes.PASS_RESTORE_RETURNED_TRAILERS
            in startup_passes.DOWNLOADS_REQUIRED_PASSES
        )

    def test_the_restore_pass_runs_at_every_start(self):
        """The storage can be away at the first start of v0.14.2, and the
        files come back only after a later start."""
        policies = {name: policy for name, _f, policy in startup_passes.REGISTRY}
        assert (
            policies[startup_passes.PASS_RESTORE_RETURNED_TRAILERS] == "always"
        )
