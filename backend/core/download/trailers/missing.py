from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.manager import trailerprofile
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.base.utils.filters import matches_filters
from core.download import trailer as trailer_downloader
from core.files_handler import FilesHandler
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailerDownloadTasks")


def _find_matching_profiles(
    db_media: MediaRead, trailer_profiles: list[TrailerProfileRead]
) -> list[TrailerProfileRead]:
    """Find all matching profiles for a media item and return them."""
    matching_profiles = []
    for profile in trailer_profiles:
        if matches_filters(db_media, profile.customfilter.filters):
            matching_profiles.append(profile)

    # Sort profiles by priority, lower number = higher priority
    matching_profiles.sort(key=lambda p: p.priority)
    return matching_profiles


def _is_valid_media(
    db_media: MediaRead,
    skipped_titles: dict[str, list[str]],
    check_folder: bool = True,
) -> bool:
    """Check if a media item is valid for downloading."""
    if check_folder:
        if db_media.folder_path is None:
            skipped_titles["missing_folder_path"].append(db_media.title)
            return False

        if not FilesHandler.check_folder_exists(db_media.folder_path):
            skipped_titles["missing_folder_path"].append(db_media.title)
            return False

    if not app_settings.wait_for_media:
        return True

    if not db_media.folder_path:
        skipped_titles["media_not_found"].append(db_media.title)
        return False

    if not FilesHandler.check_media_exists(db_media.folder_path):
        skipped_titles["media_not_found"].append(db_media.title)
        return False

    return True


# def _check_file_already_downloaded(
#     media: MediaRead, profile: TrailerProfileRead
# ) -> bool:
#     """Check if the trailer file for the given profile already exists for media."""
#     if not media.folder_path:
#         return False

#     file_name = get_trailer_filename(media, profile, profile.file_format, 1)

#     return FilesHandler.check_file_exists(media.folder_path, file_name)


async def download_missing_trailers() -> None:
    """Download missing trailers for monitored media items."""
    # Exit if monitoring is disabled
    if not app_settings.monitor_enabled:
        logger.warning("Monitoring is disabled, skipping trailers download")
        return

    successful_downloads = 0
    skipped_items = 0

    while True:
        db_manager = MediaDatabaseManager()
        db_media_list = db_manager.read_all(None, "monitored")
        trailer_profiles = trailerprofile.get_trailerprofiles()

        if not trailer_profiles:
            logger.warning(
                "No TrailerProfiles found, skipping download trailers"
            )
            return

        enabled_profiles: list[TrailerProfileRead] = [
            p for p in trailer_profiles if p.enabled
        ]

        if not enabled_profiles:
            logger.warning(
                "No enabled TrailerProfiles found, skipping download"
            )
            return

        media_to_process = None
        matching_profiles_for_media = []

        for db_media in db_media_list:
            matching_profiles = _find_matching_profiles(
                db_media, enabled_profiles
            )
            if matching_profiles:
                media_to_process = db_media
                matching_profiles_for_media = matching_profiles
                break  # Found a media item to process

        if not media_to_process:
            logger.info("No more media items to process.")
            break

        # Process the found media item
        downloads, skips = await _process_single_media_item(
            media_to_process, matching_profiles_for_media
        )
        successful_downloads += downloads
        skipped_items += skips

    logger.info(
        "Finished downloading missing trailers. "
        f"Successful downloads: {successful_downloads}, Skipped items:"
        f" {skipped_items}"
    )


async def _process_single_media_item(
    media: MediaRead, profiles: list[TrailerProfileRead]
) -> tuple[int, int]:
    """Process a single media item and download all matching trailers."""
    successful_downloads = 0
    skipped_items = 0

    for profile in profiles:
        check_folder = profile.custom_folder == "{media_folder}"
        if not _is_valid_media(media, {}, check_folder):
            return successful_downloads, skipped_items + 1
        try:
            download_successful = await trailer_downloader.download_trailer(
                media, profile
            )
            if download_successful:
                successful_downloads += 1
                if profile.stop_monitoring:
                    logger.info(
                        f"Stopping monitoring for {media.title} after"
                        " successful download with profile:"
                        f" {profile.customfilter.filter_name}"
                    )
                    break
        except DownloadFailedError:
            logger.warning(
                f"Failed to download trailer for {media.title} with profile:"
                f" {profile.customfilter.filter_name}. Continuing to next"
                " profile."
            )
            skipped_items += 1
    return successful_downloads, skipped_items
