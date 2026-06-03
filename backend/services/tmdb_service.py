"""TMDB service — pre-cache TMDB video IDs for all monitored media.

Iterates all monitored media that have a tmdb_id, fetches every available
TMDB video across the configured languages and seasons, and upserts the
results into the VideoId table. The download pipeline then reads from the
cache instead of making live TMDB calls for most requests.
"""

import asyncio
import threading

import aiohttp

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.media import MediaRead
import db.repos.media as media_repo
import db.repos.trailer_profile as trailer_profile_repo
import db.repos.video_id as video_id_repo

logger = ModuleLogger("TMDBService")

_TMDB_BASE = "https://api.themoviedb.org/3"
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
_SLEEP_BETWEEN_REQUESTS = 0.25  # normal pacing between media items
_RATE_LIMIT_BASE = 60.0         # seconds to wait on first 429
_RATE_LIMIT_MAX = 600.0         # cap at 10 minutes


async def _fetch_tmdb_videos(
    session: aiohttp.ClientSession,
    tmdb_id: str,
    is_movie: bool,
    season: int,
    api_key: str,
    language: str = "",
) -> list[dict] | None:
    """Fetch TMDB video results. Returns None on 429, [] on 404/error, list on success."""
    if is_movie:
        url = f"{_TMDB_BASE}/movie/{tmdb_id}/videos"
    elif season > 0:
        url = f"{_TMDB_BASE}/tv/{tmdb_id}/season/{season}/videos"
    else:
        url = f"{_TMDB_BASE}/tv/{tmdb_id}/videos"
    params = {"api_key": api_key, "language": language or "en-US"}
    try:
        async with session.get(
            url, params=params, timeout=_REQUEST_TIMEOUT
        ) as resp:
            if resp.status == 429:
                return None
            if resp.status == 404:
                return []
            if resp.status != 200:
                logger.warning(
                    f"TMDB returned HTTP {resp.status} for"
                    f" {'movie' if is_movie else 'tv'}/{tmdb_id}"
                    f" (season={season})"
                )
                return []
            data = await resp.json()
            return data.get("results", [])
    except asyncio.TimeoutError:
        logger.warning(
            "TMDB request timed out for"
            f" {'movie' if is_movie else 'tv'}/{tmdb_id}"
        )
        return []
    except aiohttp.ClientError as exc:
        logger.warning(f"TMDB request failed: {exc}")
        return []


def _find_youtube_key(results: list[dict], video_type: str) -> str | None:
    target = video_type.lower()
    for r in results:
        if (
            r.get("site", "").lower() == "youtube"
            and (r.get("type") or "").lower() == target
        ):
            return r.get("key")
    return None


def _get_seasons_to_fetch(media: MediaRead, has_season_profile: bool) -> list[int]:
    if media.is_movie:
        return [0]
    if not has_season_profile or not media.season_count:
        return [0]
    return [0] + list(range(1, media.season_count + 1))


async def _cache_media_tmdb_videos(
    http_session: aiohttp.ClientSession,
    media: MediaRead,
    api_key: str,
    languages: list[str],
    has_season_profile: bool,
    rate_limit_sleep: float,
) -> tuple[int, float]:
    """Fetch all TMDB videos for one media item and upsert to VideoId table.

    Returns (videos_cached, updated_rate_limit_sleep).
    """
    seasons = _get_seasons_to_fetch(media, has_season_profile)
    cached = 0

    for language in languages:
        for season in seasons:
            results = await _fetch_tmdb_videos(
                http_session, media.tmdb_id, media.is_movie, season, api_key, language
            )
            if results is None:
                # 429 — wait, double the backoff, retry once
                logger.warning(
                    f"TMDB rate-limited for media {media.id}"
                    f" (lang='{language}', season={season})."
                    f" Waiting {rate_limit_sleep:.0f}s before retry."
                )
                await asyncio.sleep(rate_limit_sleep)
                rate_limit_sleep = min(rate_limit_sleep * 2, _RATE_LIMIT_MAX)
                results = await _fetch_tmdb_videos(
                    http_session, media.tmdb_id, media.is_movie, season, api_key, language
                )
                if results is None:
                    logger.warning(
                        f"TMDB still rate-limited for media {media.id}"
                        f" (lang='{language}', season={season}) — skipping combo."
                    )
                    continue

            for item in results:
                if item.get("site", "").lower() != "youtube":
                    continue
                youtube_id = item.get("key")
                video_type = (item.get("type") or "").lower()
                if not youtube_id or not video_type:
                    continue
                video_id_repo.upsert_tmdb(
                    media_id=media.id,  # type: ignore[arg-type]
                    video_type=video_type,
                    language=language,
                    season=season,
                    youtube_id=youtube_id,
                )
                cached += 1

    return cached, rate_limit_sleep


