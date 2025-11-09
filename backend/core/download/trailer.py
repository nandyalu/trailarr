from datetime import datetime, timezone
import os

from api.v1 import websockets
from app_logger import ModuleLogger
import core.base.database.manager.media as media_manager
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import MediaRead, MonitorStatus
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.video_v2 import download_video
from core.download import trailer_file, trailer_search, video_analysis
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailersDownloader")


def __update_media_status(
    media: MediaRead, type: MonitorStatus, profile: TrailerProfileRead
):
    """Update the media status in the database."""
    if type == MonitorStatus.DOWNLOADING:
        update = MediaUpdateDC(
            id=media.id,
            monitor=True,
            status=MonitorStatus.DOWNLOADING,
        )
        if profile.stop_monitoring:
            # Save the youtube ID for trailers only (stop_monitoring = True)
            update.yt_id = media.youtube_trailer_id
    elif type == MonitorStatus.DOWNLOADED:
        _monitor = True
        if profile.stop_monitoring:
            # Stop monitoring after download if set in profile and save youtube ID
            _monitor = False
        update = MediaUpdateDC(
            id=media.id,
            monitor=_monitor,
            status=MonitorStatus.DOWNLOADED,
            trailer_exists=profile.stop_monitoring,
            downloaded_at=datetime.now(timezone.utc),
        )
        if profile.stop_monitoring:
            # Save the youtube ID for trailers only (stop_monitoring = True)
            update.yt_id = media.youtube_trailer_id
    elif type == MonitorStatus.MISSING:
        update = MediaUpdateDC(
            id=media.id,
            monitor=True,
            status=MonitorStatus.MISSING,
        )
        if media.trailer_exists:
            # If trailer exists but download failed, it should be marked as DOWNLOADED
            update = MediaUpdateDC(
                id=media.id,
                monitor=False,
                status=MonitorStatus.DOWNLOADED,
            )
    else:
        # Handle other statuses if needed
        return None
    media_manager.update_media_status(update)
    return None


def __download_and_verify_trailer(
    media: MediaRead, video_id: str, profile: TrailerProfileRead
) -> str:
    """Download the trailer and verify it."""
    trailer_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(
        f"Downloading trailer for {media.title} [{media.id}] from"
        f" {trailer_url}"
    )
    tmp_dir = "/var/lib/trailarr/tmp"
    if not os.path.exists(tmp_dir):
        tmp_dir = "/app/tmp"
    output_file = f"{tmp_dir}/{media.id}-trailer.{profile.file_format}"
    output_file = download_video(trailer_url, output_file, profile)
    if not trailer_file.verify_download(output_file, media.title, profile):
        raise DownloadFailedError("Trailer verification failed")
    if profile.remove_silence:
        output_file = video_analysis.remove_silence_at_end(output_file)
    return output_file


async def download_trailer(
    media: MediaRead,
    profile: TrailerProfileRead,
    retry_count: int = 2,
    exclude: list[str] | None = None,
) -> bool:
    """Download trailer for a media object with given profile.
    Args:
        media (MediaRead): The media object to download the trailer for.
        profile (TrailerProfileRead): The trailer profile to use.
        retry_count (int, optional): Number of retries if download fails. Defaults to 2.
        exclude (list[str], optional): List of video IDs to exclude from search. Defaults to None.
    Returns:
        bool: True if trailer download was successful, False otherwise.
    Raises:
        DownloadFailedError: If trailer download fails.
    """
    logger.info(f"Downloading trailer for {media.title} [{media.id}]")
    if not exclude:
        exclude = []

    # Exclude the current trailer ID if it exists
    if media.trailer_exists and media.youtube_trailer_id:
        exclude.append(media.youtube_trailer_id)

    # Ignore the current trailer ID if always_search is enabled
    if profile.always_search:
        media.youtube_trailer_id = None

    # Get the video ID, search if needed
    video_id = trailer_search.get_video_id(media, profile, exclude)
    media.youtube_trailer_id = video_id

    if not video_id:
        raise DownloadFailedError(f"No trailer found for {media.title}")

    try:
        __update_media_status(media, MonitorStatus.DOWNLOADING, profile)
        # Download the trailer and verify
        output_file = __download_and_verify_trailer(media, video_id, profile)
        # Move the trailer to the media folder (create subfolder if needed)
        trailer_file.move_trailer_to_folder(output_file, media, profile)
        __update_media_status(media, MonitorStatus.DOWNLOADED, profile)
        msg = (
            f"Trailer downloaded successfully for {media.title} [{media.id}]"
            f" from ({video_id})"
        )
        logger.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return True
    except Exception as e:
        logger.exception(f"Failed to download trailer: {e}")
        __update_media_status(media, MonitorStatus.MISSING, profile)
        if retry_count > 0:
            logger.info(
                f"Retrying download for {media.title}... ({3 - retry_count}/3)"
            )
            media.youtube_trailer_id = None
            if video_id:
                exclude.append(video_id)
            return await download_trailer(
                media, profile, retry_count - 1, exclude
            )
        raise DownloadFailedError(
            f"Failed to download trailer for {media.title}"
        )
