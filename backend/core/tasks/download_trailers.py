from datetime import datetime, timedelta, timezone

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaTrailer, MediaUpdateDC
from core.base.database.models.media import MonitorStatus
from core.download.trailer import download_trailer, download_trailers
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
    skipped_titles = {
        "monitoring_disabled": [],
        "missing_folder_path": [],
        "trailer_exists": [],
        "media_not_found": [],
    }
    for db_media in db_media_list:
        if not db_media.monitor:
            skipped_titles["monitoring_disabled"].append(db_media.title)
            # logger.debug(
            #     f"Skipping {db_media.title} (id:{db_media.id}), monitoring disabled"
            # )
            continue
        if db_media.folder_path is None:
            skipped_titles["missing_folder_path"].append(db_media.title)
            # logger.debug(
            #     f"Skipping {db_media.title} (id:{db_media.id}), folder path not found"
            # )
            continue
        if db_media.trailer_exists:
            skipped_titles["trailer_exists"].append(db_media.title)
            # logger.debug(
            #     f"Skipping {db_media.title} (id:{db_media.id}), trailer exists"
            # )
            continue
        if app_settings.wait_for_media:
            if not FilesHandler.check_media_exists(db_media.folder_path):
                skipped_titles["media_not_found"].append(db_media.title)
                skip_count += 1
                # logger.debug(
                #     f"Skipping {db_media.title} (id:{db_media.id}), media file(s) not found"
                # )
                continue
        # If always search is enabled, set trailer id to None
        if app_settings.trailer_always_search:
            db_media.youtube_trailer_id = None
        media_trailer = MediaTrailer(
            id=db_media.id,
            title=db_media.title,
            is_movie=db_media.is_movie,
            language=db_media.language,
            year=db_media.year,
            folder_path=db_media.folder_path,
            yt_id=db_media.youtube_trailer_id,
        )
        media_trailer_list.append(media_trailer)
    # Log skipped media titles
    if skip_count:
        logger.info(
            f"Skipping trailer download for {skip_count} {media_type}, waiting for media"
        )
    for skip_reason in skipped_titles:
        skip_titles = skipped_titles[skip_reason]
        # if len(skip_titles) > 0:
        #     all_titles = ", ".join(skip_titles)
        # else:
        #     all_titles = "None"
        skip_reason = skip_reason.replace("_", " ")
        logger.debug(f"Skipped {len(skip_titles)} titles - {skip_reason}")
        # logger.debug(f"Skipped {len(skip_titles)} titles - {skip_reason}: {all_titles}")

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
                status=MonitorStatus.DOWNLOADED,
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


def _download_trailer_by_id(mediaT: MediaTrailer):
    db_manager = MediaDatabaseManager()
    db_manager.update_media_status(
        MediaUpdateDC(
            id=mediaT.id,
            monitor=True,
            status=MonitorStatus.DOWNLOADING,
            yt_id=mediaT.yt_id,
        )
    )
    exception_msg = ""
    try:
        trailer_downloaded = download_trailer(mediaT)
        if trailer_downloaded:
            logger.debug("Trailer downloaded! Updating trailer status in database")
            db_manager.update_media_status(
                MediaUpdateDC(
                    id=mediaT.id,
                    monitor=False,
                    status=MonitorStatus.DOWNLOADED,
                    trailer_exists=True,
                    yt_id=mediaT.yt_id,
                    downloaded_at=datetime.now(timezone.utc),
                )
            )
            logger.info(f"Trailer downloaded for {mediaT.title}")
            return
    except Exception as e:
        exception_msg = str(e)
    logger.debug("Trailer download failed! Updating trailer status in database")
    db_manager.update_media_status(
        MediaUpdateDC(
            id=mediaT.id,
            monitor=True,
            status=MonitorStatus.MISSING,
        )
    )
    logger.exception(
        f"Failed to download trailer for {mediaT.title}, Exception: {exception_msg}"
    )
    raise Exception(
        f"Failed to download trailer for {mediaT.title}, Exception: {exception_msg}"
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
    _yt_id = None
    # If always search is enabled, do not use the id from the database
    if not app_settings.trailer_always_search:
        _yt_id = media.youtube_trailer_id
    # If yt_id is provided, always use it
    if yt_id:
        _yt_id = yt_id
    media_trailer = MediaTrailer(
        id=media.id,
        title=media.title,
        is_movie=media.is_movie,
        language=media.language,
        year=media.year,
        folder_path=media.folder_path,
        yt_id=_yt_id,
    )

    # Add Job to scheduler to download trailer
    scheduler.add_job(
        func=_download_trailer_by_id,
        args=(media_trailer,),
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
