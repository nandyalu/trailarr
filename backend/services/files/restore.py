"""Restore a deleted download whose file is on disk again (#733).

A download is marked deleted when its file is not on disk. When the storage
was only out of reach, for example a network share that did not mount, the
file comes back, but the download stays deleted, and the profile downloads
the same video again under a "Trailer 2" name.

A download is restored when a file is at its path, the size of the file is
the size of the download, and no active download has that path. A file of
another size is another file, and the disk scan records it.

Three callers use this: the Cleanup Task every day, a startup pass at every
start, and the download task just before it downloads for a media item.
"""

import stat

import aiofiles.os

from app_logger import ModuleLogger
import database.manager.download as download_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.download import DownloadRead
from database.models.event import EventSource
from database.models.media import MediaRead
from database.models.video_type import is_trailer_type, video_type_label

logger = ModuleLogger("FilesRestore")


async def restore_if_on_disk(
    download: DownloadRead,
    source_detail: str,
    title: str | None = None,
) -> bool:
    """Mark one deleted download as active again when its file is back.

    Args:
        download (DownloadRead): A deleted download.
        source_detail (str): The task that restores it, for the event.
        title (str | None): The title of the media item, for the log. When
            None, it is read after a restore, so that a download that is
            not restored costs no database read.
    Returns:
        bool: True when the download was restored.
    """
    if download.file_exists or not download.path:
        return False
    try:
        file_stat = await aiofiles.os.stat(download.path)
    except OSError:
        return False
    if not stat.S_ISREG(file_stat.st_mode):
        return False
    if file_stat.st_size != download.size:
        return False
    # Checks again under the write lock: the disk scan can record the same
    # file in the meantime.
    if not download_manager.mark_as_restored(download.id):
        return False
    # As in the disk scan: no event for an extra. An event is permanent, and
    # it goes to the channels that subscribe to it.
    if is_trailer_type(download.video_type):
        event_manager.track_trailer_detected(
            media_id=download.media_id,
            source=EventSource.SYSTEM,
            source_detail=source_detail,
        )
    if title is None:
        title = media_manager.read(download.media_id).title
    logger.info(
        f"The {video_type_label(download.video_type).lower()} file of"
        f" '{title}' is on disk again. Trailarr marks it as active."
        f" Path: '{download.path}'.",
        **logger.media(download.media_id),
    )
    return True


async def restore_returned_files(media: MediaRead, source_detail: str) -> int:
    """Restore the deleted downloads of one media item whose files are back.

    `media.downloads` must be loaded. Only the newest deleted download of a
    path is examined, and a path that an active download has is skipped.

    Args:
        media (MediaRead): The media item, with its downloads.
        source_detail (str): The task that restores them, for the event.
    Returns:
        int: The number of restored downloads.
    """
    active_paths = {d.path for d in media.downloads if d.file_exists}
    seen: set[str] = set()
    restored = 0
    newest_first = sorted(media.downloads, key=lambda d: d.id, reverse=True)
    for download in newest_first:
        if download.file_exists or not download.path:
            continue
        if download.path in active_paths or download.path in seen:
            continue
        seen.add(download.path)
        if await restore_if_on_disk(download, source_detail, media.title):
            restored += 1
    return restored
