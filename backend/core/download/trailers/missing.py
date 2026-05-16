import threading

from app_logger import ModuleLogger
from config.settings import app_settings
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
import core.base.database.manager.trailerprofile as trailerprofile_manager
import core.base.database.manager.trailerstatusmanager as trailer_status_manager
from core.base.database.models.mediatrailerstatus import TrailerStatusEnum
from core.download import trailer as trailer_downloader
from core.download.trailers import utils
from core.files_handler import FilesHandler
from exceptions import DownloadFailedError, ItemNotFoundError

logger = ModuleLogger("TrailerDownloadTasks")


def _is_valid_media(
    db_media,
    check_folder: bool = True,
) -> bool:
    """Check if a media item is valid for downloading."""
    if check_folder:
        if db_media.folder_path is None:
            logger.info(
                f"Media '{db_media.title}' [{db_media.id}] skipped: missing"
                " folder path."
            )
            event_manager.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Missing folder path",
                source_detail="DownloadMissingTrailers",
            )
            return False

        if not FilesHandler.check_folder_exists(db_media.folder_path):
            logger.info(
                f"Media '{db_media.title}' [{db_media.id}] skipped: folder"
                " does not exist."
            )
            event_manager.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Folder does not exist",
                source_detail="DownloadMissingTrailers",
            )
            return False

    if not app_settings.wait_for_media:
        return True

    if not db_media.folder_path:
        logger.info(
            f"Media '{db_media.title}' [{db_media.id}] skipped: missing folder"
            " path."
        )
        event_manager.track_download_skipped(
            media_id=db_media.id,
            skip_reason="Missing media folder path",
            source_detail="DownloadMissingTrailers",
        )
        return False

    if not FilesHandler.check_media_exists(db_media.folder_path):
        logger.info(
            f"Media '{db_media.title}' [{db_media.id}] skipped: media file"
            " does not exist."
        )
        event_manager.track_download_skipped(
            media_id=db_media.id,
            skip_reason="Media file not found",
            source_detail="DownloadMissingTrailers",
        )
        return False

    return True


async def download_missing_trailers(
    _stop_event: threading.Event | None = None,
) -> None:
    """Download missing trailers by working through PENDING MediaTrailerStatus rows.

    Rows are pulled in priority order (profile.priority ASC, media_id, sequence ASC).
    On success the row is marked DOWNLOADED (via record_new_trailer_download).
    On failure after all retries the row is marked FAILED.
    When stop_monitoring=True on the profile, all remaining PENDING rows for the
    same media are marked SKIPPED so lower-priority profiles are not attempted.
    """
    if not app_settings.monitor_enabled:
        logger.warning("Monitoring is disabled, skipping trailers download")
        return

    total_attempted = 0
    successful_downloads = 0
    failed_downloads = 0
    # Track media_ids whose folder/media we cannot access this run to avoid
    # repeatedly re-querying the same unresolvable media.
    skipped_media_ids: set[int] = set()

    while True:
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Stop event set, terminating download of missing trailers."
            )
            return

        # Fetch a batch so we can filter out already-skipped media without
        # needing an extra DB round-trip per row.
        batch = trailer_status_manager.get_pending_rows(limit=50)
        # Filter rows whose media we already know is inaccessible this run.
        eligible = [r for r in batch if r.media_id not in skipped_media_ids]

        if not eligible:
            logger.info("No more PENDING trailer status rows to process.")
            break

        row = eligible[0]

        # Load media
        try:
            db_media = media_manager.read(row.media_id)
        except (ItemNotFoundError, Exception) as e:
            logger.warning(
                f"Media {row.media_id} not found for status row {row.id}"
                f" — marking FAILED. Error: {e}"
            )
            trailer_status_manager.update_row_status(row.id, TrailerStatusEnum.FAILED)
            failed_downloads += 1
            continue

        # Load profile
        try:
            profile = trailerprofile_manager.get_trailerprofile(row.profile_id)
        except (ItemNotFoundError, Exception) as e:
            logger.warning(
                f"Profile {row.profile_id} not found for status row {row.id}"
                f" — marking SKIPPED. Error: {e}"
            )
            trailer_status_manager.update_row_status(row.id, TrailerStatusEnum.SKIPPED)
            continue

        if not profile.enabled:
            logger.info(
                f"Profile '{profile.customfilter.filter_name}' is disabled"
                f" — marking row {row.id} SKIPPED."
            )
            trailer_status_manager.update_row_status(row.id, TrailerStatusEnum.SKIPPED)
            continue

        check_folder = profile.custom_folder == "{media_folder}"
        if not _is_valid_media(db_media, check_folder):
            # Folder/media not yet accessible — leave PENDING, skip this
            # media for the remainder of this run.
            skipped_media_ids.add(row.media_id)
            continue

        _profile_name = profile.customfilter.filter_name
        logger.info(
            f"Downloading trailer for '{db_media.title}' [{db_media.id}]"
            f" using profile '{_profile_name}' (row {row.id},"
            f" sequence {row.sequence})"
        )

        try:
            if _stop_event and _stop_event.is_set():
                logger.info(
                    "Stop event set, terminating download of missing trailers."
                )
                return

            download_successful = await trailer_downloader.download_trailer(
                db_media,
                profile,
                profile.retry_count,
                _stop_event=_stop_event,
                status_row_id=row.id,
            )
            total_attempted += 1

            if download_successful:
                successful_downloads += 1
                if profile.stop_monitoring:
                    skipped = trailer_status_manager.set_pending_rows_skipped_for_media(
                        db_media.id, exclude_row_id=row.id
                    )
                    if skipped:
                        logger.info(
                            f"stop_monitoring=True — marked {skipped} sibling"
                            f" PENDING row(s) for media {db_media.id} as SKIPPED."
                        )

        except DownloadFailedError:
            total_attempted += 1
            failed_downloads += 1
            logger.warning(
                f"Download failed for '{db_media.title}' with profile"
                f" '{_profile_name}' after all retries — marking row {row.id} FAILED."
            )
            trailer_status_manager.update_row_status(row.id, TrailerStatusEnum.FAILED)
        except Exception as e:
            total_attempted += 1
            failed_downloads += 1
            logger.exception(
                f"Unexpected error processing row {row.id} for"
                f" '{db_media.title}' [{db_media.id}]: {e}"
            )
            trailer_status_manager.update_row_status(row.id, TrailerStatusEnum.FAILED)

        await utils.sleep_between_downloads(total_attempted, logger)

    logger.info(
        "Finished downloading missing trailers."
        f" Attempted: {total_attempted},"
        f" Successful: {successful_downloads},"
        f" Failed: {failed_downloads}."
    )
