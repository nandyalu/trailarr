import os
from app_logger import ModuleLogger
import core.base.database.manager.filefolderinfo as files_manager
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.media import MediaRead
from core.download.trailers.service import record_new_trailer_download
from backend.core.files.media_scanner import MediaScanner

logger = ModuleLogger("TrailersFilesScan")


async def scan_media_folder(
    media: MediaRead, scanner: MediaScanner | None = None
) -> tuple[int, int]:
    """Scan the media folder to find media files and trailers \
        and update the database with download records.
    Args:
        media (MediaRead): The media item to scan.
        scanner (FolderScan | None): Optional FolderScan instance to use for scanning.
    Returns:
        tuple[int, int]: A tuple containing the number of new trailer files found \
            and the number of missing trailer files.
    """
    found_paths: set[str] = set()
    if not media.folder_path:
        return 0, 0
    if scanner is None:
        scanner = MediaScanner()

    # Get the folder files info
    files_info = await scanner.get_folder_files(media.folder_path, media.id)
    if not files_info:
        return 0, 0

    # Update the file/folder info in the database
    files_manager.update(media, files_info)

    # Get trailer paths
    trailer_paths = scanner.get_trailer_paths(files_info)

    # Get all existing downloads with existing files for this media
    all_downloads = [d for d in media.downloads if d.file_exists]
    existing_paths = {d.path for d in all_downloads}

    # Check if any trailer paths are new downloads
    for t_path in trailer_paths:
        if t_path in existing_paths:
            # Already recorded as download
            continue
        # New trailer download found
        found_paths.add(t_path)
        logger.info(
            f"Found new trailer file: '{t_path}' for '{media.title}'"
            f" [{media.id}]"
        )
        await record_new_trailer_download(media, 0, t_path)
        if not media.trailer_exists:
            media.trailer_exists = True
            media_manager.update_trailer_exists(media.id, True)

    # Mark downloads as non-existent if file is deleted
    missing_count = 0
    for download in all_downloads:
        if download.path in found_paths:
            continue
        if not os.path.exists(download.path):
            missing_count += 1
            logger.info(
                f"Trailer file deleted for download: '{download.path}' for"
                f" '{media.title}' [{media.id}]"
            )
            download_manager.mark_as_deleted(download.id)

    return len(found_paths), missing_count


async def scan_all_media_folders() -> None:
    """Scan the disk for all media folders to find media files and trailers \
        and update the database with download records."""
    logger.info("Scanning disk for files and trailers.")

    # Get all media items
    all_media = media_manager.read_all_generator

    # Get a FolderScan instance
    scanner = MediaScanner()

    # Scan each media item's folder to find files
    media_count = 0
    new_trailers = 0
    missing_trailers = 0
    for media in all_media():
        try:
            media_count += 1
            new, missing = await scan_media_folder(media, scanner)
            new_trailers += new
            missing_trailers += missing
        except Exception as e:
            logger.error(
                f"Error scanning media folder for '{media.title}'"
                f" [{media.id}]: {e}"
            )
    logger.info(
        "Completed scanning disk for files and trailers. "
        f"Total media scanned: {media_count}. "
        f"New trailers found: {new_trailers}. "
        f"Missing trailers: {missing_trailers}."
    )
