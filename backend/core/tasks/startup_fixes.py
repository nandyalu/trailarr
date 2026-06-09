from app_logger import ModuleLogger
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
import core.base.database.manager.trailerprofile as trailerprofile_manager

logger = ModuleLogger("StartupFixes")


async def fix_trailer_exists_flags():
    """
    One-time startup fix: find unmonitored media (monitor=False, trailer_exists=False)
    that has a download with file_exists=True linked to a profile with stop_monitoring=True,
    and set trailer_exists=True on those items.

    This corrects a data inconsistency introduced when a file size limit caused valid
    downloaded trailers to not be tracked, leaving trailer_exists=False even though the
    file was downloaded and monitoring was stopped.
    """
    logger.info("Running startup fix: checking for incorrect trailer_exists flags...")

    # Cache profile stop_monitoring values to avoid repeated DB lookups
    profile_stop_monitoring: dict[int, bool] = {}
    for profile in trailerprofile_manager.get_trailerprofiles():
        if profile.id is not None:
            profile_stop_monitoring[profile.id] = profile.stop_monitoring

    if not profile_stop_monitoring:
        logger.info("No trailer profiles found, skipping fix.")
        return

    fix_ids: list[int] = []

    for media in media_manager.read_all_generator():
        if media.monitor or media.trailer_exists:
            continue
        downloads = download_manager.read_by_media_id(media.id)
        for download in downloads:
            if not download.file_exists:
                continue
            if profile_stop_monitoring.get(download.profile_id, False):
                fix_ids.append(media.id)
                break  # one qualifying download is enough

    if not fix_ids:
        logger.info("Startup fix: no incorrect trailer_exists flags found.")
        return

    for media_id in fix_ids:
        media_manager.update_trailer_exists(media_id, True)
    logger.info(
        f"Startup fix: corrected trailer_exists and status for {len(fix_ids)} media item(s)."
    )
