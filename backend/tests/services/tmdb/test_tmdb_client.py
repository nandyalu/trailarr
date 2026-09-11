"""Tests for the TMDB client and the mapping to candidate rows.

The recorded payloads below are trimmed copies of real answers from
api.themoviedb.org (movie 603, The Matrix), so the shapes are the ones
TMDB really sends, including the mixed video types and the trailer that
is not official.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models.mediavideo import VideoSource
from exceptions import InvalidResponseError
from services.tmdb.api_manager import TMDBAPI, TMDBAuthError, _is_read_access_token
from services.tmdb.models import TMDBVideo
from services.tmdb.videos import to_candidates

MATRIX_PAYLOAD = {
    "id": 603,
    "results": [
        {
            "iso_639_1": "en", "iso_3166_1": "US",
            "name": "How KEANU REEVES prepared", "key": "w-efbYj1YHA",
            "site": "YouTube", "size": 1080, "type": "Featurette",
            "official": True, "published_at": "2024-09-11T14:00:11.000Z",
            "id": "66e1a1",
        },
        {
            "iso_639_1": "en", "iso_3166_1": "US",
            "name": "Official 25th Anniversary Trailer #3", "key": "FVI84Dfx2-I",
            "site": "YouTube", "size": 1080, "type": "Trailer",
            "official": True, "published_at": "2024-08-01T16:00:10.000Z",
            "id": "66ab2c",
        },
        {
            "iso_639_1": "en", "iso_3166_1": "US",
            "name": "Fan cut trailer", "key": "unofficial1",
            "site": "YouTube", "size": 1080, "type": "Trailer",
            "official": False, "published_at": "2010-01-01T00:00:00.000Z",
            "id": "aaa111",
        },
        {
            "iso_639_1": "de", "iso_3166_1": "DE",
            "name": "Deutscher Trailer", "key": "german1",
            "site": "YouTube", "size": 1080, "type": "Trailer",
            "official": True, "published_at": "2024-08-02T16:00:10.000Z",
            "id": "bbb222",
        },
        {
            "iso_639_1": "en", "iso_3166_1": "US",
            "name": "Not on YouTube", "key": "vimeo1",
            "site": "Vimeo", "size": 1080, "type": "Trailer",
            "official": True, "published_at": None, "id": "ccc333",
        },
    ],
}


def _response(status=200, payload=None, headers=None):
    response = MagicMock()
    response.status = status
    response.headers = headers or {}
    response.json = AsyncMock(return_value=payload or {})
    response.text = AsyncMock(return_value="")
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


def _session_with(*responses):
    """Patch aiohttp.ClientSession so each call gets the next response."""
    session = MagicMock()
    session.get = MagicMock(side_effect=list(responses))
    holder = MagicMock()
    holder.__aenter__ = AsyncMock(return_value=session)
    holder.__aexit__ = AsyncMock(return_value=False)
    return patch("aiohttp.ClientSession", return_value=holder), session


class TestKeyKinds:
    def test_a_32_character_key_goes_in_the_query(self):
        api = TMDBAPI("7cd673aa4e20351ed73609dd49d199eb")
        headers, params = api._auth()
        assert params["api_key"] == "7cd673aa4e20351ed73609dd49d199eb"
        assert "Authorization" not in headers

    def test_a_read_access_token_goes_in_the_header(self):
        token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJ4In0.signature"
        assert _is_read_access_token(token)
        api = TMDBAPI(token)
        headers, params = api._auth()
        assert headers["Authorization"] == f"Bearer {token}"
        assert params == {}

    def test_no_key_means_no_call(self):
        api = TMDBAPI("")
        assert api.configured is False


class TestGetVideos:
    @pytest.mark.asyncio
    async def test_only_youtube_videos_come_back(self):
        """Wargame W3: TMDB also lists Vimeo."""
        patcher, _ = _session_with(_response(payload=MATRIX_PAYLOAD))
        with patcher:
            videos = await TMDBAPI("key").get_videos(603, is_movie=True)
        assert "vimeo1" not in {v.key for v in videos}
        assert len(videos) == 4

    @pytest.mark.asyncio
    async def test_an_unknown_id_is_an_answer_not_a_failure(self):
        patcher, _ = _session_with(_response(status=404))
        with patcher:
            videos = await TMDBAPI("key").get_videos(99999999, is_movie=True)
        assert videos == []

    @pytest.mark.asyncio
    async def test_a_refused_key_raises(self):
        """Wargame W1: the caller disables TMDB for the run."""
        patcher, _ = _session_with(_response(status=401))
        with patcher:
            with pytest.raises(TMDBAuthError):
                await TMDBAPI("bad").get_videos(603, is_movie=True)

    @pytest.mark.asyncio
    async def test_the_client_waits_and_retries_after_a_429(self):
        """Wargame W4: TMDB asks for fewer requests."""
        patcher, session = _session_with(
            _response(status=429, headers={"Retry-After": "1"}),
            _response(payload=MATRIX_PAYLOAD),
        )
        with patcher:
            with patch("asyncio.sleep", new=AsyncMock()) as slept:
                videos = await TMDBAPI("key").get_videos(603, is_movie=True)
        assert len(videos) == 4
        assert session.get.call_count == 2
        slept.assert_awaited_once()
        assert slept.await_args.args[0] == 1.0

    @pytest.mark.asyncio
    async def test_a_server_error_is_reported(self):
        patcher, _ = _session_with(_response(status=500))
        with patcher:
            with pytest.raises(InvalidResponseError):
                await TMDBAPI("key").get_videos(603, is_movie=True)

    @pytest.mark.asyncio
    async def test_the_same_path_is_asked_only_once_per_run(self):
        patcher, session = _session_with(_response(payload=MATRIX_PAYLOAD))
        with patcher:
            api = TMDBAPI("key")
            await api.get_videos(603, is_movie=True)
            await api.get_videos(603, is_movie=True)
        assert session.get.call_count == 1

    @pytest.mark.asyncio
    async def test_no_key_makes_no_call(self):
        """Wargame W8."""
        patcher, session = _session_with(_response(payload=MATRIX_PAYLOAD))
        with patcher:
            videos = await TMDBAPI("").get_videos(603, is_movie=True)
        assert videos == []
        assert session.get.call_count == 0

    @pytest.mark.asyncio
    async def test_a_series_asks_the_tv_path(self):
        patcher, session = _session_with(_response(payload={"results": []}))
        with patcher:
            await TMDBAPI("key").get_videos(1399, is_movie=False)
        assert "tv/1399/videos" in session.get.call_args.args[0]

    @pytest.mark.asyncio
    async def test_a_season_asks_the_season_path(self):
        patcher, session = _session_with(_response(payload={"results": []}))
        with patcher:
            await TMDBAPI("key").get_videos(1399, is_movie=False, season=2)
        assert "tv/1399/season/2/videos" in session.get.call_args.args[0]


class TestToCandidates:
    def _videos(self):
        return [
            TMDBVideo.model_validate(entry)
            for entry in MATRIX_PAYLOAD["results"]
            if entry["site"] == "YouTube"
        ]

    def test_only_trailers_become_rows(self):
        """Phase 8 downloads trailers; Phase 9 adds the other types."""
        rows = to_candidates(self._videos(), media_id=7)
        assert {r.video_id for r in rows} == {
            "FVI84Dfx2-I", "unofficial1", "german1"
        }
        assert all(r.video_type == "trailer" for r in rows)
        assert all(r.source == VideoSource.TMDB for r in rows)

    def test_an_official_trailer_comes_before_one_that_is_not(self):
        """Real data: the first Inception trailer in TMDB order is not
        official, while two official ones follow it."""
        rows = to_candidates(self._videos(), media_id=7)
        assert [r.video_id for r in rows] == [
            "FVI84Dfx2-I",  # official, first in TMDB order
            "german1",  # official, later in TMDB order
            "unofficial1",  # not official, so last
        ]
        assert [r.sequence for r in rows] == [0, 1, 2]

    def test_the_language_and_the_title_are_kept(self):
        rows = {r.video_id: r for r in to_candidates(self._videos(), media_id=7)}
        assert rows["german1"].language == "de"
        assert rows["FVI84Dfx2-I"].name == "Official 25th Anniversary Trailer #3"
        assert rows["FVI84Dfx2-I"].published_at is not None

    def test_a_title_with_no_trailer_gives_no_rows(self):
        featurettes = [v for v in self._videos() if v.type == "Featurette"]
        assert to_candidates(featurettes, media_id=7) == []

    def test_a_season_list_carries_the_season(self):
        rows = to_candidates(self._videos(), media_id=7, season=3)
        assert all(r.season == 3 for r in rows)
