import core.base.database.manager.media as media_manager
from core.base.database.models.helpers import MediaImage
from core.download.image import refresh_media_images
from app_logger import ModuleLogger

logger = ModuleLogger("ImageRefreshTasks")


async def refresh_images(recent_only: bool = False):
    """Refresh images in the system, and update paths in database as \
        needed. This task should be run periodically to ensure that \
        images are up-to-date.
    """
    logger.info("Refreshing images in the system")

    await refresh_and_save_media_images(is_movie=True, recent_only=recent_only)

    await refresh_and_save_media_images(
        is_movie=False, recent_only=recent_only
    )

    logger.info("Image refresh complete!")
    return


async def refresh_and_save_media_images(
    is_movie: bool, recent_only: bool = False
):
    if recent_only:
        # Get all media from the database that have been added/updated \
        # in the last 24 hours
        db_media_list = media_manager.read_recent(movies_only=is_movie)
    else:
        # Get all media from the database
        db_media_list = media_manager.read_all_generator(movies_only=is_movie)
    media_image_list: list[MediaImage] = []
    logger.debug(f"Refreshing images for {'movies' if is_movie else 'series'}")
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
    logger.debug(
        f"Finished refreshing images for {'movies' if is_movie else 'series'}"
    )
    return
