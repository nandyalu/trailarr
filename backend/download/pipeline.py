"""Download pipeline — combines trailer.py, service.py, batch.py, missing.py."""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import threading

from app_logger import ModuleLogger
from config.logging_context import with_logging_context
import db.repos.connection as connection_repo
import db.repos.download as download_repo
import db.repos.issue as issue_repo
import db.repos.media as media_repo
import db.repos.trailer_profile as trailer_profile_repo
import db.repos.trailer_status as trailer_status_repo
import db.repos.video_id as video_id_repo
from db.models.connection import ArrType
from db.models.download import DownloadCreate
from db.models.event import EventSource
from db.models.helpers import MediaUpdateDC
from db.models.issue import EntityType, IssueType
from db.models.media import MediaRead
from db.models.mediatrailerstatus import TrailerStatusEnum
from db.models.trailerprofile import TrailerProfileRead, VideoType
from services.tmdb_service import get_tmdb_youtube_key
from config.settings import app_settings
from utils.filters import matches_filters
from download import analysis as video_analysis
from download import filename as trailer_file
from download import search as trailer_search
from download import utils
from download.analysis import VideoInfo, get_media_info
from download.video import download_video
from exceptions import DownloadFailedError, FolderNotFoundError, FolderPathEmptyError, ItemNotFoundError, StopEventSetError
from services import event_service
from services.files_service import FilesHandler
from ws.manager import broadcast as ws_broadcast, ws_manager

logger = ModuleLogger("TrailersDownloader")

_NOT_AVAILABLE_TTL = timedelta(days=7)


def _should_skip_slot(
    row: "MediaTrailerStatus | None",
    profile: TrailerProfileRead,
    now: datetime,
) -> bool:
    """Return True if a (media, profile, season, sequence) slot should be skipped."""
    if row is None:
        return False
    if row.status in (
        TrailerStatusEnum.DOWNLOADED,
        TrailerStatusEnum.DOWNLOADING,
        TrailerStatusEnum.SKIPPED,
        TrailerStatusEnum.UNMONITORED,
    ):
        return True
    if row.status == TrailerStatusEnum.FAILED and (row.attempt_count or 0) >= profile.retry_count:
        return True
    if row.status == TrailerStatusEnum.NOT_AVAILABLE:
        updated = (
            row.updated_at.replace(tzinfo=timezone.utc)
            if row.updated_at and row.updated_at.tzinfo is None
            else row.updated_at
        )
        if updated and (now - updated) < _NOT_AVAILABLE_TTL:
            return True
    return False


def _get_seasons_for_media(media: MediaRead, profile: TrailerProfileRead) -> list[int]:
    """Return the list of season numbers to attempt for this (media, profile) pair."""
    if profile.for_movies:
        return [0]
    if profile.download_season_videos:
        return list(range(0, (media.season_count or 0) + 1))
    return [0]


# ─── Resolution helpers ────────────────────────────────────────────────────────

DEFAULT_RESOLUTION = 1080
VALID_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]
RESOLUTION_DICT = {"SD": 360, "FSD": 480, "HD": 720, "FHD": 1080, "QHD": 1440, "UHD": 2160}


def get_resolution_label(height: int) -> int:
    resolution = DEFAULT_RESOLUTION
    if isinstance(height, int):
        resolution = height
    if isinstance(height, str):
        if height.upper() in RESOLUTION_DICT:
            return RESOLUTION_DICT[height.upper()]
        resolution = height.lower().rstrip("p")
        if not resolution.isdigit():
            return DEFAULT_RESOLUTION
        resolution = int(resolution)
    if resolution in VALID_RESOLUTIONS:
        return resolution
    return min(VALID_RESOLUTIONS, key=lambda res: abs(res - resolution))


def compute_file_hash(file_path: str) -> str:
    try:
        return FilesHandler.compute_file_hash(file_path)
    except Exception as e:
        logger.error(f"Error computing file hash for {file_path}: {e}")
        return ""


