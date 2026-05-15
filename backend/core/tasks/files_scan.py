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


def _handle_folder_gone(media: MediaRead) -> None:
    """Reset stale flags when the media folder is inaccessible or deleted."""
    if media.media_exists:
        media_manager.update_media_exists(media.id, False)


async def _process_trailer_changes(
    media: MediaRead,
    trailer_paths: set[str],
    existing_downloads: list,
    source: EventSource,
) -> tuple[int, int]:
    """Detect new trailers and mark deleted downloads.

    Returns:
        tuple[int, int]: (new_trailer_count, missing_trailer_count)
    """
    existing_paths = {d.path for d in existing_downloads}

    # New trailer files found on disk that are not yet recorded as downloads
    new_count = 0
    for t_path in trailer_paths:
        if t_path in existing_paths:
            continue
        new_count += 1
        logger.info(
            f"Found new trailer file: '{t_path}' for '{media.title}'"
            f" [{media.id}]"
        )
        await record_new_trailer_download(media, 0, t_path)
        event_manager.track_trailer_detected(
            media_id=media.id,
            source=source,
            source_detail="FilesScan",
        )

    # Downloads whose file no longer exists on disk
    missing_count = 0
    for download in existing_downloads:
        if download.path in trailer_paths:
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
                source=source,
                source_detail="FilesScan",
            )

    return new_count, missing_count


async def scan_media_folder(
    media: MediaRead,
    scanner: MediaScanner | None = None,
    user_initiated: bool = True,
) -> tuple[int, int]:
    """Scan the media folder to find media files and trailers \
        and update the database with download records.
    Args:
        media (MediaRead): The media item to scan.
        scanner (MediaScanner | None): Optional scanner instance to use.
        user_initiated (bool): When False, skips scan if folder is unchanged.
    Returns:
        tuple[int, int]: Number of new trailer files found and missing trailers.
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

    files_info = await scanner.get_folder_files(media.folder_path, media.id)
    if not files_info:
        _handle_folder_gone(media)
        return 0, 0

    files_manager.update(media, files_info)

    disk_media_exists = await scanner.check_media_exists(files_info)
    if disk_media_exists != media.media_exists:
        media_manager.update_media_exists(media.id, disk_media_exists)

    trailer_paths = scanner.get_trailer_paths(files_info)
    all_downloads = [d for d in media.downloads if d.file_exists]
    source = EventSource.USER if user_initiated else EventSource.SYSTEM
    return await _process_trailer_changes(
        media, trailer_paths, all_downloads, source
    )


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
