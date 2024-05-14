import logging
from config.config import config
from core.base.database.models.helpers import MediaTrailer, MediaUpdateDC
from core.download.trailer import download_trailers
from core.radarr.database_manager import MovieDatabaseManager
from core.sonarr.database_manager import SeriesDatabaseManager


def _download_missing_media_trailers(is_movie: bool):
    if not config.monitor_enabled:
        logging.warning("Monitoring is disabled, skipping download trailers")
        return
    if is_movie:
        db_manager = MovieDatabaseManager()
    else:
        db_manager = SeriesDatabaseManager()
    # Get all media from the database
    db_media_list = db_manager.read_all()
    media_trailer_list = []
    logging.debug(
        f"Checking trailers for {len(db_media_list)} {'movies' if is_movie else 'series'}"
    )
    # Create MediaTrailer objects for each movie/series
    for db_media in db_media_list:
        if not db_media.monitor:
            logging.debug(
                f"Skipping {db_media.title} (id:{db_media.id}), monitoring disabled"
            )
            continue
        if db_media.folder_path is None:
            logging.debug(
                f"Skipping {db_media.title} (id:{db_media.id}), folder path not found"
            )
            continue
        if db_media.trailer_exists:
            logging.debug(
                f"Skipping {db_media.title} (id:{db_media.id}), trailer exists"
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

    # Download missing trailers
    downloaded_media = download_trailers(media_trailer_list, is_movie)
    if not downloaded_media:
        logging.info("No trailers downloaded")
        return
    logging.debug("Updating trailer status in database")
    media_update_list = []
    for media in downloaded_media:
        media_update_list.append(
            MediaUpdateDC(
                id=media.id,
                monitor=False,
                trailer_exists=True,
            )
        )
    # Update the trailer statuses in database
    db_manager.update_media_status_bulk(media_update_list)


def download_missing_trailers():
    """Download missing trailers for all movies and series."""
    logging.info("Downloading missing trailers")
    _download_missing_media_trailers(is_movie=True)
    _download_missing_media_trailers(is_movie=False)
    logging.info("Trailers download complete")
    return
