"""Find the download that a file on disk belongs to, and restore it (#733).

A download is marked deleted when its file is not on disk. When the storage
was only out of reach, for example a network share that did not mount, the
file comes back, but the download stays deleted, and the profile downloads
the same video again under a "Trailer 2" name.

A person can also change the file outside Trailarr: give it a new name,
move it, or change its tracks. So a file matches a download by one of these
rules, in this order:

1. The file is at the path of the download.
2. The file has the file name of the download, in another folder.
3. The file has the YouTube id of the download in its metadata. A file
   that Trailarr downloaded with `Embed Metadata` on has one.

When the file and the download both have a YouTube id and the ids are not
the same, the file is another video, and rules 1 and 2 do not apply. When
the path or the size changed, Trailarr analyzes the file again.

The Cleanup Task (every day) and a startup pass (at every start) restore a
deleted download whose file is at its path. The download task, just before
it downloads for a media item, also searches the folder of that item. The
disk scan uses the same rules for the files it finds.
"""

import asyncio
import os
import stat

import aiofiles.os

from app_logger import ModuleLogger
import database.manager.download as download_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.download import DownloadRead, is_unknown_video
from database.models.event import EventSource
from database.models.media import MediaRead
from database.models.video_type import is_trailer_type, video_type_label
from services.files.media_scanner import MediaScanner
from services.trailers.trailers.service import reanalyze_trailer_download
from services.trailers.video_analysis import VideoInfo, get_media_info

logger = ModuleLogger("FilesRestore")


def _is_other_video(
    file_youtube_id: str | None, download: DownloadRead
) -> bool:
    """True when the file and the download name two different videos."""
    if is_unknown_video(file_youtube_id) or is_unknown_video(
        download.youtube_id
    ):
        return False
    return file_youtube_id != download.youtube_id


def find_matching_download(
    file_path: str,
    file_youtube_id: str | None,
    candidates: list[DownloadRead],
) -> DownloadRead | None:
    """The download that a file belongs to, by the rules of this module.

    Args:
        file_path (str): The file on disk.
        file_youtube_id (str | None): The YouTube id in the metadata of the
            file, or None when it has none or was not read.
        candidates (list[DownloadRead]): The downloads that the file can
            belong to, in the order of preference.
    Returns:
        DownloadRead | None: The first download that matches, or None.
    """
    file_name = os.path.basename(file_path)
    same_path = [d for d in candidates if d.path == file_path]
    same_name = [
        d for d in candidates if os.path.basename(d.path) == file_name
    ]
    for download in same_path + same_name:
        if not _is_other_video(file_youtube_id, download):
            return download
    if is_unknown_video(file_youtube_id):
        return None
    return next(
        (d for d in candidates if d.youtube_id == file_youtube_id), None
    )


def restore_candidates(media: MediaRead) -> list[DownloadRead]:
    """The deleted downloads of a media item that a file can take back.

    Only the newest deleted download of a path counts, and a path that an
    active download has is left out. `media.downloads` must be loaded.

    Returns:
        list[DownloadRead]: The downloads, newest first.
    """
    active_paths = {d.path for d in media.downloads if d.file_exists}
    deleted = [d for d in media.downloads if not d.file_exists and d.path]
    seen: set[str] = set()
    candidates = []
    for download in sorted(deleted, key=lambda d: d.id, reverse=True):
        if download.path in active_paths or download.path in seen:
            continue
        seen.add(download.path)
        candidates.append(download)
    return candidates


async def probe(file_path: str) -> VideoInfo | None:
    """Run ffprobe on a file in a thread, so the event loop does not wait."""
    return await asyncio.to_thread(get_media_info, file_path)


async def take_back(
    download: DownloadRead,
    file_path: str,
    video_info: VideoInfo | None,
    source_detail: str,
    title: str | None = None,
) -> bool:
    """Restore a deleted download for the file at `file_path`.

    Args:
        download (DownloadRead): The deleted download.
        file_path (str): The file. It can have a new name or folder.
        video_info (VideoInfo | None): The ffprobe result of the file. With
            one, Trailarr analyzes the file again and updates the download.
            None keeps the stored analysis: the file is the same.
        source_detail (str): The task that restores it, for the event.
        title (str | None): The title of the media item, for the log. When
            None, it is read after the restore.
    Returns:
        bool: True when the download was restored.
    """
    moved = file_path != download.path
    # Checks again under the write lock: the disk scan can record the same
    # file in the meantime.
    if not download_manager.mark_as_restored(
        download.id, new_path=file_path if moved else None
    ):
        return False
    if video_info is not None:
        await reanalyze_trailer_download(
            download,
            file_path,
            video_info=video_info,
            with_hash=is_trailer_type(download.video_type),
        )
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
    kind = video_type_label(download.video_type).lower()
    where = (
        f" Old path: '{download.path}'. New path: '{file_path}'."
        if moved
        else f" Path: '{file_path}'."
    )
    logger.info(
        f"The {kind} file of '{title}' is on disk again. Trailarr marks it"
        f" as active.{where}",
        **logger.media(download.media_id),
    )
    return True


async def restore_if_on_disk(
    download: DownloadRead,
    source_detail: str,
    title: str | None = None,
) -> bool:
    """Restore a deleted download when a file is at its stored path.

    A file of the same size is the same file. A file of another size was
    changed, for example its tracks: Trailarr analyzes it again, unless its
    YouTube id shows that it is another video.

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
    video_info = None
    if file_stat.st_size != download.size:
        video_info = await probe(download.path)
        if video_info is None:
            return False
        if _is_other_video(video_info.youtube_id, download):
            return False
    return await take_back(
        download, download.path, video_info, source_detail, title
    )


async def _search_folder(
    media: MediaRead,
    candidates: list[DownloadRead],
    taken_paths: set[str],
    source_detail: str,
) -> int:
    """Match the trailer files in the folder of a media item that no
    download has to the deleted downloads whose stored path is gone."""
    scanner = MediaScanner()
    files_info = await scanner.get_folder_files(media.folder_path, media.id)
    if not files_info:
        return 0
    tracked = {d.path for d in media.downloads if d.file_exists}
    untracked = sorted(
        scanner.get_trailer_paths(files_info) - tracked - taken_paths
    )
    restored = 0
    for file_path in untracked:
        if not candidates:
            break
        video_info = await probe(file_path)
        file_youtube_id = video_info.youtube_id if video_info else None
        match = find_matching_download(file_path, file_youtube_id, candidates)
        if match is None:
            continue
        if await take_back(
            match, file_path, video_info, source_detail, media.title
        ):
            restored += 1
            candidates.remove(match)
    return restored


async def restore_returned_files(
    media: MediaRead,
    source_detail: str,
    search_folder: bool = False,
) -> int:
    """Restore the deleted downloads of one media item whose files are back.

    `media.downloads` must be loaded.

    Args:
        media (MediaRead): The media item, with its downloads.
        source_detail (str): The task that restores them, for the event.
        search_folder (bool): Also look in the folder of the media item for
            a file with a new name or in another folder. The download task
            does this just before it downloads.
    Returns:
        int: The number of restored downloads.
    """
    restored = 0
    taken_paths: set[str] = set()
    gone: list[DownloadRead] = []
    for download in restore_candidates(media):
        if await restore_if_on_disk(download, source_detail, media.title):
            restored += 1
            taken_paths.add(download.path)
        elif not await aiofiles.os.path.exists(download.path):
            gone.append(download)
    if search_folder and gone and media.folder_path:
        restored += await _search_folder(
            media, gone, taken_paths, source_detail
        )
    return restored
