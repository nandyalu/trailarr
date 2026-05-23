"""Tests for db/repos/trailer_status.py — Plan 1a coverage."""

import pytest

import db.repos.trailer_profile as profile_repo
import db.repos.trailer_status as trailer_status_repo
from db.engine import write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.customfilter import CustomFilterCreate, FilterType
from db.models.media import MediaCreate
from db.models.mediatrailerstatus import MediaTrailerStatus, TrailerStatusEnum
from db.models.trailerprofile import TrailerProfileCreate
from sqlmodel import Session


@write_session
def _make_connection(*, _session: Session = None) -> int:  # type: ignore
    conn = Connection(
        name="Test Connection for Status Repo",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="testkey",
        monitor=MonitorType.MONITOR_MISSING,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


@write_session
def _make_media(connection_id: int, title: str = "Test Movie", *, _session: Session = None) -> int:  # type: ignore
    import datetime
    from db.models.media import Media
    media = Media(
        connection_id=connection_id,
        arr_id=1,
        is_movie=True,
        title=title,
        clean_title=title.lower(),
        year=2024,
        language="en",
        studio="Studio",
        txdb_id="55501",
        title_slug=title.lower().replace(" ", "-"),
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=120,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )
    _session.add(media)
    _session.commit()
    _session.refresh(media)
    return media.id  # type: ignore


def _make_profile(for_movies: bool = True) -> int:
    profile_create = TrailerProfileCreate(
        for_movies=for_movies,
        enabled=True,
        customfilter=CustomFilterCreate(
            filter_name="Test Status Repo Profile",
            filter_type=FilterType.TRAILER,
            filters=[],
        ),
    )
    profile = profile_repo.create(profile_create)
    return profile.id


@write_session
def _make_download(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    import datetime
    from db.models.download import Download
    d = Download(
        media_id=media_id,
        path="/media/trailer.mkv",
        file_name="trailer.mkv",
        file_hash="abc",
        size=1024,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        duration=90.0,
        youtube_id="testid",
        file_exists=True,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )
    _session.add(d)
    _session.commit()
    _session.refresh(d)
    return d.id  # type: ignore


@write_session
def _make_status_row(
    media_id: int,
    profile_id: int,
    status: TrailerStatusEnum,
    linked_download_id: int | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    row = MediaTrailerStatus(
        media_id=media_id,
        profile_id=profile_id,
        season=0,
        sequence=1,
        status=status,
        source="app",
        linked_download_id=linked_download_id,
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row.id  # type: ignore


@write_session
def _get_row(row_id: int, *, _session: Session = None):  # type: ignore
    return _session.get(MediaTrailerStatus, row_id)


class TestDeleteUndownloadedRowsForProfile:
    """1a — UNMONITORED rows must survive delete_undownloaded_rows_for_profile."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn_id = _make_connection()
        self.media_id = _make_media(self.conn_id)
        self.profile_id = _make_profile()

    def test_preserves_unmonitored_rows(self):
        row_id = _make_status_row(
            self.media_id, self.profile_id, TrailerStatusEnum.UNMONITORED
        )

        trailer_status_repo.delete_undownloaded_rows_for_profile(
            profile_id=self.profile_id,
            media_ids=[self.media_id],
        )

        assert _get_row(row_id) is not None, "UNMONITORED row must not be deleted"

    def test_deletes_pending_rows(self):
        row_id = _make_status_row(
            self.media_id, self.profile_id, TrailerStatusEnum.PENDING
        )

        trailer_status_repo.delete_undownloaded_rows_for_profile(
            profile_id=self.profile_id,
            media_ids=[self.media_id],
        )

        assert _get_row(row_id) is None, "PENDING row with no download must be deleted"

    def test_preserves_rows_with_linked_download(self):
        download_id = _make_download(self.media_id)
        row_id = _make_status_row(
            self.media_id, self.profile_id, TrailerStatusEnum.PENDING,
            linked_download_id=download_id,
        )

        trailer_status_repo.delete_undownloaded_rows_for_profile(
            profile_id=self.profile_id,
            media_ids=[self.media_id],
        )

        assert _get_row(row_id) is not None, "Row with a linked download must be preserved"

    def test_deletes_failed_rows(self):
        row_id = _make_status_row(
            self.media_id, self.profile_id, TrailerStatusEnum.FAILED
        )

        trailer_status_repo.delete_undownloaded_rows_for_profile(
            profile_id=self.profile_id,
            media_ids=[self.media_id],
        )

        assert _get_row(row_id) is None, "FAILED row with no download must be deleted"
