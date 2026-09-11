"""Filling the candidates table from TMDB.

One media item at a time: ask TMDB which videos belong to it, keep the
trailers, and give them to the manager as the TMDB list for that item. The
manager adds what is new, updates what changed, and removes the TMDB rows
that TMDB no longer offers. Rows of the other sources are not touched.

No key means no call at all, checked once here rather than at every call
(wargame W8). A key that TMDB refuses turns TMDB off for the rest of the
run, so one bad key cannot make a whole task fail (wargame W1).
"""

from app_logger import ModuleLogger
import database.manager.mediavideo as video_manager
from config.settings import app_settings
from database.models.media import MediaRead
from database.models.mediavideo import VideoSource
from services.tmdb.api_manager import TMDBAPI, TMDBAuthError
from services.tmdb.videos import to_candidates

logger = ModuleLogger("TMDBRefresh")


class TMDBRefresher:
    """Refreshes the TMDB candidates for one run of a task.

    One instance per run: it holds the client, and with it the cache of
    answers, and it remembers a refused key so that the rest of the run
    makes no more calls.
    """

    def __init__(self, api: TMDBAPI | None = None):
        self.api = api or TMDBAPI(app_settings.tmdb_api_key)
        self._disabled = not self.api.configured

    @property
    def enabled(self) -> bool:
        """False when there is no key, or when TMDB refused the key."""
        return not self._disabled

    async def refresh_media(self, media: MediaRead) -> int:
        """Update the TMDB candidates of one media item.

        Args:
            media (MediaRead): The media item to refresh.

        Returns:
            int: How many TMDB candidates the media item has now. Zero
                when TMDB is off, the item has no TMDB id, or TMDB lists
                no trailer for it.
        """
        if self._disabled:
            return 0
        if not media.tmdb_id:
            # Decision 6: without a TMDB id there is nothing to ask for.
            # The resolver falls back to the other sources.
            logger.debug(
                f"'{media.title}' has no TMDB id, so Trailarr does not ask"
                " TMDB about it."
            )
            return 0
        try:
            videos = await self.api.get_videos(
                int(media.tmdb_id), is_movie=media.is_movie
            )
        except TMDBAuthError as e:
            self._disabled = True
            logger.error(
                f"TMDB refused the API key, so Trailarr stops asking TMDB"
                f" in this run and uses the other sources: {e}"
            )
            return 0
        except Exception as e:
            # A failure at TMDB must never stop a download task.
            logger.warning(
                f"Trailarr could not read the TMDB videos for"
                f" '{media.title}': {e}"
            )
            return 0

        candidates = to_candidates(videos, media.id)
        added, updated, removed = video_manager.replace_source_rows(
            media.id, VideoSource.TMDB, candidates
        )
        if added or updated or removed:
            logger.info(
                f"Trailarr updated the TMDB videos for '{media.title}':"
                f" {added} added, {updated} changed, {removed} removed.",
                **logger.media(media.id),
            )
        return len(candidates)
