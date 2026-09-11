"""How Trailarr picks the video to download — plans/phase-08-tmdb.md.

`get_video_id` had no test of its own: every test that reaches it patches
it out. These tests use the real database and a real candidates table, and
patch only the YouTube search, so the choice itself is what is measured.

The exit criterion of Phase 8 is here: a trailer that TMDB lists wins over
the id that Radarr gave, and a log line says where the video came from.
"""

import uuid
from unittest.mock import patch

import pytest
from sqlmodel import Session

import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
import database.manager.trailerprofile as profile_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.customfilter import CustomFilterCreate
from database.models.filter import FilterCondition, FilterCreate
from database.models.media import MediaCreate
from database.models.mediavideo import MediaVideoCreate, VideoSource
from database.models.trailerprofile import TrailerProfileCreate
from services.trailers import trailer_search

SEARCH = "services.trailers.trailer_search.search_yt_for_trailer"


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Resolution {uuid.uuid4().hex[:8]}",
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
def media():
    conn = _make_connection()
    return media_manager.create(
        MediaCreate(
            connection_id=conn.id,  # type: ignore[arg-type]
            arr_id=91001,
            is_movie=True,
            title="Resolution Movie",
            txdb_id=f"res-{uuid.uuid4().hex[:8]}",
        )
    )


@pytest.fixture
def profile():
    # The filter matters even though these tests never run attribution: the
    # suite shares one database (hygiene H4), and a profile with no filters
    # matches every media item, so it would compete for the downloads of
    # other tests. This one can only ever match its own media.
    return profile_manager.create_trailerprofile(
        TrailerProfileCreate(
            customfilter=CustomFilterCreate(
                filter_name=f"Resolution {uuid.uuid4().hex[:6]}",
                filters=[
                    FilterCreate(
                        filter_by="title",
                        filter_condition=FilterCondition.EQUALS,
                        filter_value="Resolution Movie",
                    )
                ],
            )
        )
    )


def _add(media_id: int, video_id: str, source: VideoSource, sequence=0, language="en"):
    video_manager.replace_source_rows(
        media_id,
        source,
        [
            MediaVideoCreate(
                media_id=media_id,
                video_id=video_id,
                source=source,
                sequence=sequence,
                language=language,
                name=video_id,
                official=True,
            )
        ],
    )


class TestTheChoice:

    def test_a_tmdb_trailer_beats_the_id_from_the_arr(self, media, profile):
        """The promise of Phase 8."""
        _add(media.id, "arr-id", VideoSource.ARR)
        _add(media.id, "tmdb-id", VideoSource.TMDB)

        with patch(SEARCH) as search:
            chosen = trailer_search.get_video_id(media, profile)

        assert chosen == "tmdb-id"
        search.assert_not_called()

    def test_the_video_the_user_chose_beats_tmdb(self, media, profile):
        _add(media.id, "tmdb-id", VideoSource.TMDB)
        video_manager.add_user_video(media.id, "user-id")

        with patch(SEARCH):
            assert trailer_search.get_video_id(media, profile) == "user-id"

    def test_an_excluded_video_is_passed_over(self, media, profile):
        _add(media.id, "tmdb-id", VideoSource.TMDB)
        _add(media.id, "arr-id", VideoSource.ARR)

        with patch(SEARCH):
            chosen = trailer_search.get_video_id(
                media, profile, exclude=["tmdb-id"]
            )

        assert chosen == "arr-id"

    def test_no_candidate_falls_back_to_a_search(self, media, profile):
        with patch(SEARCH, return_value="found-id") as search:
            assert trailer_search.get_video_id(media, profile) == "found-id"
        search.assert_called_once()

    def test_what_the_search_found_is_remembered(self, media, profile):
        """The next run reads it from the table instead of searching."""
        with patch(SEARCH, return_value="found-id"):
            trailer_search.get_video_id(media, profile)

        rows = video_manager.read_for_media(media.id)
        assert [(r.video_id, r.source) for r in rows] == [
            ("found-id", VideoSource.SEARCH)
        ]

        with patch(SEARCH) as search:
            assert trailer_search.get_video_id(media, profile) == "found-id"
        search.assert_not_called()

    def test_nothing_anywhere_gives_nothing(self, media, profile):
        with patch(SEARCH, return_value=None):
            assert trailer_search.get_video_id(media, profile) is None


class TestAlwaysSearch:
    """The redefinition in the plan: `Always Search` drops the stored
    search result, and keeps everything a person or a curator chose."""

    def test_a_stored_search_result_is_not_reused(self, media, profile):
        _add(media.id, "old-search", VideoSource.SEARCH)
        profile.always_search = True

        with patch(SEARCH, return_value="fresh-id") as search:
            assert trailer_search.get_video_id(media, profile) == "fresh-id"
        search.assert_called_once()

    def test_the_tmdb_trailer_is_still_used(self, media, profile):
        _add(media.id, "tmdb-id", VideoSource.TMDB)
        _add(media.id, "old-search", VideoSource.SEARCH)
        profile.always_search = True

        with patch(SEARCH) as search:
            assert trailer_search.get_video_id(media, profile) == "tmdb-id"
        search.assert_not_called()


class TestTheLogLine:

    def test_the_log_says_where_the_video_came_from(self, media, profile, caplog):
        """Exit criterion: a log line per resolution names the source."""
        _add(media.id, "tmdb-id", VideoSource.TMDB)

        with caplog.at_level("INFO"):
            with patch(SEARCH):
                trailer_search.get_video_id(media, profile)

        assert any("TMDB" in record.message for record in caplog.records), (
            f"no line named TMDB: {[r.message for r in caplog.records]}"
        )