def find_youtube_id(media_info: VideoInfo, media: MediaRead) -> str:
    youtube_id = media_info.youtube_id or "unknown0000"
    if youtube_id == "unknown0000" and media.youtube_trailer_id:
        if media.downloaded_at:
            downloaded_at = media.downloaded_at.replace(tzinfo=timezone.utc)
            time_diff = abs((media_info.created_at - downloaded_at).total_seconds())
            if time_diff < 3600:
                youtube_id = media.youtube_trailer_id
    return youtube_id


# ─── Record new trailer download ───────────────────────────────────────────────

async def record_new_trailer_download(
    media: MediaRead,
    profile_id: int,
    file_path: str,
    youtube_video_id: str | None = None,
    video_info: VideoInfo | None = None,
    season: int = 0,
    sequence: int = 1,
    video_type: str = "trailer",
) -> int | None:
    logger.debug(f"Recording new trailer download for media {media.title} [{media.id}]")
    try:
        media_info = video_info
        if not media_info:
            media_info = get_media_info(file_path)
        if not media_info:
            logger.error(f"Failed to get media info for {file_path}")
            return

        file_stat = os.stat(file_path)
        file_created_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
        file_updated_at = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
        file_hash = compute_file_hash(file_path)

        video_stream = next((s for s in media_info.streams if s.codec_type == "video"), None)
        audio_stream = next((s for s in media_info.streams if s.codec_type == "audio"), None)
        subtitle_stream = next((s for s in media_info.streams if s.codec_type == "subtitle"), None)

        resolution = DEFAULT_RESOLUTION
        if video_stream:
            resolution = get_resolution_label(video_stream.coded_height)

        yt_id = find_youtube_id(media_info, media)
        if yt_id == "unknown0000" and youtube_video_id:
            yt_id = youtube_video_id

        download = DownloadCreate(
            path=file_path,
            file_name=os.path.basename(file_path),
            file_hash=file_hash,
            size=media_info.size,
            resolution=resolution,
            file_format=media_info.format_name,
            video_format=video_stream.codec_name if video_stream else "N/A",
            audio_format=audio_stream.codec_name if audio_stream else "N/A",
            audio_language=(audio_stream.language if audio_stream and audio_stream.language else None),
            subtitle_format=(subtitle_stream.codec_name if subtitle_stream else None),
            subtitle_language=(subtitle_stream.language if subtitle_stream and subtitle_stream.language else None),
            duration=media_info.duration_seconds,
            youtube_id=yt_id,
            youtube_channel=media_info.youtube_channel,
            file_exists=True,
            video_type=video_type,
            profile_id=profile_id,
            media_id=media.id,
            added_at=file_created_at,
            updated_at=file_updated_at,
        )
        created = download_repo.create(download)
        status_row = None
        if profile_id:
            status_row = trailer_status_repo.upsert_slot_status(
                media.id, profile_id, season, sequence,
                TrailerStatusEnum.DOWNLOADED, created.id,
            )
        logger.debug(f"Successfully recorded new trailer download for media {media.title} [{media.id}]")
        return status_row.id if status_row else None
    except Exception as e:
        logger.error(f"Failed to record new trailer download for media {media.title} [{media.id}]: {e}")
    return None


# ─── Plex helpers ──────────────────────────────────────────────────────────────

async def _check_plex_trailer(media: MediaRead, profile: TrailerProfileRead) -> bool:
    if not profile.skip_if_plex_trailer:
        return False
    if not (media.plex_connection_id and media.plex_rating_key):
        return False
    if media.plex_trailer is not None:
        return media.plex_trailer
    try:
        conn = connection_repo.read(media.plex_connection_id)
        if conn.arr_type != ArrType.PLEX:
            return False
        from integrations.plex.client import PlexAPI
        api = PlexAPI(
            server_url=conn.url,
            token=conn.api_key,
            identifier=f"trailarr_{conn.id}",
        )
        extras = await api.get_library_item_extras(media.plex_rating_key)
        remote_trailers = [e for e in extras if e.subtype == "trailer" and not e.guid.startswith("file://")]
        resolution_threshold = profile.skip_if_plex_trailer_resolution
        if resolution_threshold > 0:
            has_trailer = any(e.resolution >= resolution_threshold for e in remote_trailers)
        else:
            has_trailer = len(remote_trailers) > 0
        media_repo.update_plex_trailer(media.id, has_trailer)
        return has_trailer
    except Exception as e:
        logger.warning(f"Failed to check Plex trailer for '{media.title}' [{media.id}]: {e}")
        return False


