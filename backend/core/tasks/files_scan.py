import os
import re
import subprocess
from datetime import datetime, timezone

from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.manager.connection import ConnectionDatabaseManager
from core.base.database.models.connection import ArrType
from core.base.database.models.download import Download
from core.download import video_analysis
from core.files_handler import FilesHandler
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager

logger = ModuleLogger("TrailersFilesScan")


def _extract_youtube_id_from_metadata(file_path: str) -> str | None:
    """Extract youtube id from video metadata."""
    try:
        result = subprocess.run(
            [
                "/usr/local/bin/ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format_tags=comment",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            match = re.search(r"(https?://www.youtube.com/watch\?v=)([^&]+)", result.stdout)
            if match:
                return match.group(2)
    except Exception as e:
        logger.error(f"Error extracting youtube id from metadata: {e}")
    return None


async def scan_disk_for_trailers() -> None:
    """Scan the disk for trailers and update the database with the new status."""
    logger.info("Scanning disk for trailers.")
    db_handler = MediaDatabaseManager()
    all_media = db_handler.read_all_with_downloads()

    root_folders: set[str] = set()
    connection_db_handler = ConnectionDatabaseManager()
    all_connections = connection_db_handler.read_all()

    for connection in all_connections:
        if connection.arr_type == ArrType.RADARR:
            arr_manager = RadarrConnectionManager(connection)
        elif connection.arr_type == ArrType.SONARR:
            arr_manager = SonarrConnectionManager(connection)
        else:
            continue
        root_folders.update(await arr_manager.get_rootfolders())

    all_trailer_files: list[str] = []
    for root_folder in root_folders:
        all_trailer_files.extend(
            await FilesHandler.scan_for_trailers(root_folder)
        )

    existing_downloads = [d.path for m in all_media for d in m.downloads]
    new_trailer_files = [
        f for f in all_trailer_files if f not in existing_downloads
    ]

    if not new_trailer_files:
        logger.info("No new trailers found.")
        return

    logger.info(f"Found {len(new_trailer_files)} new trailers.")

    for trailer_file in new_trailer_files:
        media_item = next(
            (
                m
                for m in all_media
                if m.folder_path and trailer_file.startswith(m.folder_path)
            ),
            None,
        )

        if not media_item:
            logger.warning(f"Could not find media for trailer: {trailer_file}")
            continue

        youtube_id = _extract_youtube_id_from_metadata(trailer_file)
        if not youtube_id:
            stat = os.stat(trailer_file)
            if media_item.youtube_trailer_id and media_item.downloaded_at:
                if abs(
                    (
                        media_item.downloaded_at
                        - datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    ).total_seconds()
                ) < 60:
                    youtube_id = media_item.youtube_trailer_id

        if not youtube_id:
            youtube_id = "unknown0000"

        video_info = video_analysis.get_media_info(trailer_file)
        if not video_info:
            logger.error(f"Could not get video info for trailer: {trailer_file}")
            continue

        video_stream = next(
            (s for s in video_info.streams if s.codec_type == "video"), None
        )
        audio_stream = next(
            (s for s in video_info.streams if s.codec_type == "audio"), None
        )
        stat = os.stat(trailer_file)

        download = Download(
            media_id=media_item.id,
            path=trailer_file,
            file_name=os.path.basename(trailer_file),
            size=stat.st_size,
            updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            resolution=f"{video_stream.coded_width}x{video_stream.coded_height}"
            if video_stream
            else "N/A",
            video_format=video_stream.codec_name if video_stream else "N/A",
            audio_format=audio_stream.codec_name if audio_stream else "N/A",
            audio_channels=str(audio_stream.audio_channels) if audio_stream else "N/A",
            file_format=video_info.format_name,
            duration=video_info.duration_seconds,
            subtitles=", ".join(
                s.language
                for s in video_info.streams
                if s.codec_type == "subtitle" and s.language
            ),
            added_at=datetime.now(timezone.utc),
            profile_id=0,  # 0 for unknown
            youtube_id=youtube_id,
            file_exists=True,
        )
        db_handler.create_download(download)
        db_handler.update_trailer_exists(media_item.id, True)
        logger.info(f"Added new download record for {media_item.title}")
