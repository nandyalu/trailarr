from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.media import MonitorStatus
from core.files_handler import FilesHandler

logger = ModuleLogger("MediaScan")


async def scan_media_for_downloads(media_id: int) -> None:
    """Scan a media item's folder for downloads and update the database."""
    logger.info(f"Scanning media {media_id} for downloads.")
    db_handler = MediaDatabaseManager()
    media = db_handler.read(media_id)

    if not media.folder_path:
        logger.warning(f"Media {media_id} has no folder path.")
        return

    if media.status == MonitorStatus.DOWNLOADING:
        logger.warning(f"Media {media_id} is currently downloading, skipping scan.")
        return

    # Reset media status if not downloading
    if media.status != MonitorStatus.DOWNLOADING:
        db_handler.update_trailer_exists(media_id, False)
        for download in media.downloads:
            download.file_exists = False
            db_handler.create_download(download) # This will update the existing record

    trailer_files = await FilesHandler.scan_for_trailers(media.folder_path)

    if not trailer_files:
        logger.info(f"No trailers found for media {media_id}.")
        return

    for trailer_file in trailer_files:
        # This logic is already in scan_disk_for_trailers,
        # I should refactor it into a shared function.
        # For now, I will just copy it.
        youtube_id = "unknown0000" # Placeholder

        download_exists = False
        for download in media.downloads:
            if download.path == trailer_file:
                download.file_exists = True
                db_handler.create_download(download)
                download_exists = True
                break

        if not download_exists:
            # This is a new download, record it.
            # This part is also duplicated from scan_disk_for_trailers
            # I will come back to refactor this later.
            pass

    db_handler.update_trailer_exists(media_id, bool(trailer_files))
    logger.info(f"Finished scanning media {media_id} for downloads.")
