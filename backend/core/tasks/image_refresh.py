from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaImage
from core.base.database.models.media import MediaUpdate
from core.download.image import refresh_media_images
from app_logger import ModuleLogger

logger = ModuleLogger("ImageRefreshTasks")


async def refresh_images(recent_only: bool = False):
    """Refresh images in the system, and update paths in database as \
        needed. This task should be run periodically to ensure that \
        images are up-to-date.
    """
    logger.info("Refreshing images in the system")

    logger.debug("Refreshing movie images")
    await refresh_and_save_media_images(is_movie=True, recent_only=recent_only)
    logger.debug("Movie Images refresh complete!")

    logger.debug("Refreshing series images")
    await refresh_and_save_media_images(
        is_movie=False, recent_only=recent_only
    )
    logger.debug("Series Images refresh complete!")

    logger.info("Image refresh complete!")
    return


async def refresh_and_save_media_images(
    is_movie: bool, recent_only: bool = False
):
    db_manager = MediaDatabaseManager()
    if recent_only:
        # Get all media from the database that have been added/updated \
        # in the last 24 hours
        db_media_list = db_manager.read_recent(movies_only=is_movie)
    else:
        # Get all media from the database
        db_media_list = db_manager.read_all(movies_only=is_movie)
    media_image_list: list[MediaImage] = []
    logger.debug(
        "Refreshing images for"
        f" {len(db_media_list)} {'movies' if is_movie else 'series'}"
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
            media_update = media_update_dict[media_image.id]
        else:
            media_update = MediaUpdate()
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
