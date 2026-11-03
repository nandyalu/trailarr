"""The last check before a download restores a file that is back (#733).

A network share can come back between two runs of the Cleanup Task. The
download task then saw only a deleted download, and it downloaded the
same video again under a "Trailer 2" name. Now it restores the download
first, and the profile needs no download.

These tests use real folders and real database rows.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

import database.manager.download as download_manager
import database.manager.media as media_manager
import database.manager.trailerprofile as profile_manager
from database.engine import engine, write_session
from database.models.connection import ArrType, Connection
from database.models.customfilter import CustomFilterCreate, FilterType
from database.models.download import DownloadCreate
from database.models.event import Event, EventType
from database.models.filter import FilterCondition, FilterCreate
from database.models.media import MediaCreate
from database.models.trailerprofile import TrailerProfileCreate
from services.files.restore import restore_returned_files
from services.trailers.trailers import missing

NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Restore Test {uuid.uuid4().hex[:8]}",
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
            arr_id=94001,
            is_movie=True,
            title="Returned Movie",
            txdb_id=f"restore-{uuid.uuid4().hex[:8]}",
            folder_path=str(folder),
            monitor=True,
        )
    )
    return media.id


def _profile():
    # A filter that matches no media, so the tests of other files never
    # pick this profile up. These tests give it to the media themselves.
    return profile_manager.create_trailerprofile(
        TrailerProfileCreate(
            customfilter=CustomFilterCreate(
                filter_name=f"Restore Profile {uuid.uuid4().hex[:6]}",
                filter_type=FilterType.TRAILER,
                filters=[
                    FilterCreate(
                        filter_by="txdb_id",
                        filter_condition=FilterCondition.EQUALS,
                        filter_value="restore-scope",
                    )
                ],
            ),
        )
    )


def _download(
    media_id: int, path: Path, profile_id: int, size: int = 7
) -> int:
    return download_manager.create(
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
            profile_id=profile_id,
            added_at=NOW,
            updated_at=NOW,
        )
    ).id


def _detected(media_id: int) -> list[str]:
    with Session(engine) as session:
        rows = session.exec(
            select(Event)
            .where(Event.media_id == media_id)
            .where(Event.event_type == EventType.TRAILER_DETECTED)
        ).all()
    return [row.source_detail for row in rows]


async def _eligible(media_id: int, profile) -> list[int]:
    with (
        patch.object(
            missing.trailerprofile,
            "get_trailerprofiles",
            return_value=[profile],
        ),
        patch.object(
            missing, "find_matching_profiles", return_value=[profile]
        ),
    ):
        _, eligible = await missing._read_current_eligible_profiles(media_id)
    return [p.id for p in eligible]


class TestCheckBeforeDownload:
    @pytest.mark.asyncio
    async def test_a_file_that_is_back_needs_no_download(self, tmp_path):
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"7 bytes")
        profile = _profile()
        media_id = _media(tmp_path)
        download_id = _download(media_id, trailer, profile.id)
        download_manager.mark_as_deleted(download_id)

        assert await _eligible(media_id, profile) == []

        assert download_manager.read(download_id).file_exists is True
        assert _detected(media_id) == ["DownloadMissingTrailers"]

    @pytest.mark.asyncio
    async def test_a_file_that_is_gone_is_downloaded(self, tmp_path):
        profile = _profile()
        media_id = _media(tmp_path)
        download_id = _download(
            media_id, tmp_path / "Movie-trailer.mkv", profile.id
        )
        download_manager.mark_as_deleted(download_id)

        assert await _eligible(media_id, profile) == [profile.id]

        assert download_manager.read(download_id).file_exists is False
        assert _detected(media_id) == []


class TestRestoreReturnedFiles:
    @pytest.mark.asyncio
    async def test_only_the_newest_row_of_a_path_is_restored(self, tmp_path):
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"7 bytes")
        profile = _profile()
        media_id = _media(tmp_path)
        older = _download(media_id, trailer, profile.id)
        newer = _download(media_id, trailer, profile.id)
        download_manager.mark_as_deleted(older)
        download_manager.mark_as_deleted(newer)

        restored = await restore_returned_files(
            media_manager.read(media_id), "Test"
        )

        assert restored == 1
        assert download_manager.read(older).file_exists is False
        assert download_manager.read(newer).file_exists is True

    @pytest.mark.asyncio
    async def test_a_path_with_an_active_download_is_skipped(self, tmp_path):
        trailer = tmp_path / "Movie-trailer.mkv"
        trailer.write_bytes(b"7 bytes")
        profile = _profile()
        media_id = _media(tmp_path)
        old = _download(media_id, trailer, profile.id)
        download_manager.mark_as_deleted(old)
        _download(media_id, trailer, profile.id)

        restored = await restore_returned_files(
            media_manager.read(media_id), "Test"
        )

        assert restored == 0
        assert download_manager.read(old).file_exists is False
