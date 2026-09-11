"""Tests for the MediaVideo manager — plans/phase-08-tmdb.md.

The rules these tests hold:
  - each source owns its rows, and a refresh of one source never touches
    another source's rows (decision 2);
  - a USER row is never written or removed by automation (decision 5b,
    cross-phase invariant 6);
  - the resolver gets its candidates in the order USER, TMDB, ARR, SEARCH
    (decision 4), with the language of the profile preferred;
  - the same video from two sources stays one row (wargame W6).
"""

import uuid

import pytest
from sqlmodel import Session

import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
from database.engine import write_session
from database.models.connection import ArrType, Connection
from database.models.media import MediaCreate
from database.models.mediavideo import (
    MediaVideoCreate,
    VideoSource,
)


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name=f"Video Test {uuid.uuid4().hex[:8]}",
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
            arr_id=90001,
            is_movie=True,
            title="Video Movie",
            txdb_id=f"video-{uuid.uuid4().hex[:8]}",
        )
    )
    return media.id


def _video(video_id: str, media_id: int, **kw) -> MediaVideoCreate:
    return MediaVideoCreate(
        media_id=media_id,
        video_id=video_id,
        source=kw.pop("source", VideoSource.TMDB),
        sequence=kw.pop("sequence", 0),
        language=kw.pop("language", "en"),
        name=kw.pop("name", ""),
        official=kw.pop("official", True),
        **kw,
    )


class TestSourceOwnership:

    def test_a_refresh_adds_updates_and_removes_its_own_rows(self, media_id):
        added, updated, removed = video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("aaa", media_id, sequence=0), _video("bbb", media_id, sequence=1)],
        )
        assert (added, updated, removed) == (2, 0, 0)

        # TMDB no longer offers 'bbb', and 'aaa' moved down the list.
        added, updated, removed = video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("aaa", media_id, sequence=3), _video("ccc", media_id)],
        )
        assert (added, updated, removed) == (1, 1, 1)
        ids = {v.video_id for v in video_manager.read_for_media(media_id)}
        assert ids == {"aaa", "ccc"}

    def test_a_refresh_leaves_the_rows_of_other_sources_alone(self, media_id):
        video_manager.replace_source_rows(
            media_id, VideoSource.ARR, [_video("arr1", media_id, source=VideoSource.ARR)]
        )
        video_manager.add_user_video(media_id, "user1")

        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("tmdb1", media_id)]
        )
        # An empty TMDB list removes only the TMDB row.
        video_manager.replace_source_rows(media_id, VideoSource.TMDB, [])

        remaining = {
            v.video_id: v.source for v in video_manager.read_for_media(media_id)
        }
        assert remaining == {
            "arr1": VideoSource.ARR,
            "user1": VideoSource.USER,
        }

    def test_a_task_cannot_replace_the_videos_of_the_user(self, media_id):
        video_manager.add_user_video(media_id, "user1")
        with pytest.raises(ValueError, match="user"):
            video_manager.replace_source_rows(media_id, VideoSource.USER, [])
        assert len(video_manager.read_for_media(media_id)) == 1

    def test_the_same_video_from_two_sources_stays_one_row(self, media_id):
        """Wargame W6: unique (media_id, video_id); the first source keeps it."""
        video_manager.replace_source_rows(
            media_id, VideoSource.ARR, [_video("same", media_id, source=VideoSource.ARR)]
        )
        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("same", media_id)]
        )
        rows = video_manager.read_for_media(media_id)
        assert len(rows) == 1
        assert rows[0].source == VideoSource.ARR


class TestUserVideos:

    def test_adding_a_video_the_user_chose(self, media_id):
        row = video_manager.add_user_video(media_id, "chosen", name="My pick")
        assert row.source == VideoSource.USER
        assert row.name == "My pick"

    def test_choosing_a_video_another_source_offered_takes_the_row_over(
        self, media_id
    ):
        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("shared", media_id)]
        )
        row = video_manager.add_user_video(media_id, "shared")
        assert row.source == VideoSource.USER

        # And a later TMDB refresh can no longer remove it.
        video_manager.replace_source_rows(media_id, VideoSource.TMDB, [])
        assert [v.video_id for v in video_manager.read_for_media(media_id)] == [
            "shared"
        ]

    def test_relabelling_an_arr_row_as_the_choice_of_the_user(self, media_id):
        video_manager.replace_source_rows(
            media_id, VideoSource.ARR, [_video("hand", media_id, source=VideoSource.ARR)]
        )
        assert video_manager.relabel_as_user(media_id, "hand") is True
        assert video_manager.read_for_media(media_id)[0].source == VideoSource.USER
        # Already a USER row: nothing to do.
        assert video_manager.relabel_as_user(media_id, "hand") is False

    def test_removing_a_video(self, media_id):
        video_manager.add_user_video(media_id, "gone")
        assert video_manager.delete_video(media_id, "gone") is True
        assert video_manager.delete_video(media_id, "gone") is False


class TestCandidateOrder:

    def test_the_source_decides_first(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.SEARCH,
            [_video("search1", media_id, source=VideoSource.SEARCH)],
        )
        video_manager.replace_source_rows(
            media_id, VideoSource.ARR, [_video("arr1", media_id, source=VideoSource.ARR)]
        )
        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("tmdb1", media_id)]
        )
        video_manager.add_user_video(media_id, "user1")

        order = [v.video_id for v in video_manager.read_candidates(media_id)]
        assert order == ["user1", "tmdb1", "arr1", "search1"]

    def test_the_sequence_decides_inside_one_source(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video("third", media_id, sequence=2),
                _video("first", media_id, sequence=0),
                _video("second", media_id, sequence=1),
            ],
        )
        order = [v.video_id for v in video_manager.read_candidates(media_id)]
        assert order == ["first", "second", "third"]

    def test_the_language_of_the_profile_comes_first(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video("en1", media_id, sequence=0, language="en"),
                _video("de1", media_id, sequence=1, language="de"),
                _video("none1", media_id, sequence=2, language=None),
            ],
        )
        order = [
            v.video_id for v in video_manager.read_candidates(media_id, language="de")
        ]
        # The asked language first, then the row with no language, then
        # English, then the rest. Nothing is dropped: a trailer in another
        # language is better than no trailer.
        assert order[0] == "de1"
        assert set(order) == {"en1", "de1", "none1"}

    def test_the_source_still_wins_when_a_language_is_asked_for(self, media_id):
        """A USER row carries no language, because a person pasted a link.
        Ordering by language across sources therefore let a TMDB trailer in
        the asked language beat the video the user chose. The source
        decides first, and the language orders inside one source."""
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("tmdb_en", media_id, language="en")],
        )
        video_manager.add_user_video(media_id, "user_pick")

        order = [
            v.video_id
            for v in video_manager.read_candidates(media_id, language="en")
        ]
        assert order == ["user_pick", "tmdb_en"]

    def test_a_season_video_is_not_a_candidate_for_the_movie(self, media_id):
        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("s1", media_id)], season=1
        )
        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("main", media_id)]
        )
        assert [v.video_id for v in video_manager.read_candidates(media_id)] == [
            "main"
        ]
        assert [
            v.video_id for v in video_manager.read_candidates(media_id, season=1)
        ] == ["s1"]
