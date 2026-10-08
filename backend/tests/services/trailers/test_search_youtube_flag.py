"""The Search YouTube flag in the resolver and the API — Phase 9, decision
5 as amended on Oct 8, 2026.

With the flag off a profile takes known videos only and waits for TMDB.
With it on, a profile of any type searches when no known video suits it.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.trailers import trailer_search


def _profile(video_type: str, search_youtube: bool) -> MagicMock:
    profile = MagicMock()
    profile.id = 1
    profile.video_type = video_type
    profile.search_youtube = search_youtube
    profile.always_search = False
    profile.language = ""
    profile.customfilter.filter_name = "Test Profile"
    return profile


@pytest.fixture
def media() -> MagicMock:
    media = MagicMock()
    media.id = 1
    media.title = "Test Movie"
    return media


class TestResolver:
    def _run(self, media, profile):
        with (
            patch.object(
                trailer_search.video_manager, "read_candidates", return_value=[]
            ),
            patch.object(
                trailer_search, "_last_tried_video_id", return_value=None
            ),
            patch.object(
                trailer_search, "search_yt_for_trailer", return_value="found1"
            ) as search,
            patch.object(trailer_search, "_remember_search_result"),
        ):
            video_id = trailer_search.get_video_id(media, profile, [])
        return video_id, search

    def test_search_off_waits_for_tmdb(self, media):
        video_id, search = self._run(media, _profile("trailer", False))
        assert video_id is None
        search.assert_not_called()

    def test_search_on_searches_for_a_trailer(self, media):
        video_id, search = self._run(media, _profile("trailer", True))
        assert video_id == "found1"
        search.assert_called_once()

    def test_a_featurette_profile_searches_when_the_flag_is_on(self, media):
        video_id, search = self._run(media, _profile("featurette", True))
        assert video_id == "found1"
        search.assert_called_once()

    def test_a_featurette_profile_waits_when_the_flag_is_off(self, media):
        video_id, search = self._run(media, _profile("featurette", False))
        assert video_id is None
        search.assert_not_called()


class TestSearchEndpoint:
    @pytest.mark.asyncio
    async def test_refuses_a_profile_with_the_search_off(self):
        from fastapi import HTTPException

        from api.v1 import media as media_api

        with (
            patch.object(media_api.media_manager, "read", return_value=MagicMock()),
            patch.object(
                media_api.trailerprofile,
                "get_trailerprofile",
                return_value=_profile("trailer", False),
            ),
            patch.object(media_api.trailer_search, "search_yt_for_trailer") as search,
        ):
            with pytest.raises(HTTPException) as exc:
                await media_api.search_for_trailer(1, 1)
        assert exc.value.status_code == 409
        assert "Search YouTube is off" in exc.value.detail
        search.assert_not_called()


class TestTheSearchResultTakesTheTypeOfTheProfile:
    """Code review of Phase 9, finding 2: a search made for a featurette
    profile is stored as a SEARCH featurette, not as a trailer, so the
    profile reads its own result back and a trailer profile never takes
    it."""

    def test_the_resolver_stores_the_result_with_the_type(self, media):
        with (
            patch.object(
                trailer_search.video_manager, "read_candidates", return_value=[]
            ),
            patch.object(
                trailer_search, "_last_tried_video_id", return_value=None
            ),
            patch.object(
                trailer_search, "search_yt_for_trailer", return_value="feat1"
            ),
            patch.object(
                trailer_search.video_manager, "replace_source_rows"
            ) as replace,
        ):
            trailer_search.get_video_id(media, _profile("featurette", True), [])

        replace.assert_called_once()
        args, kwargs = replace.call_args
        assert kwargs["video_type"] == "featurette"
        [row] = args[2]
        assert (row.video_id, row.video_type) == ("feat1", "featurette")

    def test_the_default_is_still_a_trailer(self, media):
        with patch.object(
            trailer_search.video_manager, "replace_source_rows"
        ) as replace:
            trailer_search._remember_search_result(media, "t1")
        assert replace.call_args.kwargs["video_type"] == "trailer"

    @pytest.mark.asyncio
    async def test_the_endpoint_takes_the_old_id_of_the_same_type(self):
        from api.v1 import media as media_api

        found = MagicMock()
        found.id = 1
        found.title = "Test Movie"
        with (
            patch.object(media_api.media_manager, "read", return_value=found),
            patch.object(
                media_api.trailerprofile,
                "get_trailerprofile",
                return_value=_profile("featurette", True),
            ),
            patch.object(
                media_api.trailer_search,
                "search_yt_for_trailer",
                return_value="feat2",
            ),
            patch.object(
                media_api.media_service, "first_video_id", return_value="feat1"
            ) as first,
            patch.object(
                media_api.trailer_search, "_remember_search_result"
            ) as remember,
            patch.object(
                media_api.event_manager, "track_youtube_id_changed"
            ) as track,
            patch.object(
                media_api.websockets.ws_manager, "broadcast", new=AsyncMock()
            ),
        ):
            assert await media_api.search_for_trailer(1, 1) == "feat2"

        first.assert_called_once_with(1, "featurette")
        remember.assert_called_once_with(found, "feat2", video_type="featurette")
        assert track.call_args.kwargs["old_yt_id"] == "feat1"
