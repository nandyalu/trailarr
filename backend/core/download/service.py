import os
from datetime import datetime, timezone

from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.download import DownloadCreate
from core.download.video_analysis import get_media_info

logger = ModuleLogger("DownloadService")


async def record_new_trailer_download(
    media_id: int,
    profile_id: int,
    file_path: str,
    youtube_video_id: str,
) -> None:
    """
    Records a new trailer download in the database.

    Args:
        media_id (int): The ID of the media.
        profile_id (int): The ID of the profile used for the download.
        file_path (str): The path to the downloaded file.
        youtube_video_id (str): The YouTube video ID of the trailer.
    """
    logger.info(f"Recording new trailer download for media {media_id}")
    try:
        # Get file stats
        file_stat = os.stat(file_path)

        # Get media info
        media_info = get_media_info(file_path)
        if not media_info:
            logger.error(f"Failed to get media info for {file_path}")
            return

        # Extract video and audio info
        video_stream = next(
            (s for s in media_info.streams if s.codec_type == "video"), None
        )
        audio_stream = next(
            (s for s in media_info.streams if s.codec_type == "audio"), None
        )
        subtitle_streams = [
            s.language for s in media_info.streams if s.codec_type == "subtitle"
        ]

        # Create download record
        download = DownloadCreate(
            path=file_path,
            file_name=os.path.basename(file_path),
            size=file_stat.st_size,
            updated_at=datetime.fromtimestamp(
                file_stat.st_mtime, tz=timezone.utc
            ),
            resolution=f"{video_stream.coded_width}x{video_stream.coded_height}"
            if video_stream
            else "N/A",
            video_format=video_stream.codec_name if video_stream else "N/A",
            audio_format=audio_stream.codec_name if audio_stream else "N/A",
            audio_channels=str(audio_stream.audio_channels)
            if audio_stream
            else "N/A",
            file_format=media_info.format_name,
            duration=media_info.duration_seconds,
            subtitles=",".join(subtitle_streams) or "unk",
            added_at=datetime.now(timezone.utc),
            profile_id=profile_id,
            media_id=media_id,
            youtube_id=youtube_video_id,
            file_exists=True,
        )

        # Save to database
        db_manager = MediaDatabaseManager()
        db_manager.create_download(download)
        logger.info(f"Successfully recorded new trailer download for media {media_id}")

    except Exception as e:
        logger.error(
            f"Failed to record new trailer download for media {media_id}: {e}"
        )
