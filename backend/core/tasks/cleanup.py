import aiofiles.os
from app_logger import ModuleLogger
from config.logs import manager as logs_manager
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import MonitorStatus
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


def monitor_media(media_id: int):
    """
    Set the monitor status of the media to True. \n
    Args:
        media_id (int): ID of the media. \n
    Returns:
        None
    """
    media_manager.update_media_status(
        MediaUpdateDC(
            id=media_id,
            monitor=True,
            status=MonitorStatus.MONITORED,
            trailer_exists=False,
        )
    )
    return None


async def trailer_cleanup():
    """
    Cleanup failed trailers (without audio), delete them and set monitor status to True.
    Also cleanup any residual files left in '/tmp' directory.
    """
    logger.info("Running trailer cleanup task...")
    # Get all media from the database and filter out the ones that have no trailers
    db_media_list = media_manager.read_all()
    media_with_trailers = [
        media for media in db_media_list if len(media.downloads) > 0
    ]
    logger.info(
        f"Analyzing {len(media_with_trailers)} media items with trailers."
    )
    # Analyze the trailer files and remove the ones without audio
    for media in media_with_trailers:
        logger.debug(f"Checking trailer for {media.title}")
        for download in media.downloads:
            _path = download.path
            # Skip if file has already been deleted or path is missing
            if not download.file_exists or not _path:
                continue
            # Check if file exists on disk
            if not await aiofiles.os.path.exists(_path):
                continue

            # Verify the trailer has audio and video streams
            # if not, delete the trailer file and set monitor to True
            if not video_analysis.verify_trailer_streams(_path):
                logger.info(
                    "Deleting trailer with missing audio/video for"
                    f" {media.title}"
                )
                download.file_exists = False
                await delete_trailer(_path, download.id)
        # If no valid trailers remain, set monitor to True
        if not any(dl.file_exists for dl in media.downloads):
            logger.info(
                f"No valid trailers remain for {media.title}. Setting monitor"
                " to True."
            )
            monitor_media(media.id)
    logger.info("Trailer cleanup task completed.")
    return None
