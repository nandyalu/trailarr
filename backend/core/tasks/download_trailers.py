from datetime import datetime, timedelta
import os
from random import randint
import time

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.manager import trailerprofile
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.filter import (
    FilterCondition,
    FilterRead,
)
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.trailer import download_trailer
from core.files_handler import FilesHandler
from core.tasks import scheduler
from exceptions import (
    DownloadFailedError,
    FolderNotFoundError,
    FolderPathEmptyError,
)

logger = ModuleLogger("TrailerDownloadTasks")


def matches_filters(media: MediaRead, filters: list[FilterRead]) -> bool:
    """Check if a media item matches the given filters.
    Args:
        media (MediaRead): The media item to check.
        filters (list[Filter]): The list of filters to apply.
    Returns:
        bool: True if the media item matches all filters, False otherwise.
    """
    for filter in filters:
        media_value = getattr(media, filter.filter_by, None)
        filter_value = filter.filter_value

        # Perform type-specific comparisons
        if isinstance(media_value, bool):
            if filter.filter_condition == FilterCondition.EQUALS:
                if media_value != (filter.filter_value.lower() == "true"):
                    return False
            elif filter.filter_condition == FilterCondition.NOT_EQUALS:
                if media_value == (filter.filter_value.lower() == "true"):
                    return False
            else:
                return False  # Unsupported condition for booleans

        elif isinstance(media_value, (int, float)):
            filter_value = float(filter.filter_value)
            if filter.filter_condition == FilterCondition.EQUALS:
                if media_value != filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.NOT_EQUALS:
                if media_value == filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.GREATER_THAN:
                if not media_value > filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.GREATER_THAN_EQUAL:
                if not media_value >= filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.LESS_THAN:
                if not media_value < filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.LESS_THAN_EQUAL:
                if not media_value <= filter_value:
                    return False
            else:
                return False  # Unsupported condition for numbers

        elif isinstance(media_value, datetime):
            # Check number filter_value comparisions first
            if filter.filter_condition == FilterCondition.IN_THE_LAST:
                _delta = media_value.date() - datetime.now().date()
                if _delta.days > int(filter.filter_value):
                    return False
            elif filter.filter_condition == FilterCondition.NOT_IN_THE_LAST:
                _delta = media_value.date() - datetime.now().date()
                if _delta.days <= int(filter.filter_value):
                    return False
            else:
                # Convert filter_value to datetime for comparison
                # Assuming filter_value is in the format "YYYY-MM-DD"
                try:
                    filter_date = datetime.strptime(
                        filter.filter_value, "%Y-%m-%d"
                    )
                except ValueError:
                    return False  # Invalid date format in filter_value

                # Compare only the date part, ignoring the time part
                if filter.filter_condition == FilterCondition.EQUALS:
                    if media_value.date() != filter_date.date():
                        return False
                elif filter.filter_condition == FilterCondition.NOT_EQUALS:
                    if media_value.date() == filter_date.date():
                        return False
                elif filter.filter_condition == FilterCondition.IS_AFTER:
                    if media_value.date() < filter_date.date():
                        return False
                elif filter.filter_condition == FilterCondition.IS_BEFORE:
                    if media_value.date() > filter_date.date():
                        return False
                else:
                    return False  # Unsupported condition for dates

        elif isinstance(media_value, str):
            if filter.filter_condition == FilterCondition.EQUALS:
                if media_value != filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.NOT_EQUALS:
                if media_value == filter_value:
                    return False
            elif filter.filter_condition == FilterCondition.CONTAINS:
                if filter.filter_value not in media_value:
                    return False
            elif filter.filter_condition == FilterCondition.NOT_CONTAINS:
                if filter.filter_value in media_value:
                    return False
            elif filter.filter_condition == FilterCondition.STARTS_WITH:
                if not media_value.startswith(filter.filter_value):
                    return False
            elif filter.filter_condition == FilterCondition.NOT_STARTS_WITH:
                if media_value.startswith(filter.filter_value):
                    return False
            elif filter.filter_condition == FilterCondition.ENDS_WITH:
                if not media_value.endswith(filter.filter_value):
                    return False
            elif filter.filter_condition == FilterCondition.NOT_ENDS_WITH:
                if media_value.endswith(filter.filter_value):
                    return False
            elif filter.filter_condition == FilterCondition.IS_EMPTY:
                if media_value.strip():
                    return False
            elif filter.filter_condition == FilterCondition.IS_NOT_EMPTY:
                if not media_value.strip():
                    return False
            else:
                return False  # Unsupported condition for strings

        else:
            if filter.filter_condition == FilterCondition.IS_EMPTY:
                if media_value is not None:
                    return False
            elif filter.filter_condition == FilterCondition.IS_NOT_EMPTY:
                if media_value is None:
                    return False
            else:
                # Unsupported media_value type
                return False
    return True


