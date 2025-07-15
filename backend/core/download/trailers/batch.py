import asyncio
from random import randint
from app_logger import ModuleLogger
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.trailer import download_trailer
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailerDownloadTasks")


async def batch_download_task(
    media_list: list[MediaRead],
    profile: TrailerProfileRead,
    downloading_count: int | None = None,
    download_count: int | None = None,
) -> None:
    """Download trailers for a list of media IDs with given profile. \n
    🚨 This function needs to be called from a background task. 🚨
    Args:
        media_list (list[MediaRead]): List of media objects to download trailers for.
        profile (TrailerProfileRead): The trailer profile to use for download.
        downloading_count (int, optional=None): The current downloading count.
        download_count (int, optional=None): The total download count.
    Returns:
        None
    """
    if downloading_count is None:
        downloading_count = 1
    if download_count is None:
        download_count = len(media_list)
    for media in media_list:
        logger.info(
            f"Downloading trailer {downloading_count}/{download_count}"
        )
        try:
            await download_trailer(media, profile)
        except DownloadFailedError as e:
            logger.error(e)
        except Exception as e:
            logger.error(
                "Unexpected error downloading trailer for media"
                f" '{media.title}' [{media.id}]: {e}"
            )
        finally:
            downloading_count += 1
        # Sleep for a random time if more downloads are pending
        if downloading_count >= download_count:
            return
        _sleep_for = randint(0, 60)  # Random sleep between 0 and 60 seconds
        # Increase the sleep time as more trailers are being downloaded
        if downloading_count < 10:
            _sleep_for += 120
        elif downloading_count < 50:
            _sleep_for += 240
        elif downloading_count < 100:
            _sleep_for += 360
        elif downloading_count < 200:
            _sleep_for += 420
        elif downloading_count < 500:
            _sleep_for += 540
        elif downloading_count < 1000:
            _sleep_for += 600
        logger.info(
            f"Sleeping for {_sleep_for} seconds before next download..."
        )
        await asyncio.sleep(_sleep_for)
    return None
