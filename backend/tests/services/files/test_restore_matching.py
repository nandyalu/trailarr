"""Which download a file on disk belongs to (#733).

A person can change a trailer outside Trailarr: give it a new name, move it,
or change its tracks. A file matches a download by its path, then by its
file name, then by the YouTube id in its metadata. Two known YouTube ids
that are not the same are two videos.

The matcher tests need nothing. The other tests make real videos with
ffmpeg, with the YouTube URL in the metadata as yt-dlp writes it, and use
real database rows.
"""

import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlmodel import Session

import database.manager.download as download_manager
import database.manager.media as media_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.download import DownloadCreate
from database.models.media import MediaCreate
from services.files.restore import (
    find_matching_download,
    restore_if_on_disk,
    restore_returned_files,
)
from tasks.files_scan import scan_media_folder

NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)
YT_A = "dQw4w9WgXcQ"
YT_B = "KbWtUJjMj3Y"

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="needs ffmpeg and ffprobe",
)


@pytest.fixture(autouse=True)
def system_ffprobe(monkeypatch):
    """The default path is the one in the Docker image. The app falls back
    to the system PATH at its start, which the tests do not run."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        monkeypatch.setenv("FFPROBE_PATH", ffprobe)


def _row(path: str, youtube_id: str = "unknown0000", row_id: int = 1):
    return SimpleNamespace(id=row_id, path=path, youtube_id=youtube_id)


class TestFindMatchingDownload:
    def test_the_same_path_matches(self):
        row = _row("/m/Movie-trailer.mkv")
        assert find_matching_download(row.path, None, [row]) is row

    def test_the_same_name_in_another_folder_matches(self):
        row = _row("/m/Movie-trailer.mkv")
        found = find_matching_download("/m/Trailers/Movie-trailer.mkv", None, [row])
        assert found is row

    def test_the_same_youtube_id_under_a_new_name_matches(self):
        row = _row("/m/Movie-trailer.mkv", YT_A)
        found = find_matching_download("/m/Renamed.mkv", YT_A, [row])
        assert found is row

    def test_another_known_youtube_id_is_another_video(self):
        row = _row("/m/Movie-trailer.mkv", YT_A)
        assert find_matching_download(row.path, YT_B, [row]) is None

    def test_a_file_without_an_id_matches_by_name_only(self):
        row = _row("/m/Movie-trailer.mkv", YT_A)
        assert find_matching_download("/m/Renamed.mkv", None, [row]) is None

    def test_the_path_wins_over_the_youtube_id(self):
        by_path = _row("/m/Movie-trailer.mkv", row_id=1)
        by_id = _row("/m/Other.mkv", YT_A, row_id=2)
        found = find_matching_download(by_path.path, YT_A, [by_id, by_path])
        assert found is by_path


def _video(path: Path, youtube_id: str | None, seconds: int = 1) -> int:
    """Make a real video. yt-dlp writes the URL of the video in the tags."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tags = (
        ["-metadata", f"comment=https://www.youtube.com/watch?v={youtube_id}"]
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


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Match Test {uuid.uuid4().hex[:8]}",
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
            arr_id=95001,
            is_movie=True,
            title="Matched Movie",
            txdb_id=f"match-{uuid.uuid4().hex[:8]}",
            folder_path=str(folder),
        )
    ).id


def _deleted(media_id: int, path: Path, youtube_id: str, size: int) -> int:
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
            added_at=NOW,
            updated_at=NOW,
        )
    ).id
    download_manager.mark_as_deleted(download_id)
    return download_id


