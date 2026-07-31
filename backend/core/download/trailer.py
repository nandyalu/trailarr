from datetime import datetime, timezone
from pathlib import Path
import tempfile
import threading

from api.v1 import websockets
from app_logger import ModuleLogger
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.downloadattempt as attempt_manager
import core.base.database.manager.event as event_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.connection import ArrType
from core.base.database.models.event import EventSource
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download.inflight import inflight_registry
from core.download.trailers.service import record_new_trailer_download
from core.download.video_v2 import download_video
from core.download import trailer_file, trailer_search, video_analysis
from core.download.video_analysis import VideoInfo
from exceptions import DownloadFailedError, StopEventSetError

logger = ModuleLogger("TrailersDownloader")


async def _check_plex_trailer(
    media: MediaRead, profile: TrailerProfileRead
) -> bool:
    """Return True if Plex already has a trailer for this item.

    Calls get_library_item_extras for the media's plex_rating_key and checks
    for any extra with subtype 'trailer'. Persists the result to plex_trailer
    on the DB row so it's available for display in the frontend.
    Only runs when profile.skip_if_plex_trailer is True and the media is
    linked to a Plex connection.
    """
    if not profile.skip_if_plex_trailer:
        return False
    if not (media.plex_connection_id and media.plex_rating_key):
        return False

    # Use cached flag set by the weekly plex_trailer_refresh task.
    # None means the item hasn't been scanned yet — fall through to the API call.
    if media.plex_trailer is not None:
        return media.plex_trailer

    try:
        conn = connection_manager.read(media.plex_connection_id)
        if conn.arr_type != ArrType.PLEX:
            return False
        from core.plex.api_manager import PlexAPI

        api = PlexAPI(
            server_url=conn.url,
            token=conn.api_key,
            identifier=f"trailarr_{conn.id}",
        )
        extras = await api.get_library_item_extras(media.plex_rating_key)
        remote_trailers = [
            e
            for e in extras
            if e.subtype == "trailer" and not e.guid.startswith("file://")
        ]
        resolution_threshold = profile.skip_if_plex_trailer_resolution
        if resolution_threshold > 0:
            has_trailer = any(
                e.resolution >= resolution_threshold for e in remote_trailers
            )
        else:
            has_trailer = len(remote_trailers) > 0
        media_manager.update_plex_trailer(media.id, has_trailer)
        return has_trailer
    except Exception as e:
        logger.warning(
            f"Failed to check Plex trailer for '{media.title}'"
            f" [{media.id}]: {e}"
        )
        return False


async def _notify_plex(media: MediaRead) -> None:
    """Trigger a targeted Plex scan for a media item after trailer download.

    Reads the Plex connection, builds a PlexConnectionManager, and calls
    ``trigger_item_scan``.  Requires ``plex_connection_id``, ``plex_section_key``,
    and ``folder_path`` to all be set on the media row; silently skips if any
    are missing.
    """
    if not (
        media.plex_connection_id
        and media.plex_section_key
        and media.folder_path
    ):
        logger.debug(
            f"Skipping Plex scan notify for '{media.title}' [{media.id}]:"
            " missing plex_connection_id, plex_section_key, or folder_path"
        )
        return
    try:
        conn = connection_manager.read(media.plex_connection_id)
        if conn.arr_type != ArrType.PLEX:
            return
        # Import here to avoid a circular import at module level
        from core.plex.connection_manager import PlexConnectionManager

        plex_manager = PlexConnectionManager(conn)
        await plex_manager.trigger_item_scan(
            media_id=media.id,
            section_key=media.plex_section_key,
            folder_path=media.folder_path,
            source=EventSource.SYSTEM,
            source_detail="TrailerDownloaded",
        )
    except Exception as e:
        logger.warning(
            f"Failed to notify Plex for '{media.title}' [{media.id}]: {e}"
        )


def __record_download_facts(media: MediaRead):
    """Record the facts a successful download owns: downloaded_at and the
    YouTube id that was used.

    Phase 3: DOWNLOADING is runtime-only (see core/download/inflight.py) and
    is never written to the database.
    Phase 4: downloads never write `monitor` — it is user intent (invariant
    #6). No MONITOR_CHANGED events can originate from downloads anymore.
    Phase 5: the stored mirror columns are gone — download rows are the
    only record of downloaded-ness, so failures write nothing here.
    """
    update = MediaUpdateDC(
        id=media.id,
        downloaded_at=datetime.now(timezone.utc),
        yt_id=media.youtube_trailer_id,
    )
    media_manager.update_download_facts(update)
    return None


