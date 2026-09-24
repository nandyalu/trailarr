"""The sync decides where a stored YouTube id came from — Phase 8.

The upgrade cannot know. `media.youtube_trailer_id` holds an id from
Radarr for some items and a video Trailarr downloaded for others, and no
column tells them apart, so every migrated row starts as a SEARCH row.
Radarr is the only thing that can say, and it says it through the sync.

Sonarr never says anything: its metadata comes from TVDB, which holds no
YouTube trailer ids, so its series keep the SEARCH row they were given.
"""

import uuid

import pytest
from sqlmodel import Session

import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.media import MediaCreate
from database.models.mediavideo import MediaVideoCreate, VideoSource
from services.connections.arr_videos import sync_arr_video_id


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"ArrVideos {uuid.uuid4().hex[:8]}",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="k",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


@pytest.fixture
def media():
    conn = _make_connection()
    return media_manager.create(
        MediaCreate(
            connection_id=conn.id,  # type: ignore[arg-type]
            arr_id=92001,
            is_movie=True,
            title="Arr Videos Movie",
            txdb_id=f"av-{uuid.uuid4().hex[:8]}",
        )
    )


def _migrated_row(media_id: int, video_id: str):
    """What the upgrade leaves behind: a SEARCH row of unknown origin."""
    video_manager.replace_source_rows(
        media_id,
        VideoSource.SEARCH,
        [
            MediaVideoCreate(
                media_id=media_id,
                video_id=video_id,
                source=VideoSource.SEARCH,
                sequence=0,
                name="",
                official=False,
            )
        ],
    )


class TestTheSyncDecidesTheSource:

    def test_the_id_the_arr_reports_becomes_an_arr_row(self, media):
        _migrated_row(media.id, "fromRadarr")

        sync_arr_video_id(media, "fromRadarr")

        rows = video_manager.read_for_media(media.id)
        assert len(rows) == 1
        assert rows[0].source == VideoSource.ARR

    def test_an_id_the_arr_does_not_report_stays_a_search_row(self, media):
        """Trailarr found this one itself, so it keeps its own label."""
        _migrated_row(media.id, "trailarrFoundIt")

        sync_arr_video_id(media, "fromRadarr")

        rows = {
            r.video_id: r.source
            for r in video_manager.read_for_media(media.id)
        }
        assert rows["trailarrFoundIt"] == VideoSource.SEARCH
        assert rows["fromRadarr"] == VideoSource.ARR

    def test_a_series_keeps_its_search_row(self, media):
        """Sonarr reports nothing, so the sync passes it nothing."""
        _migrated_row(media.id, "seriesVideo")

        sync_arr_video_id(media, None)
        sync_arr_video_id(media, "")

        rows = video_manager.read_for_media(media.id)
        assert [(r.video_id, r.source) for r in rows] == [
            ("seriesVideo", VideoSource.SEARCH)
        ]

    def test_the_video_the_user_chose_is_never_taken(self, media):
        """Even when the Arr reports the very same id."""
        video_manager.add_user_video(media.id, "myPick")

        sync_arr_video_id(media, "myPick")

        rows = video_manager.read_for_media(media.id)
        assert len(rows) == 1
        assert rows[0].source == VideoSource.USER
