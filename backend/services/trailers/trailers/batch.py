import threading

from app_logger import ModuleLogger
from database.models.media import MediaRead
from database.models.trailerprofile import TrailerProfileRead
from services.trailers.trailer import download_trailer
from services.trailers.trailers import utils
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailerDownloadTasks")


async def batch_download_task(
    media_list: list[MediaRead],
    profile: TrailerProfileRead,
    downloading_count: int | None = None,
    download_count: int | None = None,
    _stop_event: threading.Event | None = None,
) -> None:
    """Download trailers for a list of media IDs with given profile. \n
    🚨 This function needs to be called from a background task. 🚨
    Args:
        media_list (list[MediaRead]): List of media objects to download trailers for.
        profile (TrailerProfileRead): The trailer profile to use for download.
        downloading_count (int, optional=None): The current downloading count.
        download_count (int, optional=None): The total download count.
        _stop_event (threading.Event, optional=None): Event to signal stopping the download.
    Returns:
        None
    """
    if downloading_count is None:
        downloading_count = 1
    if download_count is None:
        download_count = len(media_list)
    for media in media_list:
        logger.info(
            f"Trailarr downloads trailer {downloading_count} of"
            f" {download_count}."
        )
        try:
            await download_trailer(
                media, profile, profile.retry_count, _stop_event=_stop_event
            )
        except DownloadFailedError as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(
                f"Trailarr could not download the trailer for '{media.title}':"
                f" {e}",
                **logger.media(media.id),
            )
        finally:
            downloading_count += 1
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Trailarr stopped the downloads. A stop was requested."
            )
            return None
        # Sleep for a random time if more downloads are pending
        if downloading_count >= download_count:
            return None
        await utils.sleep_between_downloads(downloading_count, logger)
    return None
