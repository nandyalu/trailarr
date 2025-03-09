from datetime import datetime, timedelta
import os

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import MediaRead, MonitorStatus
from core.download.trailer import download_trailer, download_trailers
from core.files_handler import FilesHandler
from core.tasks import scheduler

logger = ModuleLogger("TrailerDownloadTasks")


def _download_missing_media_trailers(is_movie: bool) -> None:
    if not app_settings.monitor_enabled:
        logger.warning("Monitoring is disabled, skipping download trailers")
        return None
    db_manager = MediaDatabaseManager()
    media_type = "movies" if is_movie else "series"
    # Get all media from the database
    db_media_list = db_manager.read_all(movies_only=is_movie)
    media_trailer_list: list[MediaRead] = []
    logger.debug(f"Checking trailers for {len(db_media_list)} monitored {media_type}")
    # Create MediaTrailer objects for each movie/series
    skip_count = 0
    skipped_titles = {
        "monitoring_disabled": [],
        "missing_folder_path": [],
        "trailer_exists": [],
        "media_not_found": [],
    }
    for db_media in db_media_list:
        if not db_media.monitor:
            skipped_titles["monitoring_disabled"].append(db_media.title)
            continue
        if db_media.folder_path is None:
            skipped_titles["missing_folder_path"].append(db_media.title)
            continue
        if db_media.trailer_exists:
            skipped_titles["trailer_exists"].append(db_media.title)
            continue
        if app_settings.wait_for_media:
            if not FilesHandler.check_media_exists(db_media.folder_path):
                skipped_titles["media_not_found"].append(db_media.title)
                skip_count += 1
                continue
        # If always search is enabled, set trailer id to None
        if app_settings.trailer_always_search:
            db_media.youtube_trailer_id = None
        media_trailer_list.append(db_media)
    # Log skipped media titles
    if skip_count:
        logger.info(
            f"Skipping trailer download for {skip_count} {media_type}, waiting for media"
        )
    for skip_reason in skipped_titles:
        skip_titles = skipped_titles[skip_reason]
        skip_reason = skip_reason.replace("_", " ")
        logger.debug(f"Skipped {len(skip_titles)} titles - {skip_reason}")
    # Return if no media to download
    if not media_trailer_list:
        logger.info(f"No missing {media_type} trailers to download")
        return None

    # Download missing trailers
    download_trailers(media_trailer_list, is_movie)
    return None


def download_missing_trailers():
    """Download missing trailers for all movies and series."""
    logger.info("Downloading missing trailers")
    _download_missing_media_trailers(is_movie=True)
    _download_missing_media_trailers(is_movie=False)
    # logger.info("Trailers download complete")
    return


def _download_trailer_by_id(media: MediaRead):
    exception_msg = ""
    try:
        trailer_downloaded = download_trailer(media)
        if trailer_downloaded:
            logger.info(f"Trailer downloaded for {media.title}")
            return
    except Exception as e:
        exception_msg = str(e)
        db_manager = MediaDatabaseManager()
        db_manager.update_media_status(
            MediaUpdateDC(
                id=media.id,
                monitor=True,
                status=MonitorStatus.MISSING,
            )
        )
    logger.exception(
        f"Failed to download trailer for {media.title}, Exception: {exception_msg}"
    )
    raise Exception(
        f"Failed to download trailer for {media.title}, Exception: {exception_msg}"
    )


def download_trailer_by_id(media_id: int, yt_id: str = "") -> str:
    """Download trailer for a movie or series by ID."""
    db_manager = MediaDatabaseManager()
    try:
        media = db_manager.read(media_id)
        logger.info(
            f"Downloading trailer for {'movie' if media.is_movie else 'series'} ID: {media_id}"
        )
    except Exception as e:
        msg = f"Failed to get media with ID: {media_id}"
        logger.error(msg)
        logger.exception(e)
        return msg
    is_movie = media.is_movie
    if not media.folder_path:
        msg = f"{'Movie' if is_movie else 'Series'} '{media.title}' has no folder path"
        logger.error(msg)
        return msg
    if not os.path.exists(media.folder_path):
        msg = f"{'Movie' if is_movie else 'Series'} '{media.title}' folder path does not exist"
        logger.error(msg)
        return msg
    _yt_id = None
    # If always search is enabled, do not use the id from the database
    if not app_settings.trailer_always_search:
        _yt_id = media.youtube_trailer_id
    # If yt_id is provided, always use it
    if yt_id:
        _yt_id = yt_id
    media.youtube_trailer_id = _yt_id

    # Add Job to scheduler to download trailer
    scheduler.add_job(
        func=_download_trailer_by_id,
        args=(media,),
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=1),
        id=f"download_trailer_by_id_{media_id}_{is_movie}",
        name=f"Download Trailer for {media.title}",
        max_instances=1,
    )
    msg = "Trailer download started in background for "
    msg += f"{'movie' if is_movie else 'series'}: '{media.title}' (ID: {media_id})"
    if yt_id:
        msg += f" from [{yt_id}]"

    logger.info(msg)
    return msg


def batch_download_trailers(media_ids: list[int]) -> None:
    """Download trailers for a list of media IDs. \n
    Schedules a background job to download them. \n
    Args:
        media_ids (list[int]): List of media IDs to download trailers for.
    Returns:
        None
    """
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
        if db_media.trailer_exists:
            skipped_titles["trailer_exists"].append(db_media.title)
            continue
        if app_settings.wait_for_media:
            if not FilesHandler.check_media_exists(db_media.folder_path):
                skipped_titles["media_not_found"].append(db_media.title)
                continue
        # If always search is enabled, set trailer id to None
        if app_settings.trailer_always_search:
            db_media.youtube_trailer_id = None
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
        logger.debug(f"Skipped {len(skip_titles)} titles - {skip_reason}: {all_titles}")

    # Return if no media to download
    if not media_trailer_list:
        logger.info("No missing trailers to download")
        return
    # Add Job to scheduler to download trailers
    scheduler.add_job(
        func=download_trailers,
        args=(media_trailer_list, None),
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=1),
        id="batch_download_trailers",
        name="Batch Download Trailers",
        max_instances=1,
    )
