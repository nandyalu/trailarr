"""Guards around a restore that the review of v0.14.2 found (#733).

- The disk scan does not record a second active download when a restore
  takes the file while the scan examines it.
- A restore whose new analysis fails keeps the download deleted.
- A file that ffprobe cannot read does not take a download back.
- A renamed and edited extra makes no `TRAILER_RENAMED` event.

The tests make real videos with ffmpeg and use real database rows.
"""

import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session

import database.manager.download as download_manager
import database.manager.media as media_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.download import DownloadCreate
from database.models.media import MediaCreate
from services.files import restore
from services.files.restore import (
    restore_if_on_disk,
    restore_returned_files,
)
from tasks.files_scan import scan_media_folder

NOW = datetime(2026, 11, 5, tzinfo=timezone.utc)
YT_A = "dQw4w9WgXcQ"

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="needs ffmpeg and ffprobe",
)


@pytest.fixture(autouse=True)
def system_ffprobe(monkeypatch):
    """The default path is the one in the Docker image."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        monkeypatch.setenv("FFPROBE_PATH", ffprobe)


def _video(path: Path, youtube_id: str | None, seconds: int = 1) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tags = (
        [
            "-metadata",
            f"comment=https://www.youtube.com/watch?v={youtube_id}",
        ]
        if youtube_id
        else []
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"testsrc=size=160x90:rate=24:duration={seconds}",
            "-f", "lavfi", "-i", f"sine=duration={seconds}",
            "-shortest", "-c:v", "libx264", "-c:a", "aac", *tags, str(path),
        ],
        check=True,
    )
    return path.stat().st_size


def _not_a_video(path: Path) -> None:
    """A file with a video name that ffprobe cannot read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"this is not a video" * 100)


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Guard Test {uuid.uuid4().hex[:8]}",
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
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "Movie (2016).mkv").write_bytes(b"movie" * 1000)
    return media_manager.create(
        MediaCreate(
            connection_id=_make_connection().id,  # type: ignore[arg-type]
            arr_id=95101,
            is_movie=True,
            title="Guarded Movie",
            txdb_id=f"guard-{uuid.uuid4().hex[:8]}",
            folder_path=str(folder),
        )
    ).id


def _download(
    media_id: int,
    path: Path,
    youtube_id: str,
    size: int,
    video_type: str = "trailer",
    deleted: bool = True,
) -> int:
    download_id = download_manager.create(
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
            duration=60,
            youtube_id=youtube_id,
            profile_id=0,
            video_type=video_type,
            added_at=NOW,
            updated_at=NOW,
        )
    ).id
    if deleted:
        download_manager.mark_as_deleted(download_id)
    return download_id


def _create(media_id: int, path: Path) -> DownloadCreate:
    return DownloadCreate(
        media_id=media_id,
        path=str(path),
        file_name=path.name,
        file_hash="",
        size=1,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        youtube_id="unknown0000",
        profile_id=0,
        added_at=NOW,
        updated_at=NOW,
    )


