"""Download one trailer, from the search to the file in the media folder.

The steps are: find a video, download it, convert it, and move it into
place. A failure at any step is recorded as a failed attempt, which puts
that media and profile pair into backoff.
"""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import threading

from api.v1 import websockets
from app_logger import ModuleLogger
import database.manager.connection as connection_manager
import database.manager.download as download_manager
import database.manager.downloadattempt as attempt_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
from database.models.connection import ArrType
from database.models.download import DownloadRead
from database.models.event import EventSource
from database.models.helpers import MediaUpdateDC
from database.models.media import MediaRead
from database.models.trailerprofile import TrailerProfileRead
from services.files import service as files_service
from services.trailers.inflight import inflight_registry
from services.trailers.trailers.service import (
    record_new_trailer_download,
    rename_trailer_download,
)
from services.trailers.video_v2 import download_video
from services.trailers import (
    resolver,
    trailer_file,
    trailer_search,
    video_analysis,
)
from services.trailers.video_analysis import VideoInfo
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
        from services.connections.plex.api_manager import PlexAPI

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
            f"Trailarr could not check whether Plex has a trailer for"
            f" '{media.title}': {e}",
            **logger.media(media.id),
        )
        return False


async def _notify_plex(media: MediaRead) -> None:
    """Make a downloaded trailer visible in Plex.

    Reads the Plex connection, builds a PlexConnectionManager, and calls
    ``trigger_item_scan``, which scans the media folder and refreshes the
    item's metadata. Both are needed: the scan indexes the new file, and
    the refresh is what attaches it to the item as a local extra.

    Requires ``plex_connection_id``, ``plex_section_key``, and
    ``folder_path`` to all be set on the media row; silently skips if any
    are missing. The metadata refresh also needs ``plex_rating_key``.
    """
    if not (
        media.plex_connection_id
        and media.plex_section_key
        and media.folder_path
    ):
        logger.debug(
            f"Trailarr does not tell Plex about '{media.title}':"
            " missing plex_connection_id, plex_section_key, or folder_path"
        )
        return
    try:
        conn = connection_manager.read(media.plex_connection_id)
        if conn.arr_type != ArrType.PLEX:
            return
        # Import here to avoid a circular import at module level
        from services.connections.plex.connection_manager import (
            PlexConnectionManager,
        )

        plex_manager = PlexConnectionManager(conn)
        await plex_manager.trigger_item_scan(
            media_id=media.id,
            section_key=media.plex_section_key,
            folder_path=media.folder_path,
            rating_key=media.plex_rating_key,
            source=EventSource.SYSTEM,
            source_detail="TrailerDownloaded",
        )
    except Exception as e:
        logger.warning(
            f"Trailarr could not tell Plex about the new trailer for"
            f" '{media.title}': {e}",
            **logger.media(media.id),
        )


