"""TMDB service — check video availability and update trailer-status rows.

Fetches TMDB video metadata for PENDING/NOT_AVAILABLE rows and either
updates the YouTube ID on the Media record (for Trailer type) or flips
the row status between PENDING and NOT_AVAILABLE (for other video types).
"""

import asyncio
import threading
from collections import defaultdict

import aiohttp

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.media import MediaRead
from db.models.mediatrailerstatus import TrailerStatusEnum
from db.models.trailerprofile import VideoType
import db.repos.media as media_repo
import db.repos.trailer_status as trailer_status_repo
from db.repos.trailer_status import TmdbPendingRow

logger = ModuleLogger("TMDBService")

_TMDB_BASE = "https://api.themoviedb.org/3"
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
_SLEEP_BETWEEN_REQUESTS = 0.5


async def _fetch_tmdb_videos(
    session: aiohttp.ClientSession,
    tmdb_id: str,
    is_movie: bool,
    season: int,
    api_key: str,
    language: str = "",
) -> list[dict]:
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


async def get_tmdb_youtube_key(
    media: MediaRead,
    video_type: str,
    season: int = 0,
    language: str = "",
) -> str | None:
    """Fetch the first matching YouTube key from TMDB for the given video_type and season."""
    api_key = app_settings.tmdb_api_key
    if not api_key or not media.txdb_id:
        return None
    async with aiohttp.ClientSession() as session:
        results = await _fetch_tmdb_videos(
            session,
            media.txdb_id,
            media.is_movie,
            season,
            api_key,
            language=language,
        )
    return _find_youtube_key(results, str(video_type))


async def refresh_tmdb_videos(
    _stop_event: threading.Event | None = None,
) -> None:
    """Check TMDB for video availability and update trailer-status rows accordingly.

    Groups rows by (media_id, season, tmdb_language) so each unique language gets its
    own TMDB API call. Found YouTube keys are cached on the row (youtube_id field) so
    the download task can skip redundant live TMDB calls. TMDB-sourced keys are NEVER
    written back to media.youtube_trailer_id.
    """
    api_key = app_settings.tmdb_api_key
    if not api_key:
        logger.warning(
            "TMDB API key is not configured — skipping TMDB video refresh."
            " Set TMDB_API_KEY in General Settings."
        )
        return

    rows = trailer_status_repo.get_pending_for_tmdb_refresh()
    if not rows:
        logger.info(
            "No PENDING/NOT_AVAILABLE rows found — TMDB refresh skipped."
        )
        return

    logger.info(f"TMDB refresh starting: {len(rows)} row(s) to check.")

    # Group by (media_id, season, tmdb_language) — each combination needs its own TMDB call
    groups: dict[tuple[int, int, str], list[TmdbPendingRow]] = defaultdict(
        list
    )
    for row in rows:
        groups[(row.media_id, row.season, row.tmdb_language)].append(row)

    updated_pending = 0
    updated_not_available = 0
    cached_youtube_ids = 0
    errors = 0

    async with aiohttp.ClientSession() as http_session:
        for (media_id, season, tmdb_language), group_rows in groups.items():
            if _stop_event and _stop_event.is_set():
                logger.info("Stop event set — terminating TMDB refresh.")
                break

            media = media_repo.read(media_id)
            if media is None:
                logger.warning(f"Media {media_id} not found — skipping.")
                errors += 1
                continue
            if not media.txdb_id:
                logger.debug(
                    f"Media {media_id} has no txdb_id — skipping TMDB check."
                )
                continue

            try:
                results = await _fetch_tmdb_videos(
                    http_session,
                    media.txdb_id,
                    media.is_movie,
                    season,
                    api_key,
                    language=tmdb_language,
                )
            except Exception as exc:
                logger.error(
                    "Unexpected error fetching TMDB videos for media"
                    f" {media_id}: {exc}"
                )
                errors += 1
                continue

            for row in group_rows:
                yt_key = _find_youtube_key(results, row.video_type)
                has_result = yt_key is not None

                # Cache the YouTube key on the row (applies to all video types).
                # This lets the download task skip a redundant live TMDB call.
                if yt_key and yt_key != row.youtube_id:
                    trailer_status_repo.update_row_youtube_id(
                        row.row_id, yt_key
                    )
                    cached_youtube_ids += 1

                if row.video_type == VideoType.TRAILER:
                    # Trailer rows: only cache the key, no status flip — the download
                    # pipeline handles trailer → youtube_trailer_id → YouTube search.
                    continue

                # Non-trailer TMDB types: flip status based on availability.
                if (
                    has_result
                    and row.status == TrailerStatusEnum.NOT_AVAILABLE
                ):
                    trailer_status_repo.update_row_status(
                        row.row_id, TrailerStatusEnum.PENDING
                    )
                    logger.debug(
                        f"Row {row.row_id} ({row.video_type}) reset to PENDING"
                        f" (TMDB has results for media {media_id},"
                        f" lang='{tmdb_language}')."
                    )
                    updated_pending += 1
                elif (
                    not has_result and row.status == TrailerStatusEnum.PENDING
                ):
                    trailer_status_repo.update_row_status(
                        row.row_id, TrailerStatusEnum.NOT_AVAILABLE
                    )
                    logger.debug(
                        f"Row {row.row_id} ({row.video_type}) set to"
                        " NOT_AVAILABLE (no TMDB results for media"
                        f" {media_id}, lang='{tmdb_language}')."
                    )
                    updated_not_available += 1

            await asyncio.sleep(_SLEEP_BETWEEN_REQUESTS)

    logger.info(
        "TMDB refresh complete."
        f" Cached YouTube IDs: {cached_youtube_ids},"
        f" Reset to PENDING: {updated_pending},"
        f" Set NOT_AVAILABLE: {updated_not_available},"
        f" Errors: {errors}."
    )
