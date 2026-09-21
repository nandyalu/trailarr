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
            [
                _video("aaa", media_id, sequence=0),
                _video("bbb", media_id, sequence=1),
            ],
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
            media_id,
            VideoSource.ARR,
            [_video("arr1", media_id, source=VideoSource.ARR)],
        )
        video_manager.add_user_video(media_id, "user1")

        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("tmdb1", media_id)]
        )
        # An empty TMDB list removes only the TMDB row.
        video_manager.replace_source_rows(media_id, VideoSource.TMDB, [])

        remaining = {
            v.video_id: v.source
            for v in video_manager.read_for_media(media_id)
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
        """Wargame W6: (media_id, video_id) is unique, so one row.

        The better source takes it. On a real library, most of the ids that
        Radarr and Sonarr report are the trailer TMDB lists, and leaving
        the row with the Arr showed a row with no title and sorted the
        agreed trailer below TMDB's others."""
        video_manager.replace_source_rows(
            media_id,
            VideoSource.ARR,
            [_video("same", media_id, source=VideoSource.ARR)],
        )
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("same", media_id, name="Official Trailer", language="de")],
        )
        rows = video_manager.read_for_media(media_id)
        assert len(rows) == 1
        assert rows[0].source == VideoSource.TMDB
        # And it carries what TMDB knows, which an Arr never reports.
        assert rows[0].name == "Official Trailer"
        assert rows[0].language == "de"

    def test_a_worse_source_does_not_take_the_row(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("same", media_id, name="From TMDB")],
        )
        video_manager.replace_source_rows(
            media_id,
            VideoSource.ARR,
            [_video("same", media_id, source=VideoSource.ARR)],
        )
        rows = video_manager.read_for_media(media_id)
        assert len(rows) == 1
        assert rows[0].source == VideoSource.TMDB
        assert rows[0].name == "From TMDB"

    def test_no_source_takes_the_video_the_user_chose(self, media_id):
        """The invariant of decision 5b."""
        video_manager.add_user_video(media_id, "mine")
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("mine", media_id, name="TMDB name")],
        )
        rows = video_manager.read_for_media(media_id)
        assert len(rows) == 1
        assert rows[0].source == VideoSource.USER

        # And the TMDB refresh that follows cannot remove it either.
        video_manager.replace_source_rows(media_id, VideoSource.TMDB, [])
        assert len(video_manager.read_for_media(media_id)) == 1


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
        assert [
            v.video_id for v in video_manager.read_for_media(media_id)
        ] == ["shared"]

    def test_relabelling_an_arr_row_as_the_choice_of_the_user(self, media_id):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.ARR,
            [_video("hand", media_id, source=VideoSource.ARR)],
        )
        assert video_manager.relabel_as_user(media_id, "hand") is True
        assert (
            video_manager.read_for_media(media_id)[0].source
            == VideoSource.USER
        )
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
            media_id,
            VideoSource.ARR,
            [_video("arr1", media_id, source=VideoSource.ARR)],
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

    def test_only_the_asked_language_comes_back(self, media_id):
        """A language is a filter, not an order: a profile that asks for
        German gets the German trailer or nothing, never the English one.
        Downloading the wrong language is the pain this feature removes."""
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video("en1", media_id, sequence=0, language="en"),
                _video("de1", media_id, sequence=1, language="de"),
                _video("none1", media_id, sequence=2, language=None),
            ],
        )

        assert [
            v.video_id
            for v in video_manager.read_candidates(media_id, language="de")
        ] == ["de1"]
        # Nothing recorded in French, so nothing comes back and the caller
        # searches instead.
        assert video_manager.read_candidates(media_id, language="fr") == []
        # No language asked for: everything, in source order.
        assert len(video_manager.read_candidates(media_id)) == 3

    def test_the_source_still_decides_among_videos_of_one_language(
        self, media_id
    ):
        """Filtering by language must not disturb the source order."""
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [_video("tmdb_en", media_id, language="en")],
        )
        video_manager.add_user_video(media_id, "user_pick", language="en")

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
        assert [
            v.video_id for v in video_manager.read_candidates(media_id)
        ] == ["main"]
        assert [
            v.video_id
            for v in video_manager.read_candidates(media_id, season=1)
        ] == ["s1"]


def _connection_of(media_id: int) -> int:
    return media_manager.read(media_id).connection_id


class TestMediaDeletion:
    """Wargame W7: the rows of a deleted media item go with it.

    The foreign key says CASCADE, but SQLite enforces a foreign key only
    when `PRAGMA foreign_keys` is on for the connection. If it is off, the
    rows stay behind and point at a media item that no longer exists.
    """

    def test_deleting_the_media_removes_its_videos(self, media_id):
        video_manager.add_user_video(media_id, "goes_away")
        video_manager.replace_source_rows(
            media_id, VideoSource.TMDB, [_video("also_goes", media_id)]
        )
        assert len(video_manager.read_for_media(media_id)) == 2

        media_manager.delete_except(_connection_of(media_id), [])

        assert video_manager.read_for_media(media_id) == []


class TestLanguageFilter:
    """Wargame W2, re-decided: a language is a filter, and the fallback is
    a YouTube search rather than a trailer in a language nobody asked for.

    A profile writes its own search query, so a user who wants Italian can
    aim the search at Italian — which is a better answer than a German
    trailer.
    """

    CASES = [
        ([("de1", "de"), ("en1", "en")], "de", ["de1"], "the asked language"),
        (
            [("en1", "en"), ("fr1", "fr")],
            "de",
            [],
            "no German: search instead",
        ),
        ([("none1", None)], "de", [], "an unknown language is not German"),
        ([("en1", "en"), ("fr1", "fr")], "", ["en1", "fr1"], "any language"),
    ]

    @pytest.mark.parametrize("offered,asked,expected,reason", CASES)
    def test_the_filter(self, media_id, offered, asked, expected, reason):
        video_manager.replace_source_rows(
            media_id,
            VideoSource.TMDB,
            [
                _video(video_id, media_id, sequence=index, language=language)
                for index, (video_id, language) in enumerate(offered)
            ],
        )

        chosen = video_manager.read_candidates(media_id, language=asked)

        assert [c.video_id for c in chosen] == expected, reason