def __record_download_facts(media: MediaRead):
    """Record the facts a successful download owns: downloaded_at and the
    YouTube id that was used.

    Phase 3: DOWNLOADING is runtime-only (see services/trailers/inflight.py) and
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
    stop_event: threading.Event | None = None,
) -> tuple[str, VideoInfo | None]:
    """Download the trailer and verify it.
    Returns:
        tuple[str, VideoInfo | None]: File path and video info for reuse.
    Raises:
        StopEventSetError: If the stop event is set during the download.
    """
    trailer_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(
        f"Trailarr downloads the trailer for '{media.title}' from"
        f" {trailer_url}.",
        **logger.media(media.id),
    )
    # Use system temp directory for cross-platform compatibility
    tmp_dir = Path(tempfile.gettempdir()) / "trailarr"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    output_file = tmp_dir / f"{media.id}-trailer.{profile.file_format}"
    output_file = download_video(
        trailer_url, str(output_file), profile, stop_event=stop_event
    )

    # Verify and get video info in one pass
    is_valid, video_info = trailer_file.verify_download(
        output_file, media.title, profile
    )
    if not is_valid:
        raise DownloadFailedError("Trailer verification failed")

    if profile.remove_silence:
        if stop_event and stop_event.is_set():
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
    stop_event: threading.Event | None = None,
    replace: list[DownloadRead] | None = None,
) -> bool:
    """Download trailer for a media object with given profile.
    Args:
        media (MediaRead): The media object to download the trailer for.
        profile (TrailerProfileRead): The trailer profile to use.
        retry_count (int, optional): Number of retries if download fails. Defaults to 2.
        exclude (list[str], optional): List of video IDs to exclude from search. Defaults to None.
        stop_event (threading.Event, optional): Set when the task that
            runs this download is stopped. Every retry gets it too.
        replace (list[DownloadRead], optional): The trailers of this
            profile that `Upgrade To TMDB Trailer` replaces. When given,
            only a TMDB trailer (or a video the user chose) is downloaded,
            and never a search result. Defaults to None.
    Returns:
        bool: True if trailer download was successful, False otherwise.
    Raises:
        DownloadFailedError: If trailer download fails.
    """
    logger.info(
        f"Trailarr downloads the trailer for '{media.title}'.",
        **logger.media(media.id),
    )
    if not exclude:
        exclude = []

    if replace:
        # An upgrade replaces the trailers of this profile, so their videos
        # are left out. A video that another profile has on disk is not:
        # it can be the only TMDB trailer in the language, and this
        # profile wants its own copy of it, made with its own settings.
        # Leaving it out gave the upgrade no target, and it never searches,
        # so the profile failed and backed off on every run (Copilot
        # review on #696).
        exclude.extend(
            download.youtube_id for download in replace if download.youtube_id
        )
    else:
        # Do not download a video that this media item already has on
        # disk. Phase 8: read the ids from the downloads themselves.
        # Reading the single `media.youtube_trailer_id` missed every video
        # but the last one, and the resolver now offers a list.
        exclude.extend(
            download.youtube_id
            for download in media.downloads
            if download.file_exists and download.youtube_id
        )

    # `Always Search` is applied by the resolver, which skips the videos a
    # search stored earlier and keeps the ones a person or TMDB chose.

    if replace:
        # An upgrade does not ask Plex: Plex has a trailer because
        # Trailarr put the old one there.
        if not _upgrade_still_needed(media, profile, replace):
            return False
    # Skip download if Plex already has a trailer and profile says to
    elif await _check_plex_trailer(media, profile):
        logger.info(
            f"Plex already has a trailer for '{media.title}'. Trailarr does"
            " not download another one, because Skip If Plex Has A Trailer"
            " is on.",
            **logger.media(media.id),
        )
        return False

    # Get the video ID, search if needed
    video_id = trailer_search.get_video_id(
        media, profile, exclude, upgrade_only=bool(replace)
    )
    media.youtube_trailer_id = video_id

    if not video_id:
        if replace:
            # The item has a trailer. The pending view shows this text,
            # so it must not read as if the item had none.
            raise DownloadFailedError(
                f"No TMDB trailer of '{media.title}' could be downloaded,"
                " so the current trailer stays."
            )
        raise DownloadFailedError(f"No trailer found for {media.title}")

    # Stop if stop event is set
    if stop_event and stop_event.is_set():
        logger.info(
            f"Trailarr stopped the download for '{media.title}'.",
            **logger.media(media.id),
        )
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
            media, video_id, profile, stop_event=stop_event
        )
        # Move the trailer to the media folder (create subfolder if needed)
        final_path = trailer_file.move_trailer_to_folder(
            output_file, media, profile, video_info
        )
        # Record the download in the database
        recorded = await record_new_trailer_download(
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

        if replace and not recorded:
            # The new file is on disk, but Trailarr has no record of it.
            # The old trailer is the only one it tracks, so it stays. The
            # next files scan finds the new file.
            logger.warning(
                f"Trailarr could not record the new trailer of"
                f" '{media.title}', so it keeps the old one.",
                **logger.media(media.id),
            )
        elif replace:
            # The new trailer is in place and recorded before the old one
            # goes, so a failure above never leaves the item with none.
            # This runs after the Trailer Downloaded event, so the history
            # reads "downloaded", then "deleted, replaced".
            try:
                await _finish_upgrade(
                    media, profile, replace, final_path, video_info
                )
            except Exception as e:
                # The new trailer is in place. A failure here must not
                # reach the retry below, which would download another one.
                logger.exception(
                    f"Trailarr replaced the trailer of '{media.title}' but"
                    f" could not remove the old one: {e}",
                    **logger.media(media.id),
                )

        # Record download facts last so any events they log (e.g.
        # YouTube ID Changed) appear after the Trailer Downloaded event
        __record_download_facts(media)

        # Notify Plex to scan the media folder if enabled in the profile
        if profile.notify_plex:
            await _notify_plex(media)

        msg = (
            f"Trailarr downloaded the trailer for '{media.title}'"
            f" from video {video_id}."
        )
        logger.info(msg, **logger.media(media.id))
        # Finish BEFORE broadcasting so clients refetching the downloading
        # overlay on this message no longer see this media in flight. The
        # downloads reload matters too: computed status derives from it.
        inflight_registry.finish(media.id)
        await websockets.ws_manager.broadcast(
            msg, "Success", reload="media,downloads,downloading"
        )
        return True
    except Exception as e:
        logger.exception(f"Trailarr could not download the trailer: {e}")
        if stop_event and stop_event.is_set():
            logger.info(
                f"Trailarr stopped the download for '{media.title}'. A stop was"
                " requested.",
                **logger.media(media.id),
            )
            return False
        if retry_count > 0:
            logger.info(
                f"Trailarr tries the download for '{media.title}' again."
                f" Attempt {3 - retry_count} of 3.",
                **logger.media(media.id),
            )
            # The failed video is not offered again in this chain, so the
            # next call takes the next candidate from the table.
            if video_id:
                exclude.append(video_id)
            return await download_trailer(
                media,
                profile,
                retry_count - 1,
                exclude,
                stop_event=stop_event,
                replace=replace,
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


def _upgrade_still_needed(
    media: MediaRead,
    profile: TrailerProfileRead,
    replace: list[DownloadRead],
) -> bool:
    """Check the upgrade again, with the TMDB list as it is now.

    The download task decided on the list it read before, and asked TMDB
    again just before this call. The new answer can list the trailer that
    is already on disk, or nothing at all. Either way the trailer stays.
    """
    candidates = video_manager.read_candidates(media.id)
    targets = resolver.upgrade_targets(candidates, profile)
    if not targets:
        logger.info(
            f"TMDB lists no trailer for '{media.title}' that the profile"
            f" '{profile.customfilter.filter_name}' can use. Trailarr keeps"
            " the current trailer.",
            **logger.media(media.id),
        )
        return False
    kept = resolver.upgrade_keeps(candidates, targets)
    if any(download.youtube_id in kept for download in replace):
        logger.info(
            f"The trailer of '{media.title}' is already a TMDB trailer or a"
            " video you chose. Trailarr keeps it.",
            **logger.media(media.id),
        )
        return False
    logger.info(
        f"Trailarr replaces the trailer of '{media.title}' with a TMDB"
        f" trailer, because Upgrade To TMDB Trailer is on in the profile"
        f" '{profile.customfilter.filter_name}'.",
        **logger.media(media.id),
    )
    return True


async def _finish_upgrade(
    media: MediaRead,
    profile: TrailerProfileRead,
    replace: list[DownloadRead],
    new_path: str,
    video_info: VideoInfo | None,
) -> None:
    """Delete the replaced trailers, when the profile says to.

    The new trailer then takes the name of the one it replaces, when that
    is the name the profile gives it. Without this, every upgraded file
    would keep the "Trailer 2" name that it got while the old file was
    still there.
    """
    if not profile.delete_replaced_trailer:
        logger.info(
            f"Trailarr keeps the replaced trailer of '{media.title}',"
            " because Delete Replaced Trailer is off.",
            **logger.media(media.id),
        )
        return
    deleted: list[str] = []
    for download in replace:
        if not await files_service.delete_file_or_folder(
            download.path, media.id
        ):
            logger.warning(
                f"Trailarr could not delete the replaced trailer"
                f" '{download.path}' of '{media.title}'.",
                **logger.media(media.id),
            )
            continue
        deleted.append(download.path)
        event_manager.track_trailer_deleted(
            media_id=media.id,
            reason="Replaced by a TMDB trailer",
            source=EventSource.SYSTEM,
            source_detail="TrailerUpgrade",
        )
        logger.info(
            f"Trailarr deleted the replaced trailer '{download.path}' of"
            f" '{media.title}'.",
            **logger.media(media.id),
        )
    if deleted:
        await _take_replaced_name(
            media, profile, new_path, deleted, video_info
        )


async def _take_replaced_name(
    media: MediaRead,
    profile: TrailerProfileRead,
    new_path: str,
    deleted: list[str],
    video_info: VideoInfo | None,
) -> None:
    """Rename the new trailer to the name of a trailer it replaced."""
    current = Path(new_path)
    preferred = trailer_file.get_trailer_path(
        current,
        current.parent,
        media,
        profile,
        video_info=video_info,
    )
    if preferred not in deleted:
        # The name that the profile gives now is not a name that this
        # upgrade freed. Another file holds it, or the profile changed.
        return
    new_download = next(
        (
            d
            for d in download_manager.read_by_media_id(media.id)
            if d.path == new_path and d.file_exists
        ),
        None,
    )
    if new_download is None:
        return
    try:
        current.rename(preferred)
    except OSError as e:
        logger.warning(
            f"Trailarr could not rename the new trailer of '{media.title}'"
            f" to '{preferred}': {e}",
            **logger.media(media.id),
        )
        return
    await rename_trailer_download(new_download, preferred)
