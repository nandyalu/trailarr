"""The TMDB API client.

Trailarr asks TMDB which videos belong to a movie or a series, so that it
downloads the trailer the studio published instead of the first result of a
YouTube search.

TMDB answers with English videos only unless it is asked otherwise: the
videos endpoint defaults to `language=en-US`. Measured against the live
API, /movie/603/videos returns 4 trailers, all English, and the same call
with `include_video_language=it,de,fr,en,null` returns 8 — the Italian,
German and French ones as well.

So the client sends `include_video_language`, built from the languages the
profiles ask for plus English and `null` (a video with no language). One
call then covers every profile that matches the item, whatever language
each asks for. The parameter is not in the current TMDB reference, but it
works; without it the trailer language of a profile could never do
anything.

The key: TMDB gives an account two credentials. The older one is an API key
of 32 characters, which goes in the query. The newer one is a read access
token, which goes in an Authorization header. This client accepts both, and
chooses by the shape of the value.
"""

import asyncio
from typing import Any

import aiohttp

from app_logger import ModuleLogger
from exceptions import ConnectionTimeoutError, InvalidResponseError
from services.tmdb.models import TMDBVideo

logger = ModuleLogger("TMDBAPI")

BASE_URL = "https://api.themoviedb.org/3"
_TIMEOUT = aiohttp.ClientTimeout(total=30)
# TMDB answers 429 when a client asks too fast. It sends Retry-After, and
# this client waits that long, three times, before it gives up.
_MAX_RETRIES = 3
_DEFAULT_RETRY_WAIT = 2.0


class TMDBAuthError(Exception):
    """The key that TMDB got is not valid. Raised for 401 and 403."""


def _is_read_access_token(key: str) -> bool:
    """A read access token is a JSON web token: three parts, dot separated."""
    return key.count(".") == 2 and key.startswith("ey")


