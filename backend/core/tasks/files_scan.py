import os
from app_logger import ModuleLogger
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.media import MediaRead
from core.base.database.models.connection import ArrType
from core.download.trailers.service import record_new_trailer_download
from core.download.video_analysis import VideoInfo, get_media_info
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


def find_youtube_id(media_info: VideoInfo, media_match: MediaRead) -> str:
    """Find the YouTube ID for a trailer based on its path.
    Args:
        trailer_path (str): The path of the trailer file.
        all_media (list[MediaRead]): List of all media items.
    Returns:
        str: The YouTube ID if found, else `unknown0000`.
    """
    youtube_id = media_info.youtube_id or "unknown0000"
    if youtube_id == "unknown0000" and media_match.youtube_trailer_id:
        # Check if file was recently created (within 1 hour of download)
        if media_match.downloaded_at:
            time_diff = abs(
                (
                    media_info.created_at - media_match.downloaded_at
                ).total_seconds()
            )
            if time_diff < 3600:  # Within 1 hour
                youtube_id = media_match.youtube_trailer_id
    return youtube_id


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
            # Skip if already tracked
            if trailer_path in existing_paths:
                found_paths.add(trailer_path)
                continue

            logger.info(f"Found new trailer: {trailer_path}")

            # Find matching media by folder path
            media_match = find_matching_media(trailer_path, all_media)

            if not media_match:
                # logger.warning(f"No media found for trailer: {trailer_path}")
                continue

            # Extract metadata from the trailer file
            media_info = get_media_info(trailer_path)
            if not media_info:
                # logger.warning(f"Could not extract info from: {trailer_path}")
                continue

            # Determine YouTube ID - use extracted one or fallback to media's known ID
            youtube_id = find_youtube_id(media_info, media_match)

            # Record the trailer download
            await record_new_trailer_download(
                media_match.id, 0, trailer_path, youtube_id, media_info
            )

    # Mark downloads as non-existent if file is deleted
    for download in all_downloads:
        if download.path in found_paths:
            continue
        if not os.path.exists(download.path):
            logger.info(f"Trailer file deleted: {download.path}")
            download_manager.mark_as_deleted(download.id)

    logger.info("Finished scanning disk for trailers.")
