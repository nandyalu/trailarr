from backend.core.base.database.models.helpers import MediaImage
from backend.core.base.database.models.media import MediaUpdate
from backend.core.download.image import refresh_media_images
from backend.core.radarr.database_manager import MovieDatabaseManager
from backend.core.sonarr.database_manager import SeriesDatabaseManager
from backend.app_logger import logger


async def refresh_images(recent_only: bool = False):
    """Refresh images in the system, and update paths in database as needed.
    This task should be run periodically to ensure that images are up-to-date."""
    logger.info("Refreshing images in the system")
    logger.info("Refreshing movie images")
    await refresh_and_save_media_images(is_movie=True, recent_only=recent_only)
    logger.info("Movie Images refresh complete!")
    logger.info("Refreshing series images")
    await refresh_and_save_media_images(is_movie=False, recent_only=recent_only)
    logger.info("Series Images refresh complete!")


async def refresh_and_save_media_images(is_movie: bool, recent_only: bool = False):
    if is_movie:
        db_manager = MovieDatabaseManager()
    else:
        db_manager = SeriesDatabaseManager()

    if recent_only:
        # Get all media from the database that have been added/updated in the last 24 hours
        db_media_list = db_manager.read_recent()
    else:
        # Get all media from the database
        db_media_list = db_manager.read_all()
    media_image_list: list[MediaImage] = []
    logger.debug(
        f"Refreshing images for {len(db_media_list)} {'movies' if is_movie else 'series'}"
    )
    # Create MediaImage objects for each movie/series
    for db_media in db_media_list:
        poster_image = MediaImage(
            id=db_media.id,
            is_poster=True,
            image_url=db_media.poster_url,
            image_path=db_media.poster_path,
        )
        media_image_list.append(poster_image)
        fanart_image = MediaImage(
            id=db_media.id,
            is_poster=False,
            image_url=db_media.fanart_url,
            image_path=db_media.fanart_path,
        )
        media_image_list.append(fanart_image)
    # Refresh images in the system, and/or get updated paths
    # refresh_media_images modifies the MediaImage objects in place
    await refresh_media_images(is_movie, media_image_list)

    # Update the database with new image paths
    media_update_dict: dict[int, MediaUpdate] = {}
    for media_image in media_image_list:
        if media_image.id in media_update_dict:
            media_update = MediaUpdate()
        else:
            media_update = media_update_dict[media_image.id]
        if media_image.is_poster:
            media_update.poster_path = media_image.image_path
        else:
            media_update.fanart_path = media_image.image_path
        media_update_dict[media_image.id] = media_update
    media_update_tuples = [
        (id, update_obj) for id, update_obj in media_update_dict.items()
    ]
    # Save changes to database
    db_manager.update_bulk(media_update_tuples)
    return
