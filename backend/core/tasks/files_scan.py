import os
import re
from datetime import datetime, timezone
from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.manager.connection import ConnectionDatabaseManager
from core.base.database.models.connection import ArrType
from core.download.service import record_new_trailer_download
from core.download.video_analysis import get_media_info
from core.files_handler import FilesHandler
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager

logger = ModuleLogger("TrailersFilesScan")


async def scan_disk_for_trailers() -> None:
    """Scan the disk for trailers and update the database with the new status."""
    logger.info("Scanning disk for trailers.")
    db_handler = MediaDatabaseManager()
    all_media = db_handler.read_all_with_downloads()
    all_downloads = db_handler.read_all_downloads()
    existing_paths = {d.path for d in all_downloads}

    connection_db_handler = ConnectionDatabaseManager()
    all_connections = connection_db_handler.read_all()

    root_folders: set[str] = set()
    for connection in all_connections:
        arr_manager = None
        if connection.arr_type == ArrType.RADARR:
            arr_manager = RadarrConnectionManager(connection)
        elif connection.arr_type == ArrType.SONARR:
            arr_manager = SonarrConnectionManager(connection)
        if arr_manager:
            root_folders.update(await arr_manager.get_rootfolders())

    for root_folder in root_folders:
        for trailer_path in await FilesHandler.scan_root_folders_for_trailers(
            root_folder
        ):
            if trailer_path in existing_paths:
                continue

            logger.info(f"Found new trailer: {trailer_path}")
            media_match = next(
                (
                    m
                    for m in all_media
                    if m.folder_path and trailer_path.startswith(m.folder_path)
                ),
                None,
            )

            if not media_match:
                logger.warning(f"No media found for trailer: {trailer_path}")
                continue

            youtube_id = "unknown0000"
            media_info = get_media_info(trailer_path)
            if media_info:
                comment = media_info.format_name
                if "comment" in media_info.format_name:
                    match = re.search(r"https://www.youtube.com/watch\?v=([a-zA-Z0-9_-]+)", comment)
                    if match:
                        youtube_id = match.group(1)

            if youtube_id == "unknown0000" and media_match.youtube_trailer_id:
                 # Check file modification time against media download time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(trailer_path), tz=timezone.utc)
                if media_match.downloaded_at and (file_mtime - media_match.downloaded_at).total_seconds() < 3600:
                    youtube_id = media_match.youtube_trailer_id

            await record_new_trailer_download(
                media_id=media_match.id,
                profile_id=0,  # 0 for unknown profile
                file_path=trailer_path,
                youtube_video_id=youtube_id,
            )

    # Mark downloads as non-existent if file is deleted
    for download in all_downloads:
        if not os.path.exists(download.path):
            logger.info(f"Trailer file deleted: {download.path}")
            db_handler.update_download_file_exists(download.id, False)

    logger.info("Finished scanning disk for trailers.")


async def scan_and_refresh_downloads(media_id: int) -> None:
    """Scan and refresh the downloads for a media item."""
    logger.info(f"Scanning and refreshing downloads for media {media_id}")
    db_handler = MediaDatabaseManager()
    media = db_handler.read(media_id)

    if not media.folder_path:
        logger.warning(f"No folder path for media {media_id}")
        return

    # Reset media status if not downloading
    if media.status != "downloading":
        db_handler.update_trailer_exists(media.id, False)

    # Scan for new trailers
    existing_downloads = {d.path for d in media.downloads}
    for trailer_path in await FilesHandler.scan_root_folders_for_trailers(
        media.folder_path
    ):
        if trailer_path in existing_downloads:
            continue

        logger.info(f"Found new trailer for media {media_id}: {trailer_path}")
        youtube_id = "unknown0000"
        media_info = get_media_info(trailer_path)
        if media_info:
            comment = media_info.format_name
            if "comment" in media_info.format_name:
                match = re.search(r"https://www.youtube.com/watch\?v=([a-zA-Z0-9_-]+)", comment)
                if match:
                    youtube_id = match.group(1)

        if youtube_id == "unknown0000" and media.youtube_trailer_id:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(trailer_path), tz=timezone.utc)
            if media.downloaded_at and (file_mtime - media.downloaded_at).total_seconds() < 3600:
                youtube_id = media.youtube_trailer_id

        await record_new_trailer_download(
            media_id=media.id,
            profile_id=0,  # 0 for unknown profile
            file_path=trailer_path,
            youtube_video_id=youtube_id,
        )

    # Mark downloads as non-existent if file is deleted
    for download in media.downloads:
        if not os.path.exists(download.path):
            logger.info(f"Trailer file deleted: {download.path}")
            db_handler.update_download_file_exists(download.id, False)

    logger.info(f"Finished scanning and refreshing downloads for media {media_id}")
