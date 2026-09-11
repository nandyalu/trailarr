"""Tests for the trailer resolver — plans/phase-08-tmdb.md decision 4.

The order is the promise of Phase 8: what the user chose beats the TMDB
list, which beats the id from Radarr or Sonarr, which beats a result a
search stored earlier.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from database.models.mediavideo import MediaVideoRead, VideoSource
from database.models.trailerprofile import TrailerProfileRead
from services.trailers.resolver import choose_candidates, describe_choice


def _candidate(video_id: str, source: VideoSource, sequence: int = 0):
    now = datetime.now(timezone.utc)
    return MediaVideoRead(
        id=abs(hash(video_id)) % 100000,
        media_id=1,
        video_id=video_id,
        source=source,
        season=None,
        video_type="trailer",
        sequence=sequence,
        language="en",
        name=video_id,
        official=True,
        published_at=None,
        added_at=now,
        updated_at=now,
    )


def _profile(always_search=False):
    profile = MagicMock(spec=TrailerProfileRead)
    profile.always_search = always_search
    return profile


ORDERED = [
    _candidate("user1", VideoSource.USER),
    _candidate("tmdb1", VideoSource.TMDB),
    _candidate("arr1", VideoSource.ARR),
    _candidate("search1", VideoSource.SEARCH),
]


class TestChooseCandidates:

    def test_the_order_of_the_sources_is_kept(self):
        chosen = choose_candidates(ORDERED, _profile())
        assert [c.video_id for c in chosen] == [
            "user1", "tmdb1", "arr1", "search1"
        ]

    def test_an_excluded_video_is_not_offered(self):
        """The trailer already on disk must not be downloaded again."""
        chosen = choose_candidates(ORDERED, _profile(), exclude=["user1"])
        assert [c.video_id for c in chosen] == ["tmdb1", "arr1", "search1"]

    def test_always_search_drops_only_the_stored_search_result(self):
        """The pitfall in the plan: `Always Search` used to mean 'ignore
        the stored id'. It now means 'do not reuse what a search found',
        and it never throws away the choice of the user or the TMDB list."""
        chosen = choose_candidates(ORDERED, _profile(always_search=True))
        assert [c.video_id for c in chosen] == ["user1", "tmdb1", "arr1"]

    def test_the_video_of_the_last_attempt_goes_last(self):
        """Wargame W5: the video may be gone from YouTube, so try the
        others first — but keep it, because the failure may have been the
        network."""
        chosen = choose_candidates(ORDERED, _profile(), last_tried="user1")
        assert [c.video_id for c in chosen] == [
            "tmdb1", "arr1", "search1", "user1"
        ]

    def test_nothing_to_try_gives_an_empty_list(self):
        chosen = choose_candidates([], _profile())
        assert chosen == []

    def test_everything_excluded_gives_an_empty_list(self):
        chosen = choose_candidates(
            ORDERED, _profile(), exclude=["user1", "tmdb1", "arr1", "search1"]
        )
        assert chosen == []


class TestDescribeChoice:

    def test_the_log_line_names_the_source(self):
        """The exit criterion: a log line proves TMDB is being preferred."""
        media = MagicMock(title="The Matrix", id=1)
        line = describe_choice(media, _candidate("tmdb1", VideoSource.TMDB))
        assert "The Matrix" in line
        assert "TMDB" in line
        assert "tmdb1" in line

    def test_each_source_reads_differently(self):
        media = MagicMock(title="The Matrix", id=1)
        lines = {
            source: describe_choice(media, _candidate("v", source))
            for source in VideoSource
        }
        assert len(set(lines.values())) == len(VideoSource)
