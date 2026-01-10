import aiofiles.os
from app_logger import ModuleLogger
from config.logs import manager as logs_manager
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
from core.download import video_analysis
from core.files_handler import FilesHandler

logger = ModuleLogger("CleanupTasks")


async def delete_old_logs():
    """
    Delete old log files from the '/config/logs' directory.
    This function is intended to be run periodically to keep the log directory clean.
    """
    logger.info("Running old logs cleanup task...")
    deleted_count = await logs_manager.delete_old_logs(30)
    logger.info(
        f"Old logs cleanup task completed. Deleted {deleted_count} logs older"
        " than 30 days."
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


async def trailer_cleanup():
    """
    Cleanup failed trailers (without audio), delete them and set monitor status to True.
    Also cleanup any residual files left in '/tmp' directory.
    """
    logger.info("Running trailer cleanup task...")
    # Get all media from the database that are downloaded
    media_with_trailers = media_manager.read_all_generator(
        downloaded_only=True
    )
    logger.info("Analyzing media items with trailers.")
    # Analyze the trailer files and remove the ones without audio
    analyzed_count = 0
    file_missing_count = 0
    verification_failed_count = 0
    for media in media_with_trailers:
        # Skip media with no downloads
        if not media.downloads:
            media_manager.update_no_trailers_exist(media.id)
            continue
        logger.debug(f"Analyzing trailers for {media.title}")
        for download in media.downloads:
            _path = download.path
            # Skip if file has already been deleted or path is missing
            if not download.file_exists:
                continue
            analyzed_count += 1
            # Check if file exists on disk
            if not _path or not await aiofiles.os.path.exists(_path):
                file_missing_count += 1
                logger.info(
                    f"Trailer file '{_path}' does not exist on disk for"
                    f" '{media.title}' [{media.id}]. Marking as deleted."
                )
                download.file_exists = False
                download_manager.mark_as_deleted(download.id)
                continue

            # Verify the trailer has audio and video streams
            # if not, delete the trailer file and set monitor to True
            verified = video_analysis.verify_trailer_streams(_path)
            if verified is None:
                logger.info(
                    f"Could not analyze trailer for {media.title} [{media.id}]"
                    f" at path '{_path}'. Skipping deletion."
                )
                continue
            elif verified is False:
                verification_failed_count += 1
                logger.info(
                    "Deleting trailer with missing audio/video for"
                    f" {media.title} [{media.id}] at path '{_path}'."
                )
                download.file_exists = False
                await delete_trailer(_path, download.id)
    logger.info(
        f"Trailer cleanup task completed. Analyzed {analyzed_count} trailers."
        f" Missing files: {file_missing_count}."
        f" Verification failed: {verification_failed_count}."
    )
    return None
