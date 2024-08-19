from datetime import datetime, timedelta, timezone

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaTrailer, MediaUpdateDC
from core.download.trailer import download_trailers
from core.files_handler import FilesHandler
from core.tasks import scheduler

logger = ModuleLogger("TrailerDownloadTasks")


def _download_missing_media_trailers(is_movie: bool):
    if not app_settings.monitor_enabled:
        logger.warning("Monitoring is disabled, skipping download trailers")
        return
    db_manager = MediaDatabaseManager()
    media_type = "movies" if is_movie else "series"
    # Get all media from the database
    db_media_list = db_manager.read_all(movies_only=is_movie)
    media_trailer_list = []
    logger.debug(f"Checking trailers for {len(db_media_list)} monitored {media_type}")
    # Create MediaTrailer objects for each movie/series
    skip_count = 0
    for db_media in db_media_list:
        if not db_media.monitor:
            logger.debug(
                f"Skipping {db_media.title} (id:{db_media.id}), monitoring disabled"
            )
            continue
        if db_media.folder_path is None:
            logger.debug(
                f"Skipping {db_media.title} (id:{db_media.id}), folder path not found"
            )
            continue
        if db_media.trailer_exists:
            logger.debug(
                f"Skipping {db_media.title} (id:{db_media.id}), trailer exists"
            )
            continue
        if app_settings.wait_for_media:
            if not FilesHandler.check_media_exists(db_media.folder_path):
                skip_count += 1
                logger.debug(
                    f"Skipping {db_media.title} (id:{db_media.id}), media file(s) not found"
                )
                continue
        media_trailer = MediaTrailer(
            id=db_media.id,
            title=db_media.title,
            year=db_media.year,
            folder_path=db_media.folder_path,
            yt_id=db_media.youtube_trailer_id,
        )
        media_trailer_list.append(media_trailer)
    if skip_count:
        logger.info(f"Skipping trailer download for {skip_count} {media_type}")

    if not media_trailer_list:
        logger.info(f"No missing {media_type} trailers to download")
        return

    # Download missing trailers
    downloaded_media = download_trailers(media_trailer_list, is_movie)
    if not downloaded_media:
        logger.info(f"No {media_type} trailers downloaded")
        return
    logger.debug("Updating trailer status in database")
    media_update_list = []
    for media in downloaded_media:
        media_update_list.append(
            MediaUpdateDC(
                id=media.id,
                monitor=False,
                trailer_exists=True,
                downloaded_at=media.downloaded_at,
                yt_id=media.yt_id,
            )
        )
    # Update the trailer statuses in database
    db_manager.update_media_status_bulk(media_update_list)
    return


def download_missing_trailers():
    """Download missing trailers for all movies and series."""
    logger.info("Downloading missing trailers")
    _download_missing_media_trailers(is_movie=True)
    _download_missing_media_trailers(is_movie=False)
    # logger.info("Trailers download complete")
    return


def _download_trailer_by_id(mediaT: MediaTrailer, is_movie: bool):
    download_media = download_trailers([mediaT], is_movie)
    if not download_media:
        logger.info("No trailers downloaded")
        return
    logger.debug("Updating trailer status in database")
    media_update_list = []
    for media in download_media:
        if media.downloaded_at is None:
            media.downloaded_at = datetime.now(timezone.utc)
        media_update_list.append(
            MediaUpdateDC(
                id=media.id,
                monitor=False,
                trailer_exists=True,
                yt_id=media.yt_id,
                downloaded_at=media.downloaded_at,
            )
        )

    db_manager = MediaDatabaseManager()
    # Update the trailer statuses in database
    db_manager.update_media_status_bulk(media_update_list)


def download_trailer_by_id(media_id: int, is_movie: bool, yt_id: str = "") -> str:
    """Download trailer for a movie or series by ID."""
    logger.info(
        f"Downloading trailer for {'movie' if is_movie else 'series'} ID: {media_id}"
    )
    db_manager = MediaDatabaseManager()
    try:
        media = db_manager.read(media_id)
    except Exception as e:
        msg = f"Failed to get {'movie' if is_movie else 'series'} with ID: {media_id}"
        logger.error(msg)
        logger.exception(e)
        return msg
    if not media.folder_path:
        msg = f"{'Movie' if is_movie else 'Series'} '{media.title}' has no folder path"
        logger.error(msg)
        return msg
    if yt_id:
        media.youtube_trailer_id = yt_id
    media_trailer = MediaTrailer(
        id=media.id,
        title=media.title,
        year=media.year,
        folder_path=media.folder_path,
        yt_id=media.youtube_trailer_id,
    )

    # Add Job to scheduler to download trailer
    scheduler.add_job(
        func=_download_trailer_by_id,
        args=(media_trailer, is_movie),
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
