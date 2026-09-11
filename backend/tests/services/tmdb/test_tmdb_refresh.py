"""Tests for the TMDB refresh service — plans/phase-08-tmdb.md wargames.

The rules here:
  - W8: no key means no call at all;
  - W1: a refused key turns TMDB off for the run instead of failing it;
  - decision 6: no TMDB id means no call, and the other sources still work;
  - decision 2: a refresh replaces the TMDB rows and no others;
  - a failure at TMDB never reaches the caller.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models.media import MediaRead
from services.tmdb.api_manager import TMDBAuthError
from services.tmdb.models import TMDBVideo
from services.tmdb.refresh import TMDBRefresher

PKG = "services.tmdb.refresh"


def _media(media_id=1, tmdb_id=603, is_movie=True, title="The Matrix"):
    media = MagicMock(spec=MediaRead)
    media.id = media_id
    media.tmdb_id = tmdb_id
    media.is_movie = is_movie
    media.title = title
    return media


def _trailer(key="abc", official=True, language="en"):
    return TMDBVideo(
        key=key, name="Official Trailer", site="YouTube", type="Trailer",
        official=official, iso_639_1=language,
    )


class TestRefresh:

    @pytest.mark.asyncio
    async def test_no_key_makes_no_call(self):
        """Wargame W8."""
        api = MagicMock(configured=False)
        api.get_videos = AsyncMock()
        refresher = TMDBRefresher(api)

        assert refresher.enabled is False
        assert await refresher.refresh_media(_media()) == 0
        api.get_videos.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_media_without_a_tmdb_id_is_skipped(self):
        """Decision 6: no /find backfill; the other sources still work."""
        api = MagicMock(configured=True)
        api.get_videos = AsyncMock()
        refresher = TMDBRefresher(api)

        assert await refresher.refresh_media(_media(tmdb_id=None)) == 0
        api.get_videos.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_the_trailers_are_stored_as_tmdb_rows(self):
        api = MagicMock(configured=True)
        api.get_videos = AsyncMock(return_value=[_trailer("aaa"), _trailer("bbb")])
        with patch(f"{PKG}.video_manager") as manager:
            manager.replace_source_rows.return_value = (2, 0, 0)
            count = await TMDBRefresher(api).refresh_media(_media())

        assert count == 2
        media_id, source, rows = manager.replace_source_rows.call_args.args
        assert media_id == 1
        assert source.value == "tmdb"
        assert [r.video_id for r in rows] == ["aaa", "bbb"]

    @pytest.mark.asyncio
    async def test_a_refused_key_turns_tmdb_off_for_the_run(self):
        """Wargame W1: the task keeps going with the other sources."""
        api = MagicMock(configured=True)
        api.get_videos = AsyncMock(side_effect=TMDBAuthError("bad key"))
        refresher = TMDBRefresher(api)

        assert await refresher.refresh_media(_media()) == 0
        assert refresher.enabled is False

        # The next media item makes no call at all.
        api.get_videos.reset_mock()
        assert await refresher.refresh_media(_media(media_id=2)) == 0
        api.get_videos.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_failure_at_tmdb_never_reaches_the_caller(self):
        api = MagicMock(configured=True)
        api.get_videos = AsyncMock(side_effect=OSError("network down"))
        refresher = TMDBRefresher(api)

        assert await refresher.refresh_media(_media()) == 0
        # One bad response is not a bad key: TMDB stays on for the others.
        assert refresher.enabled is True

    @pytest.mark.asyncio
    async def test_a_title_with_no_trailer_clears_its_tmdb_rows(self):
        """TMDB lists videos, but no trailer: the TMDB rows go away and
        the rows of the other sources stay."""
        api = MagicMock(configured=True)
        api.get_videos = AsyncMock(return_value=[])
        with patch(f"{PKG}.video_manager") as manager:
            manager.replace_source_rows.return_value = (0, 0, 3)
            count = await TMDBRefresher(api).refresh_media(_media())

        assert count == 0
        assert manager.replace_source_rows.call_args.args[2] == []
