from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import MonitorStatus
from core.download import video_analysis
from core.files_handler import FilesHandler


async def delete_trailer_and_monitor(
    trailer_path: str, media_id: int, db_manager: MediaDatabaseManager | None = None
):
    """
    Delete the trailer file and set the monitor status to True. \n
    Args:
        trailer_path (str): Path to the trailer file. \n
        media_id (int): ID of the media. \n
        db_manager (MediaDatabaseManager | None): Instance of MediaDatabaseManager. \n
    Returns:
        None
    """
    if not db_manager:
        db_manager = MediaDatabaseManager()
    await FilesHandler.delete_file(trailer_path)
    db_manager.update_media_status(
        MediaUpdateDC(
            id=media_id,
            monitor=True,
            status=MonitorStatus.MISSING,
        )
    )
    return None


async def verify_trailer_streams(trailer_path: str):
    """
    Check if the trailer has audio and video streams. \n
    Args:
        trailer_path (str): Path to the trailer file. \n
    Returns:
        bool: True if the trailer has audio and video streams, False otherwise.
    """
    # Check trailer file exists
    if not trailer_path:
        return False
    # Get media analysis for the trailer
    media_info = video_analysis.get_media_info(trailer_path)
    if media_info is None:
        return False
    # Verify the trailer has audio and video streams
    streams = media_info.streams
    if len(streams) == 0:
        return False
    audio_exists = False
    video_exists = False
    for stream in streams:
        if stream.codec_type == "audio":
            audio_exists = True
        if stream.codec_type == "video":
            video_exists = True
    if not audio_exists or not video_exists:
        return False
    return True


async def trailer_cleanup():
    """
    Cleanup failed trailers (without audio), delete them and set monitor status to True.
    Also cleanup any residual files left in '/tmp' directory.
    """
    # Get all media from the database and filter out the ones that have no trailers
    db_manager = MediaDatabaseManager()
    db_media_list = db_manager.read_all()
    media_with_trailers = [
        media for media in db_media_list if media.trailer_exists is True
    ]
    # Analyze the trailer files and remove the ones without audio
    for media in media_with_trailers:
        # Check if the trailer file exists
        if not media.folder_path:
            continue
        trailer_path = await FilesHandler.get_trailer_path(
            media.folder_path, check_inline_file=True
        )
        if not trailer_path:
            continue

        # Verify the trailer has audio and video streams
        # if not, delete the trailer file and set monitor to True
        if not await verify_trailer_streams(trailer_path):
            await delete_trailer_and_monitor(trailer_path, media.id, db_manager)
            continue
    # Cleanup any residual files left in '/tmp' directory
    await FilesHandler.cleanup_tmp_dir()
    return None
