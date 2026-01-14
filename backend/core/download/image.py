import asyncio
import hashlib
from io import BytesIO
from pathlib import Path
import aiohttp
import aiofiles.os
from PIL import Image
from async_lru import alru_cache

from app_logger import logger
from config.settings import app_settings
from core.base.database.models.helpers import MediaImage
from core.base.database.manager import media as media_manager

POSTER = (300, 450)
FANART = (1280, 720)
IMAGES_PATH = Path(app_settings.app_data_dir, "web", "images")
STATIC_PATH_MOVIES = IMAGES_PATH / "movies"
STATIC_PATH_SHOWS = IMAGES_PATH / "shows"


# TODO: For v1.0.0 release - Change the paths saved in DB to paths \
# relative to `images` folder and serve them statically from there.


@alru_cache
async def get_base_path(is_movie: bool, is_poster: bool) -> Path:
    """Get the base path for saving images. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        is_poster (bool): Whether the image is a poster or fanart."""
    base_path = STATIC_PATH_MOVIES if is_movie else STATIC_PATH_SHOWS
    base_path = base_path / "posters" if is_poster else base_path / "fanart"
    # Create directories if they don't exist
    try:
        await aiofiles.os.makedirs(base_path, exist_ok=True)
    except Exception:
        logger.error(f"Unable to create images folder: '{base_path}'")
    return base_path


def get_md5_filename(url: str) -> str:
    """Get the MD5 hash of the image URL. \n
    Args:
        url (str): URL of the image."""
    # Return the MD5 hash of the URL as the filename (str)
    return hashlib.md5(url.encode(), usedforsecurity=False).hexdigest()


async def delete_image(image_path: str):
    """Delete an image from disk. \n
    Args:
        image_path (str): Path to the image."""
    try:
        if await aiofiles.os.path.exists(image_path):
            await aiofiles.os.remove(image_path)
        else:
            logger.debug(f"Image not found: '{image_path}'")
    except Exception:
        logger.error(f"Unable to delete image: '{image_path}'")
    return


async def download_needed(is_movie: bool, media: MediaImage) -> bool:
    """Check if a poster or fanart needs to be downloaded. \n
    If image URL updated, deletes old image and sets new path. \n
    This modifies the `media` object's `image_path` if needed. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        media (MediaImage): Media image object."""
    if not media.image_url:
        return False
    base_path = await get_base_path(is_movie, media.is_poster)
    filename = get_md5_filename(media.image_url)
    file_path = base_path / f"{filename}.jpg"
    # Check if a poster/artwork already exists
    if media.image_path:
        # Check if the existing path matches with new path
        if media.image_path != file_path.as_posix():
            logger.debug(
                f"Image updated for media id: [{media.id}], deleting old"
                f" image! Path: '{media.image_path}'"
            )
            await delete_image(media.image_path)
    # Update the image path
    media.image_path = file_path.as_posix()
    # Check if the file exists
    if await aiofiles.os.path.exists(file_path):
        return False  # Poster/Artwork already exist
    return True


async def download_image(url: str) -> Image.Image:
    """Download an image from a URL. \n
    Args:
        url (str): URL of the image."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            image_data = await response.read()
            image_file = BytesIO(image_data)
            image = Image.open(image_file)
            return image.convert("RGB")  # Convert to RGB for consistency


# ? Is the return value needed here?
async def process_image(
    is_movie: bool, media: MediaImage, retries: int = 3
) -> bool:
    """Process a media image, download it if updated/doesn't exist, and save it to disk. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        media (MediaImage): Media image object.
        retries (int) [Optional]: Number of retries in case of failure. Default is 3.
    """
    # keep original path for update check
    _image_path = media.image_path
    if not await download_needed(is_movie, media):
        return _image_path != media.image_path
    # download_needed() checks if image_url is None and returns False,
    # and sets image_path if empty/updated.
    # We are checking them here to make sure nothing went wrong, also for type checking.
    if media.image_url is None or media.image_path is None:
        return _image_path != media.image_path
    # Set the image type
    image_dimensions = POSTER if media.is_poster else FANART
    # Download image from URL and save it to disk
    try:
        image = await download_image(media.image_url)
        image.thumbnail(image_dimensions)
        image.save(
            media.image_path, format="JPEG", optimize=True, progressive=True
        )
        logger.debug(
            f"Image downloaded for media id: [{media.id}], "
            f"URL: '{media.image_url}', path: '{media.image_path}'"
        )
    except Exception:
        if retries > 0:
            return await process_image(is_movie, media, retries - 1)
        else:
            logger.debug(
                f"Failed to download image for media id: [{media.id}], "
                f"URL: '{media.image_url}'"
            )
            return False
    return True


async def refresh_media_images(
    is_movie: bool, media_list: list[MediaImage]
) -> None:
    """Refresh images in the disk. \n
    New images will be downloaded if:
    - The image URL is updated.
    - The image doesn't exist in the disk.
    - The existing image path doesn't match with md5 hash of URL. \n
    If an image with the same URL already exists, image path will be set to existing image. \n
    Note: \n
        The `media_list` objects will be modified in place. \n
        Also updates the database with new image paths. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        media_list (list[MediaImage]): List of media image objects. \n
    Returns:
        None
    """

    sem = asyncio.Semaphore(5)  # Limit to 5 concurrent downloads

    async def download(media_image: MediaImage):
        async with sem:  # Wait for a free slot in the semaphore
            updated = await process_image(is_movie, media_image)
            if updated:
                media_manager.update_media_image(media_image)
            return

    # Start all downloads and wait for them to complete
    await asyncio.gather(*(download(media) for media in media_list))
    return
