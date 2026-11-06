"""A copy that fails is not a trailer (#705).

The temporary folder of the container and the media folder are often on
different file systems. Then `shutil.move` copies the file. The copy
creates the new file first, so a copy that stops before the end leaves an
empty or short file. Before the fix, Trailarr saw that the file exists and
recorded a good download. The size in the row came from the file in the
temporary folder, so the row showed a good size for a bad file.

The last two tests of the move use a real copy between two real file
systems, and a real limit of the file size makes the write fail.
"""

from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from exceptions import FileMoveFailedError
from services.trailers.trailer_file import (
    get_folder_permissions,
    move_trailer_to_folder,
)
from services.trailers.trailers import service
from services.trailers.video_analysis import StreamInfo, VideoInfo
from utils.error_classify import classify_folder_error

_MOVE = "services.trailers.trailer_file.shutil.move"
_COPY = "services.trailers.trailer_file.shutil.copyfile"
# The real functions, for the fakes that run while the patches are on.
_real_move = shutil.move
_real_copyfile = shutil.copyfile


@pytest.fixture
def media(tmp_path):
    folder = tmp_path / "media" / "Movie (2024)"
    folder.mkdir(parents=True)
    media = MagicMock()
    media.id = 1
    media.title = "Movie"
    media.folder_path = str(folder)
    media.media_filename = "Movie.2024.mkv"
    media.model_dump.return_value = {
        "id": 1,
        "title": "Movie",
        "year": 2024,
        "is_movie": True,
        "folder_path": str(folder),
        "media_filename": "Movie.2024.mkv",
    }
    return media


@pytest.fixture
def profile():
    profile = MagicMock()
    profile.id = 1
    profile.file_name = "{title}-trailer.{ext}"
    profile.file_format = "mkv"
    profile.folder_enabled = False
    profile.custom_folder = "{media_folder}"
    profile.video_type = "trailer"
    return profile


def _download(folder: Path, size: int = 256 * 1024) -> tuple[Path, bytes]:
    """A download in the temporary folder."""
    folder.mkdir(parents=True, exist_ok=True)
    src = folder / "1-trailer.mkv"
    data = os.urandom(size)
    src.write_bytes(data)
    return src, data


def _files(media) -> list[Path]:
    return list(Path(media.folder_path).iterdir())


class TestTheMoveChecksTheCopy:
    def test_an_empty_copy_is_copied_again(self, tmp_path, media, profile):
        """The copy left an empty file. Trailarr copies again."""
        src, data = _download(tmp_path / "tmp")

        def copy_that_stops(s, d):
            Path(d).touch()
            raise OSError(errno.EIO, "Input/output error")

        with patch(_MOVE, side_effect=copy_that_stops):
            result = move_trailer_to_folder(src, media, profile)

        assert Path(result).read_bytes() == data
        assert not src.exists()
        assert _files(media) == [Path(result)]
        # The second copy gets the permissions of the folder too.
        expected = get_folder_permissions(Path(result).parent)
        assert Path(result).stat().st_mode & 0o777 == expected & 0o777

    def test_a_second_failed_copy_raises_the_error(
        self, tmp_path, media, profile
    ):
        """No empty file stays. The error of a full disk stays an OSError,
        so the download task says that the disk is full."""
        src, _ = _download(tmp_path / "tmp")

        def copy_that_stops(s, d):
            Path(d).write_bytes(b"x")
            raise OSError(errno.ENOSPC, "No space left on device", str(d))

        with (
            patch(_MOVE, side_effect=copy_that_stops),
            patch(_COPY, side_effect=copy_that_stops),
            pytest.raises(OSError) as raised,
        ):
            move_trailer_to_folder(src, media, profile)

        assert raised.value.errno == errno.ENOSPC
        assert "full" in classify_folder_error(raised.value)
        assert _files(media) == []
        assert src.exists()

    def test_a_complete_copy_without_attributes_is_kept(
        self, tmp_path, media, profile
    ):
        """#285: the copy is complete, but the folder does not let the app
        copy the attributes. Trailarr keeps the file and copies once."""
        src, data = _download(tmp_path / "tmp")

        def copy_without_attributes(s, d):
            _real_copyfile(s, d)
            raise PermissionError(errno.EPERM, "Operation not permitted")

        with (
            patch(_MOVE, side_effect=copy_without_attributes),
            patch(_COPY) as second_copy,
        ):
            result = move_trailer_to_folder(src, media, profile)

        second_copy.assert_not_called()
        assert Path(result).read_bytes() == data
        assert not src.exists()

    def test_a_folder_that_refuses_the_permissions_is_not_a_failure(
        self, tmp_path, media, profile
    ):
        """#285: the move is complete, and only the chmod fails."""
        src, data = _download(tmp_path / "tmp")

        with patch.object(
            Path, "chmod", side_effect=PermissionError(errno.EPERM, "no")
        ):
            result = move_trailer_to_folder(src, media, profile)

        assert Path(result).read_bytes() == data

    def test_a_short_file_after_a_move_without_an_error_is_a_failure(
        self, tmp_path, media, profile
    ):
        src, data = _download(tmp_path / "tmp")

        def move_that_cuts(s, d):
            Path(d).write_bytes(data[:10])
            Path(s).unlink()

        with (
            patch(_MOVE, side_effect=move_that_cuts),
            pytest.raises(FileMoveFailedError, match="10 bytes"),
        ):
            move_trailer_to_folder(src, media, profile)

        assert _files(media) == []

    def test_a_failed_move_without_the_download_is_a_failure(
        self, tmp_path, media, profile
    ):
        src, _ = _download(tmp_path / "tmp")

        def move_that_loses_the_file(s, d):
            Path(d).touch()
            Path(s).unlink()
            raise OSError(errno.EIO, "Input/output error")

        with (
            patch(_MOVE, side_effect=move_that_loses_the_file),
            pytest.raises(FileMoveFailedError, match="temporary folder"),
        ):
            move_trailer_to_folder(src, media, profile)

        assert _files(media) == []


