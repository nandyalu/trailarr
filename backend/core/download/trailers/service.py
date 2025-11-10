import os
from datetime import datetime, timezone

from app_logger import ModuleLogger
import core.base.database.manager.download as download_manager
from core.base.database.models.download import DownloadCreate
from core.download.video_analysis import VideoInfo, get_media_info
from core.files_handler import FilesHandler

logger = ModuleLogger("DownloadService")

DEFAULT_RESOLUTION = 1080
VALID_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]
RESOLUTION_DICT = {
    "SD": 360,
    "FSD": 480,
    "HD": 720,
    "FHD": 1080,
    "QHD": 1440,
    "UHD": 2160,
}


def get_resolution_label(height: int) -> int:
    """Convert resolution dimensions to standard labels (e.g., 1080p, 2160p).
    Gets the closest standard resolution label based on height.
    Args:
        height (int | str): The height dimension or resolution label.
    Returns:
        int: Standard resolution label (e.g., 1080, 2160).
    """
    resolution = DEFAULT_RESOLUTION
    if isinstance(height, int):
        resolution = height

    if isinstance(height, str):
        # Check if value is like HD/UHD etc.
        if height.upper() in RESOLUTION_DICT:
            return RESOLUTION_DICT[height.upper()]
        # Else, Convert to lowercase and remove 'p' from the end if present
        resolution = height.lower()
        resolution = resolution.rstrip("p")
        if not resolution.isdigit():
            return DEFAULT_RESOLUTION
        resolution = int(resolution)

    # If resolution is valid, return it
    if resolution in VALID_RESOLUTIONS:
        return resolution
    # Find the closest resolution. Ex: 1079 -> 1080
    closest_resolution = min(
        VALID_RESOLUTIONS, key=lambda res: abs(res - resolution)
    )
    return closest_resolution


def compute_file_hash(file_path: str) -> str:
    """Compute the hash of a file using FilesHandler.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The computed file hash.
    """
    try:
        return FilesHandler.compute_file_hash(file_path)
    except Exception as e:
        logger.error(f"Error computing file hash for {file_path}: {e}")
        return ""


async def record_new_trailer_download(
    media_id: int,
    profile_id: int,
    file_path: str,
    youtube_video_id: str | None = None,
    media_info: VideoInfo | None = None,
) -> None:
    """
    Records a new trailer download in the database with comprehensive metadata.
    Args:
        media_id (int): The ID of the media.
        profile_id (int): The ID of the TrailerProfile used for download.
        file_path (str): The path to the downloaded file.
        youtube_video_id (str): The YouTube video ID of the trailer.
    """
    logger.debug(f"Recording new trailer download for media {media_id}")
    try:
        # Get media info using ffprobe
        if not media_info:
            media_info = get_media_info(file_path)
        if not media_info:
            logger.error(f"Failed to get media info for {file_path}")
            return

        # Compute File Hash
        file_hash = compute_file_hash(file_path)

        # Extract video stream info
        video_stream = next(
            (s for s in media_info.streams if s.codec_type == "video"), None
        )

        # Extract audio stream info (prefer first audio stream)
        audio_stream = next(
            (s for s in media_info.streams if s.codec_type == "audio"), None
        )

        # Extract subtitle stream info (if any)
        subtitle_stream = next(
            (s for s in media_info.streams if s.codec_type == "subtitle"), None
        )

        # Determine resolution label
        resolution = DEFAULT_RESOLUTION
        if video_stream:
            resolution = get_resolution_label(video_stream.coded_height)

        # Get youtube video id
        yt_id = None
        if media_info.youtube_id and media_info.youtube_id != "unknown0000":
            yt_id = media_info.youtube_id
        elif youtube_video_id:
            yt_id = youtube_video_id
        else:
            yt_id = "unknown0000"

        # Create download record with comprehensive metadata
        download = DownloadCreate(
            path=file_path,
            file_name=os.path.basename(file_path),
            file_hash=file_hash,
            size=media_info.size,
            resolution=resolution,
            file_format=media_info.format_name.split(",")[
                0
            ],  # Get primary format
            video_format=video_stream.codec_name if video_stream else "N/A",
            audio_format=audio_stream.codec_name if audio_stream else "N/A",
            audio_language=(
                audio_stream.language
                if audio_stream and audio_stream.language
                else None
            ),
            subtitle_format=(
                subtitle_stream.codec_name if subtitle_stream else None
            ),
            subtitle_language=(
                subtitle_stream.language
                if subtitle_stream and subtitle_stream.language
                else None
            ),
            duration=media_info.duration_seconds,
            youtube_id=yt_id,
            youtube_channel=media_info.youtube_channel,
            file_exists=True,
            profile_id=profile_id,
            media_id=media_id,
            added_at=media_info.created_at or datetime.now(timezone.utc),
            updated_at=media_info.updated_at or datetime.now(timezone.utc),
        )

        # Save to database using dedicated download manager
        download_manager.create(download)
        logger.debug(
            f"Successfully recorded new trailer download for media {media_id}"
        )

    except Exception as e:
        logger.error(
            f"Failed to record new trailer download for media {media_id}: {e}"
        )
