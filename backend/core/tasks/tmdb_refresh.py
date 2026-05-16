"""Weekly task: refresh TMDB video availability for non-trailer profile rows.

For each monitored media item that has PENDING or NOT_AVAILABLE rows on a profile
whose video_type != 'trailer', query the TMDB videos endpoint.
- If TMDB has matching results  → reset the row to PENDING so the download loop picks it up.
- If TMDB has no matching results → set/keep the row as NOT_AVAILABLE.

For trailer-type rows that are PENDING, also check TMDB to pre-cache the YouTube key
on the media row so the download loop can skip the search step.
"""

import asyncio
import threading
from dataclasses import dataclass

import aiohttp

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.mediatrailerstatus import (
    MediaTrailerStatus,
    TrailerStatusEnum,
)
from core.base.database.models.trailerprofile import TrailerProfile, VideoType
from core.base.database.models.media import Media
import core.base.database.manager.trailerstatusmanager as trailer_status_manager
import core.base.database.manager.media as media_manager
from core.base.database.utils.engine import read_session
from sqlmodel import Session, col, select

logger = ModuleLogger("TMDBRefreshTask")

_TMDB_BASE = "https://api.themoviedb.org/3"
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
_SLEEP_BETWEEN_REQUESTS = 0.5  # seconds between TMDB API calls


@dataclass
class _PendingRow:
    """Lightweight holder for rows that need a TMDB check."""

    row_id: int
    media_id: int
    profile_id: int
    season: int
    video_type: str
    status: TrailerStatusEnum


def _get_rows_to_check() -> list[_PendingRow]:
    """Load PENDING and NOT_AVAILABLE rows for monitored media where profile_id IS NOT NULL."""

    @read_session
    def _query(*, _session: Session = None) -> list[_PendingRow]:  # type: ignore
        stmt = (
            select(
                MediaTrailerStatus.id,
                MediaTrailerStatus.media_id,
                MediaTrailerStatus.profile_id,
                MediaTrailerStatus.season,
                MediaTrailerStatus.status,
                TrailerProfile.video_type,
            )
            .join(
                TrailerProfile,
                TrailerProfile.id == MediaTrailerStatus.profile_id,
            )
            .join(Media, Media.id == MediaTrailerStatus.media_id)
            .where(
                MediaTrailerStatus.status.in_(  # type: ignore[union-attr]
                    [TrailerStatusEnum.PENDING, TrailerStatusEnum.NOT_AVAILABLE]
                ),
                MediaTrailerStatus.profile_id.isnot(None),  # type: ignore[union-attr]
                col(Media.monitor).is_(True),
            )
        )
        rows = _session.exec(stmt).all()
        return [
            _PendingRow(
                row_id=r.id,
                media_id=r.media_id,
                profile_id=r.profile_id,
                season=r.season,
                video_type=str(r.video_type),
                status=r.status,
            )
            for r in rows
        ]

    return _query()  # type: ignore


def _get_media_info(media_id: int) -> tuple[str, bool] | None:
    """Return (txdb_id, is_movie) for the given media_id, or None if not found."""
    media = media_manager.read(media_id)
    if media is None:
        return None
    return media.txdb_id, media.is_movie


async def _fetch_tmdb_videos(
    session: aiohttp.ClientSession,
    tmdb_id: str,
    is_movie: bool,
    season: int,
    api_key: str,
) -> list[dict]:
    """Call the TMDB videos endpoint and return the results list.

    Endpoints used:
    - Movie:       /movie/{id}/videos
    - Series root: /tv/{id}/videos
    - Season:      /tv/{id}/season/{season}/videos
    """
    if is_movie:
        url = f"{_TMDB_BASE}/movie/{tmdb_id}/videos"
    elif season > 0:
        url = f"{_TMDB_BASE}/tv/{tmdb_id}/season/{season}/videos"
    else:
        url = f"{_TMDB_BASE}/tv/{tmdb_id}/videos"

    params = {"api_key": api_key, "language": "en-US"}
    try:
        async with session.get(url, params=params, timeout=_REQUEST_TIMEOUT) as resp:
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
            f"TMDB request timed out for {'movie' if is_movie else 'tv'}/{tmdb_id}"
        )
        return []
    except aiohttp.ClientError as exc:
        logger.warning(f"TMDB request failed: {exc}")
        return []