def _other_file_system(tmp_path: Path) -> Path:
    """A temporary folder on a file system that is not the one of
    `tmp_path`, so that the move is a copy. Skips the test if there is
    none."""
    if sys.platform != "linux":
        pytest.skip("The size limit of a process is a Linux feature here.")
    shm = Path("/dev/shm")
    if not shm.is_dir() or shm.stat().st_dev == tmp_path.stat().st_dev:
        pytest.skip("No second file system for a real copy.")
    return Path(tempfile.mkdtemp(dir=shm, prefix="trailarr-705-"))


def _with_size_limit(func, limit: int):
    """Run `func` while the process cannot write a file past `limit`
    bytes. The write then fails with EFBIG, as a real failed copy does."""

    def limited(*args, **kwargs):
        soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
        old_handler = signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, hard))
        try:
            return func(*args, **kwargs)
        finally:
            resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))
            signal.signal(signal.SIGXFSZ, old_handler)

    return limited


class TestARealCopyThatFails:
    def test_the_second_copy_completes_the_trailer(
        self, tmp_path, media, profile
    ):
        temp_folder = _other_file_system(tmp_path)
        try:
            src, data = _download(temp_folder, size=1024 * 1024)
            with patch(
                _MOVE, side_effect=_with_size_limit(_real_move, 64 * 1024)
            ):
                result = move_trailer_to_folder(src, media, profile)

            assert Path(result).read_bytes() == data
            assert not src.exists()
        finally:
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_no_short_file_stays_when_the_copies_fail(
        self, tmp_path, media, profile
    ):
        temp_folder = _other_file_system(tmp_path)
        try:
            src, _ = _download(temp_folder, size=1024 * 1024)
            with (
                patch(
                    _MOVE,
                    side_effect=_with_size_limit(_real_move, 64 * 1024),
                ),
                patch(
                    _COPY,
                    side_effect=_with_size_limit(_real_copyfile, 64 * 1024),
                ),
                pytest.raises(OSError) as raised,
            ):
                move_trailer_to_folder(src, media, profile)

            assert raised.value.errno == errno.EFBIG
            assert _files(media) == []
            assert src.exists()
        finally:
            shutil.rmtree(temp_folder, ignore_errors=True)


class TestTheRowHasTheSizeOfTheTrailer:
    @pytest.mark.asyncio
    async def test_the_size_is_read_from_the_final_file(self, tmp_path):
        """The video info of a download comes from the file in the
        temporary folder. The row takes the size of the moved file."""
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"\0" * 1000)
        now = datetime(2026, 11, 5, tzinfo=timezone.utc)
        info = VideoInfo(
            name="1-trailer.mkv",
            file_path="/tmp/trailarr/1-trailer.mkv",
            format_name="matroska",
            duration_seconds=90,
            size=7_700_000,
            streams=[
                StreamInfo(index=0, codec_type="video", codec_name="h264"),
                StreamInfo(index=1, codec_type="audio", codec_name="aac"),
            ],
            created_at=now,
            updated_at=now,
        )

        with patch.object(service.download_manager, "create") as create:
            ok = await service.record_new_trailer_download(
                SimpleNamespace(id=1, title="Movie"),
                0,
                str(trailer),
                video_info=info,
            )

        assert ok is True
        [row] = create.call_args.args
        assert row.size == 1000