async def _notify_plex(media: MediaRead) -> None:
    if not (media.plex_connection_id and media.plex_section_key and media.folder_path):
        logger.debug(
            f"Skipping Plex scan notify for '{media.title}' [{media.id}]:"
            " missing plex_connection_id, plex_section_key, or folder_path"
        )
        return
    try:
        conn = connection_repo.read(media.plex_connection_id)
        if conn.arr_type != ArrType.PLEX:
            return
        from integrations.plex.sync import PlexConnectionManager
        plex_manager = PlexConnectionManager(conn)
        await plex_manager.trigger_item_scan(
            media_id=media.id,
            section_key=media.plex_section_key,
            folder_path=media.folder_path,
            source=EventSource.SYSTEM,
            source_detail="TrailerDownloaded",
        )
    except Exception as e:
        logger.warning(f"Failed to notify Plex for '{media.title}' [{media.id}]: {e}")


# ─── Media status update ───────────────────────────────────────────────────────

_DOWNLOADING = "downloading"
_DOWNLOADED = "downloaded"
_MISSING = "missing"


def _update_media_status(media: MediaRead, type: str, profile: TrailerProfileRead) -> None:
    if type == _DOWNLOADING:
        update = MediaUpdateDC(id=media.id, monitor=True)
    elif type == _DOWNLOADED:
        update = MediaUpdateDC(
            id=media.id,
            monitor=not profile.stop_monitoring,
            downloaded_at=datetime.now(timezone.utc),
        )
    elif type == _MISSING:
        update = MediaUpdateDC(id=media.id, monitor=True)
    else:
        return

    if update.monitor != media.monitor:
        event_service.track_monitor_changed(
            media_id=media.id,
            old_monitor=media.monitor,
            new_monitor=update.monitor,
            source=EventSource.SYSTEM,
            source_detail="TrailerDownload",
        )
    media_repo.update_media_status(update)


# ─── Core download function ────────────────────────────────────────────────────

def _download_and_verify_trailer(
    media: MediaRead,
    video_id: str,
    profile: TrailerProfileRead,
    _stop_event: threading.Event | None = None,
) -> tuple[str, VideoInfo | None]:
    trailer_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"Downloading trailer for {media.title} [{media.id}] from {trailer_url}")
    tmp_dir = Path(tempfile.gettempdir()) / "trailarr"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    output_file = tmp_dir / f"{media.id}-trailer.{profile.file_format}"
    output_file = download_video(trailer_url, str(output_file), profile, _stop_event=_stop_event)

    is_valid, video_info = trailer_file.verify_download(output_file, media.title, profile)
    if not is_valid:
        raise DownloadFailedError("Trailer verification failed")

    if profile.remove_silence:
        if _stop_event and _stop_event.is_set():
            raise StopEventSetError("Stop event set during silence removal")
        output_file, _trimmed = video_analysis.remove_silence_at_end(output_file)
        if _trimmed:
            video_info = video_analysis.get_media_info(output_file)

    return output_file, video_info


