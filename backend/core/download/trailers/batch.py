from random import randint
import time
from app_logger import ModuleLogger
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.trailer import download_trailer
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailerDownloadTasks")


def batch_download_task(
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
            download_trailer(media, profile)
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
        _sleep_for = 100 + randint(0, 50)
        logger.debug(
            f"Sleeping for {_sleep_for} seconds before next download..."
        )
        time.sleep(_sleep_for)
    return None
