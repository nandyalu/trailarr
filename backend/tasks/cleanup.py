"""Daily cleanup: old log entries, and trailers that are gone or broken.

The trailer part reads what is on disk. A file that no longer exists is
marked deleted, but only when the folder that holds it still has files:
an empty or missing folder means that the storage is not there (#733). A
deleted download whose file is back on disk is marked active again. A file
with no audio or no video is deleted, but only when the user turned that
on. An empty file is a bad trailer too (#705).
"""

import asyncio
import os
import threading

import aiofiles.os
from app_logger import ModuleLogger
from config.settings import app_settings
from config.logs import manager as logs_manager
import database.manager.download as download_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.event import EventSource
from database.models.video_type import is_trailer_type
from services.trailers import video_analysis
from services.files.files_handler import FilesHandler, folder_has_entries
from services.files.restore import restore_if_on_disk
from utils.path_utils import is_subpath

logger = ModuleLogger("CleanupTasks")


async def delete_old_logs():  # pragma: no cover
    """
    Delete old log files from the '/config/logs' directory.
    This function is intended to be run periodically to keep the log directory clean.
    """
    logger.info("Trailarr removes the old log entries.")
    deleted_count = await logs_manager.delete_old_logs(30)
    logger.info(
        f"Trailarr removed {deleted_count} log entries that were more than"
        " 30 days old."
    )
    return None


async def delete_trailer(trailer_path: str, download_id: int):
    """
    Delete the trailer file and mark file as deleted in Download. \n
    Args:
        trailer_path (str): Path to the trailer file. \n
        download_id (int): ID of the download entry. \n
    Returns:
        None
    """
    await FilesHandler.delete_file(trailer_path)
    download_manager.mark_as_deleted(download_id)
    return None


async def _is_empty_file(path: str) -> bool:
    """True when the file has 0 bytes. False when it has data, or when
    Trailarr cannot read its size: then the check of the streams decides."""
    try:
        return await aiofiles.os.path.getsize(path) == 0
    except OSError:
        return False


def _storage_folder(media_folder: str, trailer_path: str) -> str:
    """The folder that must hold files before a missing trailer counts as
    deleted: the media folder for a trailer inside it, else the folder of
    the trailer itself (a custom folder)."""
    if media_folder and is_subpath(media_folder, trailer_path):
        return media_folder
    return os.path.dirname(trailer_path)


async def restore_returned_trailers(
    stop_event: threading.Event | None = None,
) -> int:
    """Mark the deleted downloads whose files are back as active again.

    See `services/files/restore.py` for the rule (#733). This pass looks at
    the whole library. The download task looks at one media item just
    before it downloads for it.

    Returns:
        int: The number of restored downloads.
    """
    restored = 0
    seen: set[str] = set()
    for download in download_manager.read_deleted_without_live_copy():
        if stop_event and stop_event.is_set():
            break
        # The list is newest first, so the newest row of a path is restored.
        if download.path in seen:
            continue
        seen.add(download.path)
        if await restore_if_on_disk(download, "CleanupTask"):
            restored += 1
    if restored:
        logger.info(
            f"Trailarr found {restored} deleted files on disk again and"
            " marked them as active."
        )
    return restored