async def download_trailer(
    media: MediaRead,
    profile: TrailerProfileRead,
    retry_count: int = 2,
    exclude: list[str] | None = None,
    _stop_event: threading.Event | None = None,
    season: int = 0,
    sequence: int = 1,
) -> bool:
    """Download a trailer according to the profile's video_type and tmdb_language settings.

    Priority for video ID lookup: user-provided VideoId → arr-provided VideoId → TMDB cache →
    live TMDB → media.youtube_trailer_id → YouTube search.

    User-provided IDs always take precedence, even when always_search=True.
    For TMDB types (teaser/clip/featurette/etc.): VideoId cache → live TMDB → NOT_AVAILABLE.
    For OTHER type: YouTube search only (no TMDB involvement).
    """
    logger.info(f"Downloading trailer for {media.title} [{media.id}]")
    if not exclude:
        exclude = []

    _vtype = profile.video_type.value if hasattr(profile.video_type, "value") else str(profile.video_type)
    _tmdb_lang = profile.tmdb_language or ""

    # Look up best available YouTube ID from the VideoId table.
    best_video_id = video_id_repo.get_best_for_download(
        media_id=media.id,
        video_type=_vtype,
        language=_tmdb_lang,
        season=season,
    )
    has_user_id = best_video_id is not None and video_id_repo.get_for_media(media.id) and any(
        r.source == "user" and r.video_type == _vtype
        for r in video_id_repo.get_for_media(media.id)
    )

    # always_search bypasses cached IDs UNLESS a user-provided ID exists.
    if profile.always_search and not has_user_id:
        media.youtube_trailer_id = None
        best_video_id = None

    if await _check_plex_trailer(media, profile):
        logger.info(
            f"Plex already has a trailer for '{media.title}' [{media.id}],"
            " skipping download (skip_if_plex_trailer=True)"
        )
        return False

    video_id: str | None = None

    if profile.video_type == VideoType.OTHER:
        # Custom YouTube search only — no TMDB involvement for 'other' type.
        video_id = trailer_search.get_video_id(
            media, profile, exclude,
            season=season, sequence=sequence, video_type=_vtype,
        )
        if not video_id:
            raise DownloadFailedError(f"No trailer found for {media.title}")

    elif profile.video_type != VideoType.TRAILER:
        # Named TMDB types (teaser, clip, featurette, etc.): TMDB only, no YouTube fallback.
        if not app_settings.tmdb_api_key:
            logger.warning(
                f"Profile '{profile.customfilter.filter_name}' has video_type={_vtype}"
                " but no TMDB API key is configured — marking row NOT_AVAILABLE."
            )
            trailer_status_repo.upsert_slot_status(
                media.id, profile.id, season, sequence, TrailerStatusEnum.NOT_AVAILABLE
            )
            return False
        # Use cached key if available; otherwise do a live TMDB call.
        if best_video_id:
            video_id = best_video_id
        else:
            _lang = profile.tmdb_language or ""
            video_id = await get_tmdb_youtube_key(media, _vtype, season, language=_lang)
        if not video_id:
            logger.info(
                f"TMDB has no {_vtype} for '{media.title}' [{media.id}]"
                " — marking NOT_AVAILABLE."
            )
            trailer_status_repo.upsert_slot_status(
                media.id, profile.id, season, sequence, TrailerStatusEnum.NOT_AVAILABLE
            )
            return False

    else:
        # TRAILER type: two-path depending on whether tmdb_language is set.
        _tmdb_lang = profile.tmdb_language
        if _tmdb_lang:
            # Language-specific TMDB first, then fall back to Radarr ID, then YouTube search.
            if best_video_id:
                video_id = best_video_id
            else:
                video_id = await get_tmdb_youtube_key(media, "trailer", season, language=_tmdb_lang)
            if not video_id and media.youtube_trailer_id:
                video_id = media.youtube_trailer_id
            if not video_id:
                video_id = trailer_search.get_video_id(
                    media, profile, exclude,
                    season=season, sequence=sequence, video_type=_vtype,
                )
        else:
            # Radarr/user ID first, then TMDB cache, then YouTube search.
            if media.youtube_trailer_id:
                video_id = media.youtube_trailer_id
            elif best_video_id:
                video_id = best_video_id
            else:
                video_id = trailer_search.get_video_id(
                    media, profile, exclude,
                    season=season, sequence=sequence, video_type=_vtype,
                )
        if not video_id:
            raise DownloadFailedError(f"No trailer found for {media.title}")

    if _stop_event and _stop_event.is_set():
        logger.info(f"Download stopped for {media.title} [{media.id}]")
        return False

    try:
        _update_media_status(media, _DOWNLOADING, profile)
        output_file, video_info = _download_and_verify_trailer(media, video_id, profile, _stop_event=_stop_event)
        final_path = trailer_file.move_trailer_to_folder(output_file, media, profile, video_info, season=season, sequence=sequence)
        _update_media_status(media, _DOWNLOADED, profile)
        new_row_id = await record_new_trailer_download(
            media, profile.id, final_path, video_id, video_info,
            season=season, sequence=sequence, video_type=_vtype,
        )

        # Push status row update so the UI reflects the new DOWNLOADED state immediately.
        if new_row_id is not None:
            try:
                status_read = trailer_status_repo.read(new_row_id)
                if status_read:
                    await ws_manager.push("trailer_status:updated", status_read)
            except Exception as e:
                logger.debug(f"Failed to push trailer_status:updated for row {new_row_id}: {e}")

        event_service.track_trailer_downloaded(
            media_id=media.id,
            yt_id=video_id,
            source=EventSource.SYSTEM,
            source_detail="TrailerDownload",
        )
        if profile.notify_plex:
            await _notify_plex(media)

        msg = f"Trailer downloaded successfully for {media.title} [{media.id}] from ({video_id})"
        logger.info(msg)
        await ws_manager.broadcast(msg, "Success", reload="media,trailer_statuses")
        return True
    except Exception as e:
        logger.exception(f"Failed to download trailer: {e}")
        _update_media_status(media, _MISSING, profile)
        if _stop_event and _stop_event.is_set():
            logger.info(f"Download stopped for {media.title} [{media.id}] due to stop event.")
            return False
        if retry_count > 0:
            logger.info(f"Retrying download for {media.title}... ({3 - retry_count}/3)")
            # Clear cached ID so retry sources a fresh result; add failed ID to exclude
            # so YouTube search won't suggest it again.
            media.youtube_trailer_id = None
            if video_id:
                exclude.append(video_id)
            return await download_trailer(
                media, profile, retry_count - 1, exclude,
                _stop_event=_stop_event,
                season=season, sequence=sequence,
            )
        raise DownloadFailedError(f"Failed to download trailer for {media.title}")


