import os
from app_logger import ModuleLogger
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.media import MediaRead
from core.base.database.models.connection import ArrType
from core.download.trailers.service import record_new_trailer_download
from core.files_handler import FilesHandler
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager

logger = ModuleLogger("TrailersFilesScan")


async def get_all_root_folders() -> set[str]:
    """Get all root folders from all connections.
    Returns:
        set[str]: Set of all root folder paths.
    """
    root_folders: set[str] = set()
    all_connections = connection_manager.read_all()

    for connection in all_connections:
        arr_manager = None
        if connection.arr_type == ArrType.RADARR:
            arr_manager = RadarrConnectionManager(connection)
        elif connection.arr_type == ArrType.SONARR:
            arr_manager = SonarrConnectionManager(connection)
        if arr_manager:
            root_folders.update(await arr_manager.get_rootfolders())

    return root_folders


def find_matching_media(
    trailer_path: str, all_media: list[MediaRead]
) -> MediaRead | None:
    """Find media IDs that match the given trailer path based on folder paths.
    Args:
        trailer_path (str): The path of the trailer file.
        all_media (list[MediaRead]): List of all media items.
    Returns:
        (MediaRead | None): The matching media, or None if no match is found.
    """
    for media in all_media:
        if media.folder_path and trailer_path.startswith(media.folder_path):
            return media
    return None


async def scan_disk_for_trailers() -> None:
    """Scan the disk for trailers and update the database with download records."""
    logger.info("Scanning disk for trailers.")

    # Get all existing downloads
    all_downloads = download_manager.read_all()
    existing_paths = {d.path for d in all_downloads}

    # Get all media items
    all_media = media_manager.read_all()

    # Get all connection root folders
    root_folders = await get_all_root_folders()

    # Scan for trailers in all root folders
    found_paths: set[str] = set()
    for root_folder in root_folders:
        for trailer_path in await FilesHandler.scan_root_folders_for_trailers(
            root_folder
        ):
            found_paths.add(trailer_path)
            # Skip if already tracked
            if trailer_path in existing_paths:
                continue

            logger.debug(f"Found new trailer: {trailer_path}")

            # Find matching media by folder path
            media_match = find_matching_media(trailer_path, all_media)

            if not media_match:
                # logger.warning(f"No media found for trailer: {trailer_path}")
                continue

            # Record the trailer download
            await record_new_trailer_download(media_match, 0, trailer_path)

    # Mark downloads as non-existent if file is deleted
    for download in all_downloads:
        if download.path in found_paths:
            continue
        if not os.path.exists(download.path):
            logger.debug(f"Trailer file deleted for download: {download.path}")
            download_manager.mark_as_deleted(download.id)

    logger.info("Finished scanning disk for trailers.")