def download_missing_trailers() -> None:
    """Download missing trailers for monitored media items. \n
    🚨 This function needs to be called from a background task. 🚨
    """
    # Check if monitoring is enabled
    if not app_settings.monitor_enabled:
        logger.warning("Monitoring is disabled, skipping trailers download")
        return None

    db_manager = MediaDatabaseManager()
    db_media_list = db_manager.read_all()
    trailer_profiles = trailerprofile.get_trailerprofiles()

    if not trailer_profiles:
        logger.warning("No TrailerProfiles found, skipping download trailers")
        return None

    logger.debug(
        f"Checking trailers for {len(db_media_list)} monitored media items"
    )
    skipped_titles: dict[str, list[str]] = {
        "no_matching_profile": [],
        "missing_folder_path": [],
        "media_not_found": [],
    }

    # Group media items by TrailerProfile
    profile_to_media_map: dict[TrailerProfileRead, list[MediaRead]] = {
        profile: [] for profile in trailer_profiles
    }

    _download_count = 0
    # Iterate through media items and check for matching profiles
    for db_media in db_media_list:
        matched_profile = None
        for profile in trailer_profiles:
            if matches_filters(db_media, profile.customfilter.filters):
                matched_profile = profile
                break

        if not matched_profile:
            skipped_titles["no_matching_profile"].append(db_media.title)
            continue

        if db_media.folder_path is None:
            skipped_titles["missing_folder_path"].append(db_media.title)
            continue

        if not os.path.exists(db_media.folder_path):
            skipped_titles["missing_folder_path"].append(db_media.title)
            continue

        if app_settings.wait_for_media:
            if not FilesHandler.check_media_exists(db_media.folder_path):
                skipped_titles["media_not_found"].append(db_media.title)
                continue

        _download_count += 1
        profile_to_media_map[matched_profile].append(db_media)

    # Log skipped media titles
    for skip_reason, skip_titles in skipped_titles.items():
        skip_reason = skip_reason.replace("_", " ")
        logger.debug(f"Skipped {len(skip_titles)} titles - {skip_reason}")
    _skip_count = sum(len(titles) for titles in skipped_titles.values())
    logger.info(
        f"Total {len(db_media_list)} media items checked. "
        f"Skipped: {_skip_count}, Download needed: {_download_count}"
    )

    # Call download_trailers for each profile with its media list
    _downloading_count = 1
    for profile, media_list in profile_to_media_map.items():
        if not media_list:
            continue
        logger.info(
            f"Downloading trailers for {len(media_list)} media items using"
            f" profile: {profile.customfilter.filter_name}"
        )
        # Download trailers for the media list and profile
        batch_download_task(
            media_list,
            profile,
            downloading_count=_downloading_count,
            download_count=_download_count,
        )
        _downloading_count += len(media_list)

    return None


def download_trailer_by_id(
    media_id: int, profile_id: int, yt_id: str = ""
) -> str:
    """Download trailer for a media by ID with given profile.
    Schedules a background job to download it. \n
    Args:
        media_id (int): The ID of the media to download the trailer for.
        profile_id (int): The ID of the trailer profile to use.
        yt_id (str, optional): YouTube ID of the trailer. Defaults to "".
    Returns:
        str: Message indicating the status of the download.
    Raises:
        ItemNotFoundError: If the media or profile is not found.
        FolderPathEmptyError: If the media folder path is empty.
        FolderNotFoundError: If the media folder path does not exist.
    """
    _type = "Media"
    retry_count = 3
    db_manager = MediaDatabaseManager()
    # Check if media with the given ID exists
    media = db_manager.read(media_id)
    _type = "Movie" if media.is_movie else "Series"
    # Check if trailer profile with the given ID exists
    profile = trailerprofile.get_trailerprofile(profile_id)

    logger.info(f"Downloading trailer for {media.title} [{media_id}]")

    if not media.folder_path:
        msg = f"{_type} '{media.title}' [{media.id}] has no folder path"
        raise FolderPathEmptyError(msg)

    if not os.path.exists(media.folder_path):
        raise FolderNotFoundError(folder_path=media.folder_path)

    if yt_id:
        # If yt_id is provided, always use it,
        # disable retries as retries will download a different trailer
        retry_count = 0
        media.youtube_trailer_id = yt_id
    elif profile.always_search:
        # If always search is enabled, do not use the id from the database
        media.youtube_trailer_id = None

    # Add Job to scheduler to download trailer
    scheduler.add_job(
        func=download_trailer,
        args=(media, profile, retry_count),
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=1),
        id=f"download_trailer_by_id_{media_id}",
        name=f"Download Trailer for {media.title}",
        max_instances=1,
    )
    msg = "Trailer download started in background for "
    msg += f"{_type}: '{media.title}' [{media_id}]"
    if yt_id:
        msg += f" from ({yt_id})"

    logger.info(msg)
    return msg