async def trailer_cleanup(stop_event: threading.Event | None = None):
    """
    Cleanup failed trailers (without audio), delete them and set monitor status to True.
    Also cleanup any residual files left in '/tmp' directory.
    """
    logger.info("Trailarr checks the trailer files on disk.")
    await restore_returned_trailers(stop_event)
    # Get all media from the database that are downloaded
    media_with_trailers = media_manager.read_all_generator(
        downloaded_only=True
    )
    logger.info("Trailarr examines every media item that has a trailer.")
    # Analyze the trailer files and remove the ones without audio
    analyzed_count = 0
    file_missing_count = 0
    storage_missing_count = 0
    verification_failed_count = 0
    for media in media_with_trailers:
        # Skip media with no downloads
        if not media.downloads:
            continue
        logger.debug(
                f"Trailarr examines the trailers of '{media.title}'.",
                **logger.media(media.id),
            )
        for download in media.downloads:
            if stop_event and stop_event.is_set():
                logger.info(
                    "Trailarr stopped the trailer check. A stop was"
                    " requested."
                )
                return

            _path = download.path
            # Skip if file has already been deleted or path is missing
            if not download.file_exists:
                continue
            # Only the trailers. The scan records the extras that a person
            # placed (a featurette, a deleted scene) as download rows too.
            # Trailarr never deletes a file it did not download, unless a
            # person deletes it from the Files section.
            if not is_trailer_type(download.video_type):
                continue
            analyzed_count += 1
            # Check if file exists on disk
            if not _path or not await aiofiles.os.path.exists(_path):
                # An empty or missing folder means that the storage is not
                # there, for example a network share that did not mount.
                # The file is probably still on the share, so the download
                # stays active (#733). A folder that is really gone is the
                # job of the disk scan.
                # TODO: once the planned "Issues" section exists, raise an
                # issue here to surface this to the user.
                folder = (
                    _storage_folder(media.folder_path, _path) if _path else ""
                )
                if folder and not await asyncio.to_thread(
                    folder_has_entries, folder
                ):
                    storage_missing_count += 1
                    logger.info(
                        f"The trailer file for '{media.title}' is not on"
                        f" disk, and the folder '{folder}' is empty or"
                        " missing. Trailarr does not mark the trailer as"
                        f" deleted. Path: '{_path}'.",
                        **logger.media(media.id),
                    )
                    continue
                file_missing_count += 1
                logger.info(
                    f"The trailer file for '{media.title}' is not on disk."
                    f" Trailarr marks it as deleted. Path: '{_path}'.",
                    **logger.media(media.id),
                )
                download.file_exists = False
                download_manager.mark_as_deleted(download.id)
                # Track trailer_deleted event for missing file
                event_manager.track_trailer_deleted(
                    media_id=media.id,
                    reason="file_not_found",
                    source=EventSource.SYSTEM,
                    source_detail="CleanupTask",
                )
                continue

            # Verify the trailer has audio and video streams
            # if not, delete the trailer file and set monitor to True.
            # ffprobe cannot read an empty file, so the check of the streams
            # cannot tell that it is bad. An empty file is never a trailer:
            # a copy that failed in an older version left such files (#705).
            if await _is_empty_file(_path):
                verified = False
                problem = "is an empty file"
            else:
                verified = video_analysis.verify_trailer_streams(_path)
                problem = "has no audio or no video"
            if verified is None:
                logger.info(
                    f"Trailarr could not examine the trailer for"
                    f" '{media.title}'. Trailarr keeps the file."
                    f" Path: '{_path}'.",
                    **logger.media(media.id),
                )
                continue
            elif verified is False:
                verification_failed_count += 1
                if app_settings.delete_corrupted_trailers:
                    logger.info(
                        f"The trailer for '{media.title}' {problem}."
                        f" Trailarr deletes it. Path: '{_path}'.",
                        **logger.media(media.id),
                    )
                    await delete_trailer(_path, download.id)
                    download.file_exists = False
                    # Track trailer_deleted event for corrupted file
                    event_manager.track_trailer_deleted(
                        media_id=media.id,
                        reason="corrupted",
                        source=EventSource.SYSTEM,
                        source_detail="CleanupTask",
                    )
                else:
                    logger.warning(
                        f"The trailer for '{media.title}' {problem}."
                        f" Trailarr keeps it, because the deletion"
                        f" of bad trailers is off. Examine the file"
                        f" yourself. Path: '{_path}'.",
                        **logger.media(media.id),
                    )
    logger.info(
        f"Trailarr examined {analyzed_count} trailers."
        f" {file_missing_count} files were not on disk."
        f" {verification_failed_count} files did not pass the check."
    )
    if storage_missing_count:
        logger.warning(
            f"Trailarr did not find the files of {storage_missing_count}"
            " trailers, and their folders are empty or missing. Trailarr"
            " did not mark them as deleted. If the media is on a network"
            " drive, make sure that the drive is mounted before Trailarr"
            " starts."
        )
    return None