# ─── Batch download ────────────────────────────────────────────────────────────

async def batch_download_task(
    media_list: list[MediaRead],
    profile: TrailerProfileRead,
    downloading_count: int | None = None,
    download_count: int | None = None,
    _stop_event: threading.Event | None = None,
) -> None:
    if downloading_count is None:
        downloading_count = 1
    if download_count is None:
        download_count = len(media_list)
    for media in media_list:
        logger.info(f"Downloading trailer {downloading_count}/{download_count}")
        try:
            await download_trailer(media, profile, profile.retry_count, _stop_event=_stop_event)
        except DownloadFailedError as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(
                f"Unexpected error downloading trailer for media '{media.title}' [{media.id}]: {e}"
            )
        finally:
            downloading_count += 1
        if _stop_event and _stop_event.is_set():
            logger.info("Batch downloads stopped due to stop event.")
            return
        if downloading_count >= download_count:
            return
        await utils.sleep_between_downloads(downloading_count, logger)


# ─── Missing trailers task ─────────────────────────────────────────────────────

def _is_valid_media(db_media: MediaRead, check_folder: bool = True, row_id: int | None = None) -> bool:
    if check_folder:
        if db_media.folder_path is None:
            logger.info(f"Media '{db_media.title}' [{db_media.id}] skipped: missing folder path.")
            event_service.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Missing folder path",
                source_detail="DownloadMissingTrailers",
            )
            return False
        if not FilesHandler.check_folder_exists(db_media.folder_path):
            logger.info(f"Media '{db_media.title}' [{db_media.id}] skipped: folder does not exist.")
            event_service.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Folder does not exist",
                source_detail="DownloadMissingTrailers",
            )
            if row_id is not None:
                issue_repo.upsert(
                    issue_type=IssueType.FOLDER_MISSING,
                    entity_type=EntityType.MEDIA_TRAILER_STATUS,
                    entity_id=row_id,
                    description=(
                        f"Folder for '{db_media.title}' [{db_media.id}] is not accessible:"
                        f" {db_media.folder_path}"
                    ),
                    details=db_media.folder_path,
                )
                ws_broadcast("", reload="issues")
            return False

    if not app_settings.wait_for_media:
        if row_id is not None:
            resolved = issue_repo.resolve(IssueType.FOLDER_MISSING, EntityType.MEDIA_TRAILER_STATUS, row_id)
            if resolved:
                ws_broadcast("", reload="issues")
        return True

    if not db_media.folder_path:
        logger.info(f"Media '{db_media.title}' [{db_media.id}] skipped: missing media folder path.")
        event_service.track_download_skipped(
            media_id=db_media.id,
            skip_reason="Missing media folder path",
            source_detail="DownloadMissingTrailers",
        )
        return False

    if not FilesHandler.check_media_exists(db_media.folder_path):
        logger.info(f"Media '{db_media.title}' [{db_media.id}] skipped: media file does not exist.")
        event_service.track_download_skipped(
            media_id=db_media.id,
            skip_reason="Media file not found",
            source_detail="DownloadMissingTrailers",
        )
        return False

    if row_id is not None:
        resolved = issue_repo.resolve(IssueType.FOLDER_MISSING, EntityType.MEDIA_TRAILER_STATUS, row_id)
        if resolved:
            ws_broadcast("", reload="issues")
    return True


