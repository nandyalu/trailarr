"""Keeping the ids that Radarr and Sonarr give in the candidates table.

Both applications report a YouTube trailer id for a media item. Before
Phase 8 that id lived in `media.youtube_trailer_id` and the resolver read
it from there. Now the resolver reads only the candidates table, so a sync
has to put the id into the table.

ARR rows are never removed here. Only the source that offers a list prunes
its own rows, and an Arr reports one id, not a list — so an id that
disappears from the Arr leaves its row behind, ready to be tried after the
better sources.
"""

from app_logger import ModuleLogger
import database.manager.mediavideo as video_manager
from database.models.media import MediaRead
from database.models.mediavideo import MediaVideoCreate, VideoSource

logger = ModuleLogger("ArrVideos")


def sync_arr_video_id(media: MediaRead, arr_video_id: str | None) -> None:
    """Put the id that the Arr reports into the candidates table.

    This is also where a migrated row learns where its id came from. The
    upgrade could not know: `media.youtube_trailer_id` held whatever was
    last written to it, which is an id from Radarr for some items and a
    video Trailarr downloaded for others, so every migrated row starts as
    a SEARCH row. The Arr is the only thing that can say, and it says it
    here — the id it reports takes the row over as an ARR row.

    A row that the user owns is never taken (decision 5b).

    Args:
        media (MediaRead): The media item that the sync just wrote.
        arr_video_id (str | None): The id the Arr reports, if any. Sonarr
            reports none, because its metadata comes from TVDB.
    """
    if not arr_video_id:
        return
    arr_video_id = arr_video_id.strip()
    if not arr_video_id:
        return

    # No early return when the id is already in the table: the row may be
    # a SEARCH row from the upgrade, or from a search that happened to find
    # the same video, and the call below promotes it to an ARR row. The
    # manager refuses to take a row the user owns, so their choice is safe.
    video_manager.replace_source_rows(
        media.id,
        VideoSource.ARR,
        [
            MediaVideoCreate(
                media_id=media.id,
                video_id=arr_video_id,
                source=VideoSource.ARR,
                sequence=0,
                name="",
                official=False,
            )
        ],
    )
