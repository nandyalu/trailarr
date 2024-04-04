import asyncio
from functools import cache
import hashlib
from io import BytesIO
import aiohttp
import aiofiles.os
from PIL import Image

from backend.core.base.database.models.helpers import MediaImage


POSTER = (300, 450)
FANART = (1280, 720)
STATIC_PATH_MOVIES = "/static/images/movies/"
STATIC_PATH_SHOWS = "/static/images/shows/"


@cache
async def get_base_path(is_movie: bool, is_poster: bool) -> str:
    """Get the base path for saving images. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        is_poster (bool): Whether the image is a poster or fanart."""
    base_path = STATIC_PATH_MOVIES if is_movie else STATIC_PATH_SHOWS
    base_path += "posters/" if is_poster else "fanart/"
    # Create directories if they don't exist
    try:
        await aiofiles.os.makedirs(base_path, exist_ok=True)
    except Exception:
        pass
    return base_path


def get_md5_filename(url: str) -> str:
    """Get the MD5 hash of the image URL. \n
    Args:
        url (str): URL of the image."""
    # Return the MD5 hash of the URL as the filename (str)
    return hashlib.md5(url.encode()).hexdigest()


async def delete_image(image_path: str):
    """Delete an image from disk. \n
    Args:
        image_path (str): Path to the image."""
    try:
        await aiofiles.os.remove(image_path)
    except Exception:
        pass


async def download_needed(is_movie: bool, media: MediaImage) -> bool:
    """Check if a poster or fanart needs to be downloaded. \n
    If image URL updated, deletes old image and sets new path. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        media (MediaImage): Media image object."""
    if not media.image_url:
        return False
    base_path = await get_base_path(is_movie, media.is_poster)
    filename = get_md5_filename(media.image_url)
    file_path = base_path + f"{filename}.jpg"
    # Check if a poster/artwork already exists
    if media.image_path:
        # Check if the existing path matches with new path
        if media.image_path != file_path:
            await delete_image(media.image_path)
    # Update the image path
    media.image_path = file_path
    # Check if the file exists
    if await aiofiles.os.path.exists(media.image_path):
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
            return image


# ? Is the return value needed here?
async def process_image(is_movie: bool, media: MediaImage, retries: int = 3) -> bool:
    """Process a media image, download it if updated/doesn't exist, and save it to disk. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        media (MediaImage): Media image object.
        retries (int) [Optional]: Number of retries in case of failure. Default is 3."""
    if not await download_needed(is_movie, media):
        return False
    if media.image_url is None or media.image_path is None:
        return False

    # Set the image type
    image_dimensions = POSTER if media.is_poster else FANART
    # Download image from URL and save it to disk
    try:
        image = await download_image(media.image_url)
        image.thumbnail(image_dimensions)
        image.save(media.image_path, format="JPEG", optimize=True)
    except Exception:
        if retries > 0:
            return await process_image(is_movie, media, retries - 1)
        else:
            return False
    return True


async def download_images(
    is_movie: bool, media_list: list[MediaImage]
) -> list[MediaImage]:
    """Download images from URLs and save them to disk. \n
    Args:
        is_movie (bool): Whether the media type is movie or show.
        media_list (list[MediaImage]): List of media image objects. \n
    Returns:
        list[MediaImage]: List of media image objects with updated image paths.
    """

    sem = asyncio.Semaphore(5)  # Limit to 5 concurrent downloads

    async def download(item):
        async with sem:  # Wait for a free slot in the semaphore
            return await process_image(is_movie, item)

    # Start all downloads and wait for them to complete
    await asyncio.gather(*(download(media) for media in media_list))
    return media_list