def __download_and_verify_trailer(
    media: MediaRead,
    video_id: str,
    profile: TrailerProfileRead,
    _stop_event: threading.Event | None = None,
) -> tuple[str, VideoInfo | None]:
    """Download the trailer and verify it.
    Returns:
        tuple[str, VideoInfo | None]: File path and video info for reuse.
    Raises:
        StopEventSetError: If the stop event is set during the download.
    """
    trailer_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(
        f"Downloading trailer for {media.title} [{media.id}] from"
        f" {trailer_url}"
    )
    # Use system temp directory for cross-platform compatibility
    tmp_dir = Path(tempfile.gettempdir()) / "trailarr"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    output_file = tmp_dir / f"{media.id}-trailer.{profile.file_format}"
    output_file = download_video(
        trailer_url, str(output_file), profile, _stop_event=_stop_event
    )

    # Verify and get video info in one pass
    is_valid, video_info = trailer_file.verify_download(
        output_file, media.title, profile
    )
    if not is_valid:
        raise DownloadFailedError("Trailer verification failed")

    if profile.remove_silence:
        if _stop_event and _stop_event.is_set():
            raise StopEventSetError("Stop event set during silence removal")

        output_file, _trimmed = video_analysis.remove_silence_at_end(
            output_file
        )
        # Re-analyze after silence removal as duration/size changed
        if _trimmed:
            video_info = video_analysis.get_media_info(output_file)

    return output_file, video_info


async def download_trailer(
    media: MediaRead,
    profile: TrailerProfileRead,
    retry_count: int = 2,
    exclude: list[str] | None = None,
    _stop_event: threading.Event | None = None,
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

    # Exclude the current trailer ID if an active download already uses it
    if media.youtube_trailer_id and any(
        d.file_exists for d in media.downloads
    ):
        exclude.append(media.youtube_trailer_id)

    # Ignore the current trailer ID if always_search is enabled
    if profile.always_search:
        media.youtube_trailer_id = None

    # Skip download if Plex already has a trailer and profile says to
    if await _check_plex_trailer(media, profile):
        logger.info(
            f"Plex already has a trailer for '{media.title}' [{media.id}],"
            " skipping download (skip_if_plex_trailer=True)"
        )
        return False

    # Get the video ID, search if needed
    video_id = trailer_search.get_video_id(media, profile, exclude)
    media.youtube_trailer_id = video_id

    if not video_id:
        raise DownloadFailedError(f"No trailer found for {media.title}")

    # Stop if stop event is set
    if _stop_event and _stop_event.is_set():
        logger.info(f"Download stopped for {media.title} [{media.id}]")
        return False

    # Runtime in-flight state — replaces the old DOWNLOADING status write.
    # The broadcast tells the frontend to refresh its downloading overlay.
    inflight_registry.start(media.id, profile.id)
    await websockets.ws_manager.broadcast(
        f"Downloading trailer for '{media.title}'",
        "Info",
        reload="downloading",
    )
    try:
        # Download the trailer and verify
        output_file, video_info = __download_and_verify_trailer(
            media, video_id, profile, _stop_event=_stop_event
        )
        # Move the trailer to the media folder (create subfolder if needed)
        final_path = trailer_file.move_trailer_to_folder(
            output_file, media, profile, video_info
        )
        # Record the download in the database
        await record_new_trailer_download(
            media, profile.id, final_path, video_id, video_info
        )
        # Success clears any failure-backoff record for this (media, profile)
        # — single choke point covering scheduled, manual, and batch paths
        attempt_manager.clear(media.id, profile.id)

        # Track trailer_downloaded event
        event_manager.track_trailer_downloaded(
            media_id=media.id,
            yt_id=video_id,
            source=EventSource.SYSTEM,
            source_detail="TrailerDownload",
        )

        # Record download facts last so any events they log (e.g.
        # YouTube ID Changed) appear after the Trailer Downloaded event
        __record_download_facts(media)

        # Notify Plex to scan the media folder if enabled in the profile
        if profile.notify_plex:
            await _notify_plex(media)

        msg = (
            f"Trailer downloaded successfully for {media.title} [{media.id}]"
            f" from ({video_id})"
        )
        logger.info(msg)
        # Finish BEFORE broadcasting so clients refetching the downloading
        # overlay on this message no longer see this media in flight. The
        # downloads reload matters too: computed status derives from it.
        inflight_registry.finish(media.id)
        await websockets.ws_manager.broadcast(
            msg, "Success", reload="media,downloads,downloading"
        )
        return True
    except Exception as e:
        logger.exception(f"Failed to download trailer: {e}")
        if _stop_event and _stop_event.is_set():
            logger.info(
                f"Download stopped for {media.title} [{media.id}] due to stop"
                " event."
            )
            return False
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
    finally:
        # Safety net for every failure/stop path (retries re-register in
        # their own frame; the pop is idempotent). Stale entries are also
        # cleared by task-lifecycle broadcasts and cost at most a lingering
        # spinner until the next 'downloading' reload.
        inflight_registry.finish(media.id)
