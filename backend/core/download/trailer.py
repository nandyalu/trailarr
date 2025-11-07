from datetime import datetime, timezone

from api.v1 import websockets
from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import MediaRead, MonitorStatus
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.service import record_new_trailer_download
from core.download.video_v2 import download_video
from core.download import trailer_file, trailer_search, video_analysis
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailersDownloader")


def __update_media_status(media: MediaRead, type: MonitorStatus):
    """Update the media status in the database."""
    db_manager = MediaDatabaseManager()
    if type == MonitorStatus.DOWNLOADING:
        update = MediaUpdateDC(
            id=media.id,
            monitor=True,
            status=MonitorStatus.DOWNLOADING,
            yt_id=media.youtube_trailer_id,
        )
    elif type == MonitorStatus.DOWNLOADED:
        update = MediaUpdateDC(
            id=media.id,
            monitor=False,
            status=MonitorStatus.DOWNLOADED,
            trailer_exists=True,
            downloaded_at=datetime.now(timezone.utc),
            yt_id=media.youtube_trailer_id,
        )
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
    db_manager.update_media_status(update)
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
    tmp_output_file = f"/app/tmp/{media.id}-trailer.%(ext)s"
    output_file = download_video(trailer_url, tmp_output_file, profile)
    tmp_output_file = tmp_output_file.replace("%(ext)s", profile.file_format)
    if not trailer_file.verify_download(
        tmp_output_file, output_file, media.title
    ):
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
        __update_media_status(media, MonitorStatus.DOWNLOADING)
        # Download the trailer and verify
        output_file = __download_and_verify_trailer(media, video_id, profile)
        # Move the trailer to the media folder (create subfolder if needed)
        final_file_path = trailer_file.move_trailer_to_folder(output_file, media, profile)
        __update_media_status(media, MonitorStatus.DOWNLOADED)
        await record_new_trailer_download(
            media_id=media.id,
            profile_id=profile.id,
            file_path=final_file_path,
            youtube_video_id=video_id,
        )
        msg = (
            f"Trailer downloaded successfully for {media.title} [{media.id}]"
            f" from ({video_id})"
        )
        logger.info(msg)
        await websockets.ws_manager.broadcast(msg, "Success")
        return True
    except Exception as e:
        logger.exception(f"Failed to download trailer: {e}")
        __update_media_status(media, MonitorStatus.MISSING)
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
