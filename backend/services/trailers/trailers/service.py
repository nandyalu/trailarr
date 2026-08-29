"""Record what happened to a trailer file in the downloads table.

A download row is the record that a trailer exists: its path, its size, its
resolution and its hash. The scan and the download flow both write here.
"""

import os
from datetime import datetime, timezone

from app_logger import ModuleLogger
import database.manager.download as download_manager
from database.models.download import DownloadCreate, DownloadRead
from database.models.media import MediaRead
from services.trailers.video_analysis import VideoInfo, get_media_info
from services.files.files_handler import FilesHandler

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
        logger.error(
            f"Trailarr could not compute the hash of '{file_path}': {e}"
        )
        return ""


def find_youtube_id(media_info: VideoInfo, media: MediaRead) -> str:
    """Find the YouTube ID for a trailer based on its path.
    Args:
        media_info (VideoInfo): The video info object.
        media (MediaRead): The media object.
    Returns:
        str: The YouTube ID if found, else `unknown0000`.
    """
    youtube_id = media_info.youtube_id or "unknown0000"
    if youtube_id == "unknown0000" and media.youtube_trailer_id:
        # Check if file was recently created (within 1 hour of download)
        if media.downloaded_at:
            # media.downloaded_at is UTC but timezone-naive from database
            # media_info.created_at is timezone-aware UTC
            downloaded_at = media.downloaded_at.replace(tzinfo=timezone.utc)
            time_diff = media_info.created_at - downloaded_at
            time_diff = abs(time_diff.total_seconds())
            if time_diff < 3600:  # Within 1 hour
                youtube_id = media.youtube_trailer_id
    return youtube_id


def _extract_metadata_fields(media_info: VideoInfo, file_path: str) -> dict:
    """Extract the physical-file-derived metadata fields shared by new-download
    recording and re-analysis after an in-place content change.
    Args:
        media_info (VideoInfo): The ffprobe-derived video info for the file.
        file_path (str): Path to the file (used to compute the content hash).
    Returns:
        dict: Fields suitable for merging into a DownloadCreate payload —
            file_hash, size, resolution, file_format, video_format,
            audio_format, audio_language, subtitle_format, subtitle_language,
            duration.
    """
    video_stream = next(
        (s for s in media_info.streams if s.codec_type == "video"), None
    )
    audio_stream = next(
        (s for s in media_info.streams if s.codec_type == "audio"), None
    )
    subtitle_stream = next(
        (s for s in media_info.streams if s.codec_type == "subtitle"), None
    )

    resolution = DEFAULT_RESOLUTION
    if video_stream:
        resolution = get_resolution_label(video_stream.coded_height)

    return {
        "file_hash": compute_file_hash(file_path),
        "size": media_info.size,
        "resolution": resolution,
        "file_format": media_info.format_name,
        "video_format": video_stream.codec_name if video_stream else "N/A",
        "audio_format": audio_stream.codec_name if audio_stream else "N/A",
        "audio_language": (
            audio_stream.language
            if audio_stream and audio_stream.language
            else None
        ),
        "subtitle_format": (
            subtitle_stream.codec_name if subtitle_stream else None
        ),
        "subtitle_language": (
            subtitle_stream.language
            if subtitle_stream and subtitle_stream.language
            else None
        ),
        "duration": media_info.duration_seconds,
    }