async def download_missing_trailers(_stop_event: threading.Event | None = None) -> None:
    """Iterate monitored media and download trailers for all matching profiles."""
    if not app_settings.monitor_enabled:
        logger.warning("Monitoring is disabled, skipping trailers download")
        return

    all_profiles = trailer_profile_repo.read_all()
    enabled_profiles = [p for p in all_profiles if p.enabled]
    if not enabled_profiles:
        logger.info("No enabled trailer profiles — skipping.")
        return

    total_attempted = 0
    successful_downloads = 0
    failed_downloads = 0
    seen_media_ids: set[int] = set()
    skipped_media_ids: set[int] = set()       # folder-validation failures
    stop_monitoring_ids: set[int] = set()     # media IDs that fired stop_monitoring
    now = datetime.now(timezone.utc)

    for media in media_repo.read_all_generator(monitored_only=True):
        if _stop_event and _stop_event.is_set():
            logger.info("Stop event set, terminating download of missing trailers.")
            return

        if media.id in seen_media_ids or media.id in skipped_media_ids:
            continue
        seen_media_ids.add(media.id)

        matching = sorted(
            [
                p for p in enabled_profiles
                if p.for_movies == media.is_movie
                and matches_filters(media, p.customfilter.filters)
            ],
            key=lambda p: -(p.priority or 0),
        )
        if not matching:
            continue

        # Validate the media folder once before processing any profile.
        first_profile = matching[0]
        check_folder = first_profile.custom_folder == "{media_folder}"
        if not _is_valid_media(media, check_folder):
            skipped_media_ids.add(media.id)
            continue

        # Batch-load existing status rows for all matching profiles at once.
        profile_ids = [p.id for p in matching]
        existing_rows = trailer_status_repo.get_rows_for_media_and_profiles(media.id, profile_ids)

        for profile in matching:
            if media.id in stop_monitoring_ids:
                break

            _profile_name = profile.customfilter.filter_name
            seasons = _get_seasons_for_media(media, profile)

            for season in seasons:
                for seq in range(1, profile.max_count + 1):
                    row = existing_rows.get((profile.id, season, seq))
                    if _should_skip_slot(row, profile, now):
                        continue

                    if _stop_event and _stop_event.is_set():
                        logger.info("Stop event set, terminating download of missing trailers.")
                        return

                    logger.info(
                        f"Downloading trailer for '{media.title}' [{media.id}]"
                        f" using profile '{_profile_name}' (season={season}, seq={seq})"
                    )
                    try:
                        success = await download_trailer(
                            media,
                            profile,
                            profile.retry_count,
                            _stop_event=_stop_event,
                            season=season,
                            sequence=seq,
                        )
                        total_attempted += 1
                        if success:
                            successful_downloads += 1
                            if profile.stop_monitoring:
                                stop_monitoring_ids.add(media.id)
                                logger.info(
                                    f"stop_monitoring=True — skipping remaining profiles"
                                    f" for media '{media.title}' [{media.id}]."
                                )
                            break  # success: no more sequences for this (profile, season)
                    except DownloadFailedError:
                        total_attempted += 1
                        failed_downloads += 1
                        logger.warning(
                            f"Download failed for '{media.title}' with profile"
                            f" '{_profile_name}' (season={season}, seq={seq}) after all retries."
                        )
                        trailer_status_repo.upsert_slot_status(
                            media.id, profile.id, season, seq,
                            TrailerStatusEnum.FAILED,
                            increment_attempt=True,
                        )
                    except Exception as e:
                        total_attempted += 1
                        failed_downloads += 1
                        logger.exception(
                            f"Unexpected error for '{media.title}' [{media.id}]"
                            f" profile '{_profile_name}' (season={season}, seq={seq}): {e}"
                        )
                        trailer_status_repo.upsert_slot_status(
                            media.id, profile.id, season, seq,
                            TrailerStatusEnum.FAILED,
                            increment_attempt=True,
                        )

                    await utils.sleep_between_downloads(total_attempted, logger)

    logger.info(
        f"Finished downloading missing trailers."
        f" Attempted: {total_attempted},"
        f" Successful: {successful_downloads},"
        f" Failed: {failed_downloads}."
    )