class TestCreateIfPathUntracked:
    def test_an_active_download_at_the_path_blocks_the_create(
        self, tmp_path
    ):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        trailer = folder / "Movie-trailer.mkv"
        _download(media_id, trailer, YT_A, 10, deleted=False)

        created = download_manager.create_if_path_untracked(
            _create(media_id, trailer)
        )

        assert created is None
        assert len(download_manager.read_by_media_id(media_id)) == 1

    def test_a_deleted_download_at_the_path_does_not_block(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        trailer = folder / "Movie-trailer.mkv"
        _download(media_id, trailer, YT_A, 10)

        created = download_manager.create_if_path_untracked(
            _create(media_id, trailer)
        )

        assert created is not None
        assert created.file_exists is True


@needs_ffmpeg
class TestTheScanAndARestoreAtTheSameTime:
    @pytest.mark.asyncio
    async def test_a_restore_during_the_scan_makes_no_second_download(
        self, tmp_path
    ):
        """The Cleanup Task restores the download while the scan runs
        ffprobe on the file. The scan then sees that its own restore
        failed, and it must not record the file as a new download."""
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        trailer = folder / "Movie-trailer.mkv"
        size = _video(trailer, YT_A)
        download_id = _download(media_id, trailer, YT_A, size + 999)
        real_probe = restore.probe

        async def probe_while_cleanup_restores(file_path):
            assert download_manager.mark_as_restored(download_id)
            return await real_probe(file_path)

        with (
            patch(
                "tasks.files_scan.probe",
                side_effect=probe_while_cleanup_restores,
            ),
            patch(
                "tasks.files_scan.event_manager.track_trailer_detected"
            ) as detected,
        ):
            await scan_media_folder(media_manager.read(media_id))

        rows = download_manager.read_by_media_id(media_id)
        assert [(r.id, r.file_exists) for r in rows] == [(download_id, True)]
        detected.assert_not_called()


@needs_ffmpeg
class TestAFailedAnalysis:
    @pytest.mark.asyncio
    async def test_the_download_stays_deleted(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        trailer = folder / "Movie-trailer.mkv"
        size = _video(trailer, YT_A)
        download_id = _download(media_id, trailer, YT_A, size + 999)

        with (
            patch(
                "services.files.restore.reanalyze_trailer_download",
                new=AsyncMock(return_value=False),
            ),
            patch(
                "services.files.restore.event_manager.track_trailer_detected"
            ) as detected,
        ):
            restored = await restore_if_on_disk(
                download_manager.read(download_id), "Test", "Guarded Movie"
            )

        assert restored is False
        assert download_manager.read(download_id).file_exists is False
        detected.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_next_pass_restores_it(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        trailer = folder / "Movie-trailer.mkv"
        size = _video(trailer, YT_A)
        download_id = _download(media_id, trailer, YT_A, size + 999)
        with patch(
            "services.files.restore.reanalyze_trailer_download",
            new=AsyncMock(return_value=False),
        ):
            await restore_if_on_disk(
                download_manager.read(download_id), "Test", "Guarded Movie"
            )

        restored = await restore_if_on_disk(
            download_manager.read(download_id), "Test", "Guarded Movie"
        )

        row = download_manager.read(download_id)
        assert restored is True
        assert row.file_exists is True
        assert row.size == size


@needs_ffmpeg
class TestAFileThatFfprobeCannotRead:
    @pytest.mark.asyncio
    async def test_the_folder_search_does_not_take_it(self, tmp_path):
        """Same file name in another folder, but no analysis."""
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        _not_a_video(folder / "Trailers" / "Movie-trailer.mkv")
        download_id = _download(
            media_id, folder / "Movie-trailer.mkv", "unknown0000", 10
        )

        restored = await restore_returned_files(
            media_manager.read(media_id), "Test", search_folder=True
        )

        assert restored == 0
        assert download_manager.read(download_id).file_exists is False

    @pytest.mark.asyncio
    async def test_the_scan_does_not_take_it(self, tmp_path):
        """Same path, but no analysis."""
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        trailer = folder / "Movie-trailer.mkv"
        _not_a_video(trailer)
        download_id = _download(media_id, trailer, YT_A, 10)

        await scan_media_folder(media_manager.read(media_id))

        rows = download_manager.read_by_media_id(media_id)
        assert [(r.id, r.file_exists) for r in rows] == [
            (download_id, False)
        ]


@needs_ffmpeg
class TestARenamedAndEditedExtra:
    @pytest.mark.asyncio
    async def test_it_keeps_its_download_and_makes_no_event(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        old = folder / "Making Of-featurette.mkv"
        old_size = _video(old, YT_A, seconds=1)
        download_id = _download(
            media_id, old, YT_A, old_size,
            video_type="featurette", deleted=False,
        )
        old.unlink()
        edited = folder / "Making Of (Remux)-featurette.mkv"
        _video(edited, YT_A, seconds=2)

        with patch(
            "tasks.files_scan.event_manager.track_trailer_renamed"
        ) as renamed_event:
            await scan_media_folder(media_manager.read(media_id))

        rows = download_manager.read_by_media_id(media_id)
        assert [(r.id, r.path, r.file_exists) for r in rows] == [
            (download_id, str(edited), True)
        ]
        renamed_event.assert_not_called()
