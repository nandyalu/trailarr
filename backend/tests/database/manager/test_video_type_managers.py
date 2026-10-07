"""Manager rules for video types — plans/phase-09-video-types.md.

- A profile that changes its type takes its downloads with it (W1).
- The TMDB refresh replaces every type in one call, so a video that TMDB
  moves from Teaser to Trailer changes its row ("What Phase 8 left").
- A download found on disk takes the type of its name, and a manual
  assignment records the type of the profile.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlmodel import Session

import database.manager.download as download_manager
import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
import database.manager.trailerprofile as profile_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.customfilter import CustomFilterCreate, FilterType
from database.models.filter import FilterCondition, FilterCreate
from database.models.download import DownloadCreate
from database.models.media import MediaCreate
from database.models.mediavideo import MediaVideoCreate, VideoSource
from database.models.trailerprofile import TrailerProfileCreate

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Type Test {uuid.uuid4().hex[:8]}",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


@pytest.fixture
def media_id() -> int:
    conn = _make_connection()
    media = media_manager.create(
        MediaCreate(
            connection_id=conn.id,  # type: ignore[arg-type]
            arr_id=91001,
            is_movie=True,
            title="Type Movie",
            txdb_id=f"type-{uuid.uuid4().hex[:8]}",
        )
    )
    return media.id


def _profile_create(video_type: str = "trailer") -> TrailerProfileCreate:
    # A filter that matches no media, so the attribution tests of other
    # files never pick this profile up.
    return TrailerProfileCreate(
        video_type=video_type,
        customfilter=CustomFilterCreate(
            filter_name=f"Type Profile {uuid.uuid4().hex[:6]}",
            filter_type=FilterType.TRAILER,
            filters=[
                FilterCreate(
                    filter_by="txdb_id",
                    filter_condition=FilterCondition.EQUALS,
                    filter_value="phase9-type-scope",
                )
            ],
        ),
    )


def _download(media_id: int, profile_id: int, name: str, **kw) -> DownloadCreate:
    return DownloadCreate(
        media_id=media_id,
        path=f"/nonexistent/{name}",
        file_name=name,
        file_hash="",
        size=1,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        profile_id=profile_id,
        added_at=NOW,
        updated_at=NOW,
        **kw,
    )


class TestProfileTypeChangeRelabelsDownloads:
    def test_update_relabels_the_downloads_of_the_profile(self, media_id):
        profile = profile_manager.create_trailerprofile(_profile_create())
        download_manager.create(_download(media_id, profile.id, "a.mkv"))
        download_manager.create(
            _download(media_id, profile.id, "b.mkv", video_type="teaser")
        )
        other = profile_manager.create_trailerprofile(_profile_create())
        download_manager.create(_download(media_id, other.id, "c.mkv"))

        update = _profile_create("featurette")
        update.customfilter.filter_name = profile.customfilter.filter_name
        profile_manager.update_trailerprofile(profile.id, update)

        rows = {
            d.file_name: d.video_type
            for d in download_manager.read_by_media_id(media_id)
        }
        assert rows["a.mkv"] == "featurette"
        assert rows["b.mkv"] == "featurette"
        assert rows["c.mkv"] == "trailer"

    def test_a_single_setting_update_relabels_too(self, media_id):
        profile = profile_manager.create_trailerprofile(_profile_create())
        download_manager.create(_download(media_id, profile.id, "d.mkv"))

        profile_manager.update_trailerprofile_setting(
            profile.id, "video_type", "clip"
        )

        [row] = download_manager.read_by_profile_id(profile.id)
        assert row.video_type == "clip"

    def test_no_change_no_write(self, media_id):
        profile = profile_manager.create_trailerprofile(_profile_create())
        download_manager.create(
            _download(media_id, profile.id, "e.mkv", video_type="teaser")
        )
        profile_manager.update_trailerprofile_setting(
            profile.id, "priority", 5
        )
        [row] = download_manager.read_by_profile_id(profile.id)
        assert row.video_type == "teaser"


class TestManualAssignRecordsTheType:
    def test_update_profile_id_takes_the_type(self, media_id):
        row = download_manager.create(
            _download(media_id, 0, "f.mkv", video_type="featurette")
        )
        download_manager.update_profile_id(row.id, 7, video_type="trailer")
        assert download_manager.read(row.id).video_type == "trailer"
        assert download_manager.read(row.id).profile_id == 7

    def test_without_a_type_the_row_keeps_its_own(self, media_id):
        row = download_manager.create(
            _download(media_id, 0, "g.mkv", video_type="featurette")
        )
        download_manager.update_profile_id(row.id, 7)
        assert download_manager.read(row.id).video_type == "featurette"


def _video(media_id: int, video_id: str, video_type: str, **kw):
    return MediaVideoCreate(
        media_id=media_id,
        video_id=video_id,
        source=VideoSource.TMDB,
        video_type=video_type,
        sequence=kw.pop("sequence", 0),
        language="en",
        name=kw.pop("name", video_id),
        official=True,
    )


class TestReplaceSourceRowsAcrossTypes:
    def test_one_call_covers_every_type(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video(media_id, "t1", "trailer"),
                _video(media_id, "f1", "featurette"),
            ],
            video_type=None,
        )
        rows = {v.video_id: v for v in video_manager.read_for_media(media_id)}
        assert rows["t1"].video_type == "trailer"
        assert rows["f1"].video_type == "featurette"

    def test_a_video_that_tmdb_moves_to_another_type_changes_its_row(
        self, media_id
    ):
        """The unique key is (media_id, video_id). A per-type call would
        try to insert the moved video again and raise."""
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video(media_id, "v1", "teaser")],
            video_type=None,
        )
        added, updated, removed = video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video(media_id, "v1", "trailer")],
            video_type=None,
        )
        assert (added, updated, removed) == (0, 1, 0)
        [row] = video_manager.read_for_media(media_id)
        assert row.video_type == "trailer"

    def test_a_list_of_one_type_leaves_the_other_types_alone(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video(media_id, "t1", "trailer"),
                _video(media_id, "f1", "featurette"),
            ],
            video_type=None,
        )
        # The SEARCH source writes trailers only, as before.
        video_manager.replace_source_rows(
            media_id,
            VideoSource.SEARCH,
            [
                MediaVideoCreate(
                    media_id=media_id,
                    video_id="s1",
                    source=VideoSource.SEARCH,
                    sequence=0,
                    name="",
                    official=False,
                )
            ],
        )
        rows = {v.video_id: v for v in video_manager.read_for_media(media_id)}
        assert set(rows) == {"t1", "f1", "s1"}

    def test_read_candidates_filters_by_type(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video(media_id, "t1", "trailer"),
                _video(media_id, "f1", "featurette"),
                _video(media_id, "f2", "featurette", sequence=1),
            ],
            video_type=None,
        )
        assert [
            v.video_id for v in video_manager.read_candidates(media_id)
        ] == ["t1"]
        assert [
            v.video_id
            for v in video_manager.read_candidates(
                media_id, video_type="featurette"
            )
        ] == ["f1", "f2"]