class TMDBAPI:
    """Async HTTP client for the TMDB API."""

    def __init__(self, api_key: str):
        """
        Args:
            api_key (str): The API key or the read access token of the user.
        """
        self.api_key = (api_key or "").strip()
        # One run of a task asks about many media items, and a series and
        # its seasons repeat calls. The cache holds the answers of this
        # client only, and the client lives for one run.
        self._cache: dict[str, Any] = {}

    @property
    def configured(self) -> bool:
        """True when a key is set. No key means Trailarr makes no call."""
        return bool(self.api_key)

    def _auth(self) -> tuple[dict[str, str], dict[str, str]]:
        """Give back the headers and the query parameters for the key."""
        headers = {"Accept": "application/json"}
        params: dict[str, str] = {}
        if _is_read_access_token(self.api_key):
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            params["api_key"] = self.api_key
        return headers, params

    async def _get(self, path: str) -> dict[str, Any]:
        """Ask TMDB for one path and give back the answer.

        Args:
            path (str): The path after the version, such as 'movie/603/videos'.

        Returns:
            dict[str, Any]: The answer of TMDB.

        Raises:
            TMDBAuthError: If TMDB refuses the key.
            InvalidResponseError: If TMDB answers something else than JSON,
                or answers an error that a retry cannot fix.
            ConnectionTimeoutError: If TMDB does not answer in time.
        """
        if path in self._cache:
            return self._cache[path]
        headers, params = self._auth()
        # `path` may already carry a query, which urljoin-free formatting
        # keeps, and the cache key is the whole path so two languages do
        # not share an answer.
        url = f"{BASE_URL}/{path.lstrip('/')}"
        wait = _DEFAULT_RETRY_WAIT
        for attempt in range(_MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status in (401, 403):
                            raise TMDBAuthError(
                                "TMDB refused the key. Check the TMDB API key"
                                " in Settings."
                            )
                        if response.status == 429:
                            wait = _retry_after(response.headers, wait)
                            logger.warning(
                                "TMDB asked Trailarr to send fewer requests."
                                f" Trailarr waits {wait:.0f} seconds."
                            )
                            await asyncio.sleep(wait)
                            wait *= 2
                            continue
                        if response.status == 404:
                            # The movie or series is not in TMDB. That is an
                            # answer, not a failure.
                            self._cache[path] = {}
                            return {}
                        if response.status != 200:
                            text = (await response.text())[:200]
                            raise InvalidResponseError(
                                f"TMDB answered {response.status} for"
                                f" '{path}': {text}"
                            )
                        data = await response.json()
            except aiohttp.ServerTimeoutError as e:
                raise ConnectionTimeoutError(
                    "TMDB did not answer in time."
                ) from e
            except asyncio.TimeoutError as e:
                raise ConnectionTimeoutError(
                    "TMDB did not answer in time."
                ) from e
            except aiohttp.ClientError as e:
                raise InvalidResponseError(
                    f"Trailarr cannot reach TMDB: {e}"
                ) from e
            self._cache[path] = data
            return data
        raise InvalidResponseError(
            "TMDB asked Trailarr to send fewer requests, and it still did"
            f" after {_MAX_RETRIES} tries."
        )

    async def get_videos(
        self,
        tmdb_id: int,
        *,
        is_movie: bool,
        season: int | None = None,
        languages: list[str] | None = None,
    ) -> list[TMDBVideo]:
        """Get the videos that TMDB lists for one movie, series or season.

        Args:
            tmdb_id (int): The id of the movie or series at TMDB.
            is_movie (bool): True for a movie, False for a series.
            season (int | None): The season number, for a season video list.
            languages (list[str] | None): The languages the profiles ask
                for. English and videos with no language always come back
                as well, so one call serves every profile.

        Returns:
            list[TMDBVideo]: Every YouTube video that TMDB lists, in the
                order TMDB gave. An unknown id gives an empty list.
        """
        if not self.configured or not tmdb_id:
            return []
        kind = "movie" if is_movie else "tv"
        if season is not None:
            path = f"tv/{tmdb_id}/season/{season}/videos"
        else:
            path = f"{kind}/{tmdb_id}/videos"
        path = f"{path}?include_video_language={video_languages(languages)}"
        data = await self._get(path)
        results = data.get("results") or []
        videos: list[TMDBVideo] = []
        for entry in results:
            try:
                video = TMDBVideo.model_validate(entry)
            except Exception:
                logger.debug(
                    f"TMDB sent a video that Trailarr cannot read: {entry}"
                )
                continue
            if video.is_youtube:
                videos.append(video)
        return videos

    async def validate_key(self) -> str:
        """Check the key with one cheap call.

        Returns:
            str: A message to show the user.

        Raises:
            TMDBAuthError: If TMDB refuses the key.
            InvalidResponseError: If TMDB answers something unexpected.
        """
        if not self.configured:
            raise TMDBAuthError("Enter a TMDB API key first.")
        data = await self._get("configuration")
        if not data.get("images"):
            raise InvalidResponseError(
                "TMDB answered, but not with its configuration."
            )
        return "TMDB key accepted."


def _retry_after(headers, fallback: float) -> float:
    """Read the Retry-After header that TMDB sends with a 429."""
    value = headers.get("Retry-After")
    if not value:
        return fallback
    try:
        return max(1.0, float(value))
    except (TypeError, ValueError):
        return fallback


def video_languages(languages: list[str] | None) -> str:
    """Build the `include_video_language` value.

    English and `null` are always included: English because most trailers
    are English and a profile asking for Italian still wants something when
    Italian is missing, and `null` because TMDB marks some videos with no
    language at all.

    Args:
        languages (list[str] | None): The languages profiles ask for.

    Returns:
        str: The comma-separated value for the query.
    """
    wanted = [
        code.strip().lower() for code in (languages or []) if code.strip()
    ]
    # dict.fromkeys keeps the order and drops the repeats.
    return ",".join(dict.fromkeys([*wanted, "en", "null"]))
