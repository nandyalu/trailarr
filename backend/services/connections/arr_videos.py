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
from database.models.mediavideo import (
    MediaVideoCreate,
    MediaVideoRead,
    VideoSource,
)

logger = ModuleLogger("ArrVideos")


def sync_arr_video_id(media: MediaRead, arr_video_id: str | None) -> None:
    """Put the id that the Arr reports into the candidates table.

    The recovery of decision 5: before Phase 8, the only way to choose a
    trailer by hand was to edit `media.youtube_trailer_id`, and the upgrade
    turned every one of those into an ARR row. So an ARR row that holds a
    different id than the Arr now reports was almost certainly typed by a
    person, and it becomes a USER row instead of being replaced.

    Mislabelling is safe in this direction: it gives an id that someone
    stored on purpose a little more precedence, and it protects it from
    later automation. Losing it is not safe, which is the other direction.

    Args:
        media (MediaRead): The media item that the sync just wrote.
        arr_video_id (str | None): The id the Arr reports, if any.
    """
    if not arr_video_id:
        return
    arr_video_id = arr_video_id.strip()
    if not arr_video_id:
        return

    existing = video_manager.read_for_media(media.id)
    by_id = {row.video_id: row for row in existing}
    if arr_video_id in by_id:
        # Already known, from this source or a better one. Nothing to do:
        # a row that the user owns must keep its source.
        return

    for row in existing:
        if row.source != VideoSource.ARR:
            continue
        if row.video_id == arr_video_id:
            continue
        _keep_as_user_choice(media, row)

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


def _keep_as_user_choice(media: MediaRead, row: MediaVideoRead) -> None:
    """Turn an ARR row that no longer matches the Arr into a USER row."""
    if video_manager.relabel_as_user(media.id, row.video_id):
        logger.info(
            f"The trailer id '{row.video_id}' for '{media.title}' is not the"
            " one that Radarr or Sonarr reports, so Trailarr keeps it as a"
            " video that you chose.",
            **logger.media(media.id),
        )
