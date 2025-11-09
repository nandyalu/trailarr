import asyncio
from datetime import datetime, timedelta

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.manager import trailerprofile
import core.base.database.manager.media as media_manager
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.trailer import download_trailer
from core.download.trailers.batch import batch_download_task
from core.files_handler import FilesHandler
from core.tasks import scheduler
from exceptions import (
    FolderNotFoundError,
    FolderPathEmptyError,
)

logger = ModuleLogger("TrailerDownloadTasks")


def _download_trailer(
    media: MediaRead,
    profile: TrailerProfileRead,
    retry_count: int,
) -> None:
    """Run the async task in a separate event loop."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(download_trailer(media, profile, retry_count))
    new_loop.close()
    return


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
    # Check if media with the given ID exists
    media = media_manager.read(media_id)
    _type = "Movie" if media.is_movie else "Series"
    # Check if trailer profile with the given ID exists
    profile = trailerprofile.get_trailerprofile(profile_id)

    logger.info(f"Downloading trailer for {media.title} [{media_id}]")

    if not media.folder_path:
        msg = f"{_type} '{media.title}' [{media.id}] has no folder path"
        raise FolderPathEmptyError(msg)

    if not FilesHandler.check_folder_exists(media.folder_path):
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
        func=_download_trailer,
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


def _batch_download_task(
    media_list: list[MediaRead],
    profile: TrailerProfileRead,
) -> None:
    """Run the async task in a separate event loop."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(batch_download_task(media_list, profile))
    new_loop.close()
    return


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
    media_trailer_list: list[MediaRead] = []
    skipped_titles = {
        "invalid_media_id": [],
        "missing_folder_path": [],
        "trailer_exists": [],
        "media_not_found": [],
    }
    for media_id in media_ids:
        try:
            db_media = media_manager.read(media_id)
        except Exception:
            skipped_titles["invalid_media_id"].append(media_id)
            continue
        check_folder = profile.custom_folder == "{media_folder}"
        if check_folder:
            if db_media.folder_path is None:
                skipped_titles["missing_folder_path"].append(db_media.title)
                continue
            if not FilesHandler.check_folder_exists(db_media.folder_path):
                skipped_titles["missing_folder_path"].append(db_media.title)
                continue
            if db_media.trailer_exists:
                skipped_titles["trailer_exists"].append(db_media.title)
                continue
        if app_settings.wait_for_media:
            if check_folder:
                if not db_media.folder_path:
                    skipped_titles["media_not_found"].append(db_media.title)
                    continue
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
        func=_batch_download_task,
        args=(media_trailer_list, profile),
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=1),
        id="batch_download_trailers",
        name="Batch Download Trailers",
        max_instances=1,
    )