def batch_download_task(
    media_list: list[MediaRead],
    profile: TrailerProfileRead,
    downloading_count: int | None = None,
    download_count: int | None = None,
) -> None:
    """Download trailers for a list of media IDs with given profile. \n
    🚨 This function needs to be called from a background task. 🚨
    Args:
        media_list (list[MediaRead]): List of media objects to download trailers for.
        profile (TrailerProfileRead): The trailer profile to use for download.
        downloading_count (int, optional=None): The current downloading count.
        download_count (int, optional=None): The total download count.
    Returns:
        None
    """
    if downloading_count is None:
        downloading_count = 1
    if download_count is None:
        download_count = len(media_list)
    for media in media_list:
        logger.info(
            f"Downloading trailer {downloading_count}/{download_count}"
        )
        try:
            download_trailer(media, profile)
        except DownloadFailedError as e:
            logger.error(e)
        except Exception as e:
            logger.error(
                "Unexpected error downloading trailer for media"
                f" '{media.title}' [{media.id}]: {e}"
            )
        finally:
            downloading_count += 1
        _sleep_for = 100 + randint(0, 50)
        logger.debug(
            f"Sleeping for {_sleep_for} seconds before next download..."
        )
        time.sleep(_sleep_for)
    return None


def batch_download_trailers(profile_id: int, media_ids: list[int]) -> None:
    """Download trailers for a list of media IDs. \n
    Schedules a background job to download them. \n
    Args:
        profile_id (int): The ID of the trailer profile to use for download.
        media_ids (list[int]): List of media IDs to download trailers for.
    Returns:
        None
    Raises:
        ItemNotFoundError: If the trailer profile with the given ID is not found.
    """
    profile = trailerprofile.get_trailerprofile(profile_id)
    db_manager = MediaDatabaseManager()
    media_trailer_list: list[MediaRead] = []
    skipped_titles = {
        "invalid_media_id": [],
        "missing_folder_path": [],
        "trailer_exists": [],
        "media_not_found": [],
    }
    for media_id in media_ids:
        try:
            db_media = db_manager.read(media_id)
        except Exception:
            skipped_titles["invalid_media_id"].append(media_id)
            continue
        if db_media.folder_path is None:
            skipped_titles["missing_folder_path"].append(db_media.title)
            continue
        if not os.path.exists(db_media.folder_path):
            skipped_titles["missing_folder_path"].append(db_media.title)
            continue
        if db_media.trailer_exists:
            skipped_titles["trailer_exists"].append(db_media.title)
            continue
        if app_settings.wait_for_media:
            if not FilesHandler.check_media_exists(db_media.folder_path):
                skipped_titles["media_not_found"].append(db_media.title)
                continue
        media_trailer_list.append(db_media)

    # Log skipped media titles
    for skip_reason in skipped_titles:
        skip_titles = skipped_titles[skip_reason]
        if len(skip_titles) > 0:
            all_titles = ", ".join(skip_titles)
        else:
            all_titles = "None"
        skip_reason = skip_reason.replace("_", " ")
        # logger.debug(f"Skipped {len(skip_titles)} titles - {skip_reason}")
        logger.debug(
            f"Skipped {len(skip_titles)} titles - {skip_reason}: {all_titles}"
        )

    # Return if no media to download
    if not media_trailer_list:
        logger.info("No missing trailers to download")
        return
    # Add Job to scheduler to download trailers
    scheduler.add_job(
        func=batch_download_task,
        args=(media_trailer_list, profile),
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=1),
        id="batch_download_trailers",
        name="Batch Download Trailers",
        max_instances=1,
    )