async def get_tmdb_youtube_key(
    media: MediaRead,
    video_type: str,
    season: int = 0,
    language: str = "",
) -> str | None:
    """Fetch the first matching YouTube key from TMDB for the given video_type and season.

    Used on-demand by the download pipeline when no cached VideoId is available.
    """
    api_key = app_settings.tmdb_api_key
    if not api_key or not media.tmdb_id:
        return None
    async with aiohttp.ClientSession() as session:
        results = await _fetch_tmdb_videos(
            session,
            media.tmdb_id,
            media.is_movie,
            season,
            api_key,
            language=language,
        )
    if results is None:
        return None
    return _find_youtube_key(results, str(video_type))


async def refresh_tmdb_videos(
    _stop_event: threading.Event | None = None,
) -> None:
    """Pre-cache TMDB video IDs for all monitored media with a tmdb_id.

    Iterates the full monitored media set, fetches all available videos from
    TMDB for each configured language and season, and upserts them into the
    VideoId table. Rate-limit responses (429) trigger exponential backoff
    starting at _RATE_LIMIT_BASE seconds, capped at _RATE_LIMIT_MAX.
    """
    api_key = app_settings.tmdb_api_key
    if not api_key:
        logger.warning(
            "TMDB API key is not configured — skipping TMDB video refresh."
            " Set TMDB_API_KEY in General Settings."
        )
        return

    cfg = trailer_profile_repo.get_tmdb_refresh_config()
    rate_limit_sleep = _RATE_LIMIT_BASE
    seen_ids: set[int] = set()
    processed = 0
    skipped = 0
    total_cached = 0
    errors = 0

    logger.info(
        f"TMDB refresh starting."
        f" Movie languages: {cfg.movie_languages},"
        f" Series languages: {cfg.series_languages},"
        f" Season profiles enabled: {cfg.has_season_profile}."
    )

    async with aiohttp.ClientSession() as http_session:
        for media in media_repo.read_all_generator(monitored_only=True):
            if _stop_event and _stop_event.is_set():
                logger.info("Stop event set — terminating TMDB refresh.")
                break

            if media.id in seen_ids:
                continue
            seen_ids.add(media.id)  # type: ignore[arg-type]

            if not media.tmdb_id:
                skipped += 1
                continue

            languages = cfg.movie_languages if media.is_movie else cfg.series_languages
            try:
                cached, rate_limit_sleep = await _cache_media_tmdb_videos(
                    http_session,
                    media,
                    api_key,
                    languages,
                    cfg.has_season_profile,
                    rate_limit_sleep,
                )
                total_cached += cached
                processed += 1
            except Exception as exc:
                logger.error(
                    f"Unexpected error fetching TMDB videos for media"
                    f" {media.id} ('{media.title}'): {exc}"
                )
                errors += 1

            await asyncio.sleep(_SLEEP_BETWEEN_REQUESTS)

    logger.info(
        "TMDB refresh complete."
        f" Processed: {processed},"
        f" Skipped (no tmdb_id): {skipped},"
        f" Videos cached: {total_cached},"
        f" Errors: {errors}."
    )