# ─── Task-scheduling wrappers (called from API endpoints) ─────────────────────

@with_logging_context
async def _download_trailer_job(
    media: MediaRead,
    profile: TrailerProfileRead,
    retry_count: int,
    *,
    _job_id: str | None = None,
    _stop_event: threading.Event | None = None,
) -> None:
    await download_trailer(media, profile, retry_count, _stop_event=_stop_event)


def download_trailer_by_id(media_id: int, profile_id: int, yt_id: str = "") -> str:
    """Validate media/profile and schedule a one-shot background download job."""
    from tasks.scheduler import scheduler

    media = media_repo.read(media_id)
    profile = trailer_profile_repo.read(profile_id)
    _type = "Movie" if media.is_movie else "Series"

    if not media.folder_path:
        raise FolderPathEmptyError(f"{_type} '{media.title}' [{media.id}] has no folder path")
    if not FilesHandler.check_folder_exists(media.folder_path):
        raise FolderNotFoundError(folder_path=media.folder_path)

    retry_count = 3
    if yt_id:
        retry_count = 0
        media.youtube_trailer_id = yt_id
    elif profile.always_search:
        media.youtube_trailer_id = None

    scheduler.add_task(
        task_name=f"Download Trailer for {media.title}",
        func=_download_trailer_job,
        interval=86400.0,
        delay=1,
        run_once=True,
        args=(media, profile, retry_count),
    )
    msg = f"Trailer download started in background for {_type}: '{media.title}' [{media_id}]"
    if yt_id:
        msg += f" from ({yt_id})"
    logger.info(msg)
    return msg


@with_logging_context
async def _batch_download_job(
    media_list: list[MediaRead],
    profile: TrailerProfileRead,
    *,
    _job_id: str | None = None,
    _stop_event: threading.Event | None = None,
) -> None:
    await batch_download_task(media_list, profile, _stop_event=_stop_event)


def batch_download_trailers(profile_id: int, media_ids: list[int]) -> None:
    """Schedule a one-shot batch download job for a list of media IDs."""
    from tasks.scheduler import scheduler

    profile = trailer_profile_repo.read(profile_id)
    media_list: list[MediaRead] = []
    for media_id in media_ids:
        try:
            media = media_repo.read(media_id)
            if not media.folder_path or not FilesHandler.check_folder_exists(media.folder_path):
                continue
            media_list.append(media)
        except Exception:
            continue

    if not media_list:
        return

    scheduler.add_task(
        task_name=f"Batch Download Trailers ({len(media_list)} items)",
        func=_batch_download_job,
        interval=86400.0,
        delay=1,
        run_once=True,
        args=(media_list, profile),
    )
    logger.info(f"Batch download scheduled for {len(media_list)} media item(s) using profile '{profile.customfilter.filter_name}'")