async def record_new_trailer_download(
    media: MediaRead,
    profile_id: int,
    file_path: str,
    youtube_video_id: str | None = None,
    video_info: VideoInfo | None = None,
) -> None:
    """
    Records a new trailer download in the database with comprehensive metadata.
    Args:
        media (MediaRead): The media object.
        profile_id (int): The ID of the TrailerProfile used for download.
        file_path (str): The path to the downloaded file.
        youtube_video_id (str | None): The YouTube video ID of the trailer.
        video_info (VideoInfo | None): Pre-analyzed video info to avoid
            redundant ffprobe calls. If None, will analyze the file.
    """
    logger.debug(
        f"Trailarr records a new trailer download for '{media.title}'.",
        **logger.media(media.id),
    )
    try:
        # Use provided video info or analyze the file
        media_info = video_info
        if not media_info:
            media_info = get_media_info(file_path)
        if not media_info:
            logger.error(
                f"Trailarr could not read the video information of"
                f" '{file_path}'."
            )
            return

        # Get file timestamps from the actual final path (may differ from original)
        file_stat = os.stat(file_path)
        file_created_at = datetime.fromtimestamp(
            file_stat.st_mtime, tz=timezone.utc
        )
        file_updated_at = datetime.fromtimestamp(
            file_stat.st_ctime, tz=timezone.utc
        )

        metadata = _extract_metadata_fields(media_info, file_path)

        # Get youtube video id
        yt_id = find_youtube_id(media_info, media)
        if yt_id == "unknown0000" and youtube_video_id:
            yt_id = youtube_video_id

        # Create download record with comprehensive metadata
        download = DownloadCreate(
            path=file_path,
            file_name=os.path.basename(file_path),
            **metadata,
            youtube_id=yt_id,
            youtube_channel=media_info.youtube_channel,
            file_exists=True,
            profile_id=profile_id,
            media_id=media.id,
            added_at=file_created_at,
            updated_at=file_updated_at,
        )

        # Save to database using dedicated download manager
        download_manager.create(download)
        logger.debug(
            "Successfully recorded new trailer download for media"
            f" {media.title} [{media.id}]"
        )

    except Exception as e:
        logger.error(
            f"Trailarr could not record the new trailer download for"
            f" '{media.title}': {e}",
            **logger.media(media.id),
        )


async def rename_trailer_download(download: DownloadRead, new_path: str) -> bool:
    """Update path/file_name for a download whose file was renamed or moved on
    disk. Used when a disk file is matched to an existing download by content
    hash at a different path — keeps history/metadata on the same row instead
    of deleting the old record and creating a new one.
    Args:
        download (DownloadRead): The existing download record.
        new_path (str): The file's new path on disk.
    Returns:
        bool: True if the update succeeded, False otherwise.
    """
    try:
        updated = download.model_dump()
        updated["path"] = new_path
        updated["file_name"] = os.path.basename(new_path)
        download_manager.update(download.id, DownloadCreate(**updated))
        return True
    except Exception as e:
        logger.error(
            f"Trailarr could not move the download {download.id} to"
            f" '{new_path}': {e}"
        )
        return False


async def reanalyze_trailer_download(
    download: DownloadRead, file_path: str
) -> bool:
    """Recompute physical-file metadata for a download whose file content
    changed in place on disk (same path, different hash — e.g. the user
    re-encoded or trimmed it outside the app). Refreshes hash, size, codecs,
    and duration, while deliberately preserving provenance fields
    (youtube_id, youtube_channel, profile_id, added_at, path, media_id) since
    an external edit doesn't change how/when we originally got this trailer.
    Args:
        download (DownloadRead): The existing download record.
        file_path (str): The file's (unchanged) path on disk.
    Returns:
        bool: True if the re-analysis succeeded, False otherwise.
    """
    try:
        media_info = get_media_info(file_path)
        if not media_info:
            logger.error(f"Failed to get media info for {file_path}")
            return False

        file_stat = os.stat(file_path)
        metadata = _extract_metadata_fields(media_info, file_path)

        updated = download.model_dump()
        updated.update(metadata)
        updated["updated_at"] = datetime.fromtimestamp(
            file_stat.st_ctime, tz=timezone.utc
        )
        download_manager.update(download.id, DownloadCreate(**updated))
        return True
    except Exception as e:
        logger.error(
            f"Trailarr could not examine the download {download.id} at"
            f" '{file_path}': {e}"
        )
        return False