def _video_type_matches(result: dict, video_type: str) -> bool:
    """Return True if the TMDB result's type matches the requested video_type."""
    result_type = (result.get("type") or "").lower()
    vt = video_type.lower()
    # TMDB uses: Trailer, Teaser, Clip, Behind the Scenes, Bloopers, Featurette, Opening Credits
    return result_type == vt


def _find_youtube_key(results: list[dict], video_type: str) -> str | None:
    """Return the YouTube key for the first TMDB result matching video_type, or None."""
    for r in results:
        if r.get("site", "").lower() == "youtube" and _video_type_matches(r, video_type):
            return r.get("key")
    return None


async def refresh_tmdb_videos(
    _stop_event: threading.Event | None = None,
) -> None:
    """Check TMDB video availability for all PENDING/NOT_AVAILABLE trailer-status rows.

    Groups rows by (media_id, season) to minimise TMDB API calls (one call per pair).
    """
    api_key = app_settings.tmdb_api_key
    if not api_key:
        logger.warning(
            "TMDB API key is not configured — skipping TMDB video refresh."
            " Set TMDB_API_KEY in General Settings."
        )
        return

    rows = _get_rows_to_check()
    if not rows:
        logger.info("No PENDING/NOT_AVAILABLE rows found — TMDB refresh skipped.")
        return

    logger.info(
        f"TMDB refresh starting: {len(rows)} row(s) to check."
    )

    # Group rows by (media_id, season) so we call TMDB once per combination.
    from collections import defaultdict

    groups: dict[tuple[int, int], list[_PendingRow]] = defaultdict(list)
    for row in rows:
        groups[(row.media_id, row.season)].append(row)

    updated_pending = 0
    updated_not_available = 0
    errors = 0

    async with aiohttp.ClientSession() as http_session:
        for (media_id, season), group_rows in groups.items():
            if _stop_event and _stop_event.is_set():
                logger.info("Stop event set — terminating TMDB refresh.")
                break

            media_info = _get_media_info(media_id)
            if media_info is None:
                logger.warning(f"Media {media_id} not found — skipping.")
                errors += 1
                continue

            txdb_id, is_movie = media_info
            if not txdb_id:
                logger.debug(
                    f"Media {media_id} has no txdb_id — skipping TMDB check."
                )
                continue

            try:
                results = await _fetch_tmdb_videos(
                    http_session, txdb_id, is_movie, season, api_key
                )
            except Exception as exc:
                logger.error(
                    f"Unexpected error fetching TMDB videos for media {media_id}: {exc}"
                )
                errors += 1
                continue

            for row in group_rows:
                yt_key = _find_youtube_key(results, row.video_type)
                has_result = yt_key is not None

                if row.video_type == VideoType.TRAILER:
                    # For trailer-type rows: only cache the YouTube key; always keep PENDING
                    # so the download loop runs (YouTube search is the fallback anyway).
                    if yt_key and row.status == TrailerStatusEnum.PENDING:
                        # Store the YouTube key on the media row as a cache hint.
                        media_manager.update_ytid(media_id, yt_key)
                    continue

                # For non-trailer types: TMDB is the only source.
                if has_result and row.status == TrailerStatusEnum.NOT_AVAILABLE:
                    # TMDB now has this type — reset to PENDING for the download loop.
                    trailer_status_manager.update_row_status(
                        row.row_id, TrailerStatusEnum.PENDING
                    )
                    logger.debug(
                        f"Row {row.row_id} ({row.video_type}) reset to PENDING"
                        f" (TMDB has results for media {media_id})."
                    )
                    updated_pending += 1
                elif not has_result and row.status == TrailerStatusEnum.PENDING:
                    # TMDB has no results — mark NOT_AVAILABLE.
                    trailer_status_manager.update_row_status(
                        row.row_id, TrailerStatusEnum.NOT_AVAILABLE
                    )
                    logger.debug(
                        f"Row {row.row_id} ({row.video_type}) set to NOT_AVAILABLE"
                        f" (no TMDB results for media {media_id})."
                    )
                    updated_not_available += 1
                # already NOT_AVAILABLE with no results, or already PENDING with results → no change

            await asyncio.sleep(_SLEEP_BETWEEN_REQUESTS)

    logger.info(
        f"TMDB refresh complete."
        f" Reset to PENDING: {updated_pending},"
        f" Set NOT_AVAILABLE: {updated_not_available},"
        f" Errors: {errors}."
    )
