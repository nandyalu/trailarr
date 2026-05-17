"""Cleanup service — verify and prune stale or corrupted trailer downloads.

Iterates all media that have trailers, checks each file on disk, and
either marks missing files as deleted or deletes corrupted ones based
on the delete_corrupted_trailers setting.
"""
import threading

import aiofiles.os
from app_logger import ModuleLogger
from config.settings import app_settings
import db.repos.download as download_repo
from db.models.event import EventSource
from download import analysis as video_analysis
from services.files_service import delete_trailer_download
from services import event_service

logger = ModuleLogger("CleanupService")


async def trailer_cleanup(_stop_event: threading.Event | None = None) -> None:
    """Scan all downloaded trailers and remove or mark any that are missing or corrupted."""
    logger.info("Running trailer cleanup task...")
    import db.repos.media as media_repo
    media_with_trailers = media_repo.read_all_generator(downloaded_only=True)
    logger.info("Analyzing media items with trailers.")
    analyzed_count = 0
    file_missing_count = 0
    verification_failed_count = 0

    for media in media_with_trailers:
        if not media.downloads:
            continue
        logger.debug(f"Analyzing trailers for {media.title}")
        for download in media.downloads:
            if _stop_event and _stop_event.is_set():
                logger.info("Stop event set, terminating trailer cleanup task.")
                return

            _path = download.path
            if not download.file_exists:
                continue
            analyzed_count += 1

            if not _path or not await aiofiles.os.path.exists(_path):
                file_missing_count += 1
                logger.info(
                    f"Trailer file '{_path}' does not exist on disk"
                    f" for '{media.title}' [{media.id}]. Marking as deleted."
                )
                download.file_exists = False
                download_repo.mark_as_deleted(download.id)
                event_service.track_trailer_deleted(
                    media_id=media.id,
                    reason="file_not_found",
                    source=EventSource.SYSTEM,
                    source_detail="CleanupTask",
                )
                continue

            verified = video_analysis.verify_trailer_streams(_path)
            if verified is None:
                logger.info(
                    f"Could not analyze trailer for {media.title} [{media.id}]"
                    f" at path '{_path}'. Skipping deletion."
                )
                continue
            elif verified is False:
                verification_failed_count += 1
                if app_settings.delete_corrupted_trailers:
                    logger.info(
                        f"Deleting trailer with missing audio/video"
                        f" for {media.title} [{media.id}] at path '{_path}'."
                    )
                    await delete_trailer_download(_path, download.id)
                    download.file_exists = False
                    event_service.track_trailer_deleted(
                        media_id=media.id,
                        reason="corrupted",
                        source=EventSource.SYSTEM,
                        source_detail="CleanupTask",
                    )
                else:
                    logger.warning(
                        f"Corrupted trailer found (missing audio/video)"
                        f" for {media.title} [{media.id}] at path '{_path}',"
                        " but deletion is disabled. Please check manually."
                    )

    logger.info(
        f"Trailer cleanup task completed. Analyzed {analyzed_count} trailers."
        f" Missing files: {file_missing_count}."
        f" Verification failed: {verification_failed_count}."
    )
