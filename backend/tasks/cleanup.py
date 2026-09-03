"""Daily cleanup: old log entries, and trailers that are gone or broken.

The trailer part reads what is on disk. A file that no longer exists is
marked deleted. A file with no audio or no video is deleted, but only when
the user turned that on.
"""

import threading

import aiofiles.os
from app_logger import ModuleLogger
from config.settings import app_settings
from config.logs import manager as logs_manager
import database.manager.download as download_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.event import EventSource
from services.trailers import video_analysis
from services.files.files_handler import FilesHandler

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


async def trailer_cleanup(_stop_event: threading.Event | None = None):
    """
    Cleanup failed trailers (without audio), delete them and set monitor status to True.
    Also cleanup any residual files left in '/tmp' directory.
    """
    logger.info("Trailarr checks the trailer files on disk.")
    # Get all media from the database that are downloaded
    media_with_trailers = media_manager.read_all_generator(
        downloaded_only=True
    )
    logger.info("Trailarr examines every media item that has a trailer.")
    # Analyze the trailer files and remove the ones without audio
    analyzed_count = 0
    file_missing_count = 0
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
            if _stop_event and _stop_event.is_set():
                logger.info(
                    "Trailarr stopped the trailer check. A stop was"
                    " requested."
                )
                return

            _path = download.path
            # Skip if file has already been deleted or path is missing
            if not download.file_exists:
                continue
            analyzed_count += 1
            # Check if file exists on disk
            if not _path or not await aiofiles.os.path.exists(_path):
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
            # if not, delete the trailer file and set monitor to True
            verified = video_analysis.verify_trailer_streams(_path)
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
                        f"The trailer for '{media.title}' has no audio or no"
                        f" video. Trailarr deletes it. Path: '{_path}'.",
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
                        f"The trailer for '{media.title}' has no audio or"
                        f" no video. Trailarr keeps it, because the deletion"
                        f" of bad trailers is off. Examine the file"
                        f" yourself. Path: '{_path}'.",
                        **logger.media(media.id),
                    )
    logger.info(
        f"Trailarr examined {analyzed_count} trailers."
        f" {file_missing_count} files were not on disk."
        f" {verification_failed_count} files did not pass the check."
    )
    return None
