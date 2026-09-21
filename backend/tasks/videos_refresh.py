"""Keep the list of videos that TMDB offers up to date.

The download task asks TMDB about a media item just before it downloads
for it, which is enough to download the right trailer. This task runs
ahead of it, so the Known videos list on a media details page is filled
in before anyone waits for a download, and so the work is spread out
instead of landing on one download run.

It asks about the items that have work waiting — the ones a download task
would look at — and it stops at a limit per run. A library of 1,700 items
would otherwise send 1,700 requests the first time it runs.
"""

import asyncio
import threading

import database.manager.media as media_manager
from app_logger import ModuleLogger
from services.tmdb.refresh import TMDBRefresher
from services.trailers.trailers.missing import refresh_videos_if_stale
from services.trailers.trailers.pending import compute_library_pending

logger = ModuleLogger("VideosRefreshTask")

# The most media items to ask TMDB about in one run. TMDB allows a healthy
# request rate, and this is about being a good neighbour rather than about
# a hard limit: the rest of the library is covered by the next run and by
# the download task.
MAX_ITEMS_PER_RUN = 200

# A short pause between calls, so a first run over a large library arrives
# as a trickle instead of a burst.
PAUSE_BETWEEN_CALLS = 0.1


async def refresh_media_videos(
    _stop_event: threading.Event | None = None,
) -> None:
    """Ask TMDB about the media items that have a download waiting."""
    refresher = TMDBRefresher()
    if not refresher.enabled:
        logger.debug(
            "No TMDB API key is set, so Trailarr does not ask TMDB about"
            " any media item."
        )
        return

    pending = compute_library_pending(limit=1000)
    media_ids = [item.media_id for item in pending.items]
    if not media_ids:
        logger.info("No media item is waiting for a trailer.")
        return

    asked = 0
    skipped = 0
    for media_id in media_ids:
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Trailarr stopped the video refresh. A stop was requested."
            )
            break
        if asked >= MAX_ITEMS_PER_RUN:
            logger.info(
                f"Trailarr asked TMDB about {MAX_ITEMS_PER_RUN} media items,"
                " which is the limit for one run. The next run continues."
            )
            break
        if not refresher.enabled:
            # The key was refused during this run.
            break
        media = media_manager.read(media_id)
        if await refresh_videos_if_stale(media, refresher):
            asked += 1
            await asyncio.sleep(PAUSE_BETWEEN_CALLS)
        else:
            skipped += 1

    logger.info(
        f"Trailarr asked TMDB about {asked} media items, and left {skipped}"
        " alone because their videos are still fresh."
    )
