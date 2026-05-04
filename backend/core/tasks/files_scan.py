import os
import threading
from datetime import datetime, timezone
from app_logger import ModuleLogger
from config.settings import app_settings
import core.base.database.manager.event as event_manager
import core.base.database.manager.filefolderinfo as files_manager
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.event import EventSource
from core.base.database.models.media import MediaRead
from core.download.trailers.service import record_new_trailer_download
from core.files.media_scanner import MediaScanner

logger = ModuleLogger("TrailersFilesScan")


def _ctime_matches_stored(ctime: float, stored: datetime) -> bool:
    """Compare filesystem st_ctime (UTC epoch float) to a stored datetime.
    SQLite returns naive datetimes in local time — use .astimezone() to convert
    to UTC, not .replace() which would mislabel local time as UTC."""
    if stored.tzinfo is None:
        stored = stored.astimezone(timezone.utc)
    return abs(ctime - stored.timestamp()) <= 1


def _has_folder_changed(folder_path: str, media_id: int, tz) -> bool:
    """Check root folder and immediate subdirs against stored modified times.
    Returns True if a scan is needed, False if nothing has changed."""
    stored = files_manager.get_folder_modified_times(media_id)
    if not stored:
        return True  # No stored data — first scan

    try:
        stored_root = stored.get(folder_path)
        if stored_root is None or not _ctime_matches_stored(
            os.stat(folder_path).st_ctime, stored_root
        ):
            return True

        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    stored_sub = stored.get(entry.path)
                    ctime = entry.stat(follow_symlinks=False).st_ctime
                    ctime_local = datetime.fromtimestamp(ctime, tz=tz)
                    ctime_utc = ctime_local.astimezone(timezone.utc)
                    if stored_sub is None or not _ctime_matches_stored(
                        ctime_utc.timestamp(), stored_sub
                    ):
                        return True
    except OSError:
        return True  # Can't stat — safer to scan

    return False


async def scan_media_folder(
    media: MediaRead,
    scanner: MediaScanner | None = None,
    user_initiated: bool = True,
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
    if not media.folder_path:
        return 0, 0
    if scanner is None:
        scanner = MediaScanner()
    if not user_initiated and not _has_folder_changed(
        media.folder_path, media.id, scanner.tz
    ):
        return 0, 0
    logger.debug(
        f"Scanning files for '{media.title}' [{media.id}] — folder changed"
    )

    # Get the folder files info
    files_info = await scanner.get_folder_files(media.folder_path, media.id)
    if not files_info:
        # Folder is gone — reset both flags if they are stale
        if media.trailer_exists:
            media_manager.update_trailer_exists(media.id, False)
        if media.media_exists:
            media_manager.update_media_exists(media.id, False)
        return 0, 0

    # Update the file/folder info in the database
    files_manager.update(media, files_info)

    # Sync media_exists with what is actually on disk
    disk_media_exists = await scanner.check_media_exists(files_info)
    if disk_media_exists != media.media_exists:
        media_manager.update_media_exists(media.id, disk_media_exists)

    # Get trailer paths
    trailer_paths = scanner.get_trailer_paths(files_info)

    # Get all existing downloads with existing files for this media
    all_downloads = [d for d in media.downloads if d.file_exists]
    existing_paths = {d.path for d in all_downloads}

    # Check if any trailer paths are new downloads
    new_count = 0
    _source = EventSource.USER if user_initiated else EventSource.SYSTEM
    for t_path in trailer_paths:
        if t_path in existing_paths:
            # Already recorded as download
            continue
        # New trailer download found
        new_count += 1
        logger.info(
            f"Found new trailer file: '{t_path}' for '{media.title}'"
            f" [{media.id}]"
        )
        await record_new_trailer_download(media, 0, t_path)
        event_manager.track_trailer_detected(
            media_id=media.id,
            source=_source,
            source_detail="FilesScan",
        )
        if not media.trailer_exists:
            media.trailer_exists = True
            media_manager.update_trailer_exists(media.id, True)

    # Mark downloads as non-existent if file is deleted
    missing_count = 0
    for download in all_downloads:
        if download.path in trailer_paths:
            # Already found in current scan
            continue
        if not os.path.exists(download.path):
            missing_count += 1
            logger.info(
                f"Trailer file deleted for download: '{download.path}' for"
                f" '{media.title}' [{media.id}]"
            )
            download_manager.mark_as_deleted(download.id)
            event_manager.track_trailer_deleted(
                media_id=media.id,
                reason="file_not_found",
                source=_source,
                source_detail="FilesScan",
            )

    # If no trailer files exist on disk but media is marked as having trailers, reset
    if not trailer_paths and media.trailer_exists:
        media.trailer_exists = False
        media_manager.update_trailer_exists(media.id, False)

    return new_count, missing_count


async def scan_all_media_folders(
    _stop_event: threading.Event | None = None,
) -> None:
    """Scan the disk for all media folders to find media files and trailers \
        and update the database with download records."""
    logger.info("Scanning disk for files and trailers.")

    force_full_scan = app_settings.files_full_scan
    if force_full_scan:
        logger.info(
            "FILES_FULL_SCAN is enabled — running full scan,"
            " bypassing folder-change check."
        )

    # Get all media items
    all_media = media_manager.read_all_generator

    # Get a FolderScan instance
    scanner = MediaScanner()

    # Scan each media item's folder to find files
    media_count = 0
    new_trailers = 0
    missing_trailers = 0
    for media in all_media():
        if _stop_event and _stop_event.is_set():
            logger.info("Stop event set, terminating scan of media folders.")
            return

        try:
            media_count += 1
            new, missing = await scan_media_folder(
                media, scanner, user_initiated=force_full_scan
            )
            new_trailers += new
            missing_trailers += missing
        except Exception as e:
            logger.error(
                f"Error scanning media folder for '{media.title}'"
                f" [{media.id}]: {e}"
            )

    # Auto-reset so the optimisation resumes on future scans
    if force_full_scan:
        app_settings.files_full_scan = False
        logger.info("FILES_FULL_SCAN reset to False after full scan.")

    logger.info(
        "Completed scanning disk for files and trailers. "
        f"Total media scanned: {media_count}. "
        f"New trailers found: {new_trailers}. "
        f"Missing trailers: {missing_trailers}."
    )
