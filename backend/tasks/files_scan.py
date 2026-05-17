import threading

from app_logger import ModuleLogger
from config.settings import app_settings
import db.repos.media as media_repo
from services.scan_service import scan_media_folder
from utils.media_scanner import MediaScanner

logger = ModuleLogger("TrailersFilesScan")


async def scan_all_media_folders(_stop_event: threading.Event | None = None) -> None:
    logger.info("Scanning disk for files and trailers.")
    force_full_scan = app_settings.files_full_scan
    if force_full_scan:
        logger.info("FILES_FULL_SCAN is enabled — running full scan, bypassing folder-change check.")

    all_media = media_repo.read_all_generator
    scanner = MediaScanner()
    media_count = 0
    new_trailers = 0
    missing_trailers = 0

    for media in all_media():
        if _stop_event and _stop_event.is_set():
            logger.info("Stop event set, terminating scan of media folders.")
            return
        try:
            media_count += 1
            new, missing = await scan_media_folder(media, scanner, user_initiated=force_full_scan)
            new_trailers += new
            missing_trailers += missing
        except Exception as e:
            logger.error(f"Error scanning media folder for '{media.title}' [{media.id}]: {e}")

    if force_full_scan:
        app_settings.files_full_scan = False
        logger.info("FILES_FULL_SCAN reset to False after full scan.")

    logger.info(
        f"Completed scanning disk for files and trailers. "
        f"Total media scanned: {media_count}. "
        f"New trailers found: {new_trailers}. "
        f"Missing trailers: {missing_trailers}."
    )