@needs_ffmpeg
class TestRestoreAtTheStoredPath:
    @pytest.mark.asyncio
    async def test_an_edited_file_is_restored_and_analyzed_again(
        self, tmp_path
    ):
        """The tracks changed, so the size changed: same download."""
        folder = tmp_path / "Movie (2016)"
        trailer = folder / "Movie-trailer.mkv"
        size = _video(trailer, YT_A, seconds=2)
        download_id = _deleted(_media(folder), trailer, YT_A, size + 999)

        restored = await restore_if_on_disk(
            download_manager.read(download_id), "Test", "Matched Movie"
        )

        row = download_manager.read(download_id)
        assert restored is True
        assert row.file_exists is True
        assert row.size == size
        assert row.duration == 2
        assert row.youtube_id == YT_A

    @pytest.mark.asyncio
    async def test_another_video_at_the_path_stays_deleted(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        trailer = folder / "Movie-trailer.mkv"
        size = _video(trailer, YT_B)
        download_id = _deleted(_media(folder), trailer, YT_A, size + 999)

        restored = await restore_if_on_disk(
            download_manager.read(download_id), "Test", "Matched Movie"
        )

        assert restored is False
        assert download_manager.read(download_id).file_exists is False


@needs_ffmpeg
class TestSearchTheFolder:
    @pytest.mark.asyncio
    async def test_a_renamed_file_is_found_by_its_youtube_id(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        renamed = folder / "Movie (2016) - Official Trailer-trailer.mkv"
        size = _video(renamed, YT_A)
        download_id = _deleted(
            media_id, folder / "Movie-trailer.mkv", YT_A, size + 999
        )

        restored = await restore_returned_files(
            media_manager.read(media_id), "Test", search_folder=True
        )

        row = download_manager.read(download_id)
        assert restored == 1
        assert row.file_exists is True
        assert row.path == str(renamed)
        assert row.file_name == renamed.name
        assert row.size == size

    @pytest.mark.asyncio
    async def test_a_moved_file_is_found_by_its_name(self, tmp_path):
        """No YouTube id: the file name in another folder decides."""
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        moved = folder / "Trailers" / "Movie-trailer.mkv"
        size = _video(moved, None)
        download_id = _deleted(
            media_id, folder / "Movie-trailer.mkv", "unknown0000", size
        )

        restored = await restore_returned_files(
            media_manager.read(media_id), "Test", search_folder=True
        )

        assert restored == 1
        assert download_manager.read(download_id).path == str(moved)

    @pytest.mark.asyncio
    async def test_the_daily_sweep_does_not_search(self, tmp_path):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        size = _video(folder / "Renamed-trailer.mkv", YT_A)
        download_id = _deleted(
            media_id, folder / "Movie-trailer.mkv", YT_A, size
        )

        restored = await restore_returned_files(
            media_manager.read(media_id), "Test"
        )

        assert restored == 0
        assert download_manager.read(download_id).file_exists is False


@needs_ffmpeg
class TestTheScanUsesTheSameRules:
    @pytest.mark.asyncio
    async def test_a_returned_renamed_file_takes_its_download_back(
        self, tmp_path
    ):
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        renamed = folder / "Renamed-trailer.mkv"
        size = _video(renamed, YT_A)
        download_id = _deleted(
            media_id, folder / "Movie-trailer.mkv", YT_A, size + 999
        )

        new, missing, renamed_count, _m, _u = await scan_media_folder(
            media_manager.read(media_id)
        )

        rows = download_manager.read_by_media_id(media_id)
        assert [r.id for r in rows] == [download_id]
        assert rows[0].file_exists is True
        assert rows[0].path == str(renamed)
        assert rows[0].size == size
        assert (new, missing) == (1, 0)

    @pytest.mark.asyncio
    async def test_a_renamed_and_edited_trailer_keeps_its_download(
        self, tmp_path
    ):
        """Another name and other content: no hash match, but the same
        YouTube id. Before #733 this was a new download and a deleted one."""
        folder = tmp_path / "Movie (2016)"
        media_id = _media(folder)
        old = folder / "Movie-trailer.mkv"
        old_size = _video(old, YT_A, seconds=1)
        download_id = download_manager.create(
            DownloadCreate(
                media_id=media_id,
                path=str(old),
                file_name=old.name,
                file_hash="hash-of-the-old-file",
                size=old_size,
                resolution=1080,
                file_format="mkv",
                video_format="h264",
                audio_format="aac",
                youtube_id=YT_A,
                profile_id=0,
                added_at=NOW,
                updated_at=NOW,
            )
        ).id
        old.unlink()
        edited = folder / "Movie (2016) - Remux-trailer.mkv"
        new_size = _video(edited, YT_A, seconds=2)

        new, missing, renamed_count, _m, _u = await scan_media_folder(
            media_manager.read(media_id)
        )

        rows = download_manager.read_by_media_id(media_id)
        assert [r.id for r in rows] == [download_id]
        assert rows[0].file_exists is True
        assert rows[0].path == str(edited)
        assert rows[0].size == new_size
        assert rows[0].duration == 2
        assert (new, missing, renamed_count) == (0, 0, 1)
