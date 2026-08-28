import asyncio
import os
import threading
from datetime import datetime, timezone
from app_logger import ModuleLogger
from config.settings import app_settings
import database.manager.event as event_manager
import database.manager.filefolderinfo as files_manager
import database.manager.download as download_manager
import database.manager.media as media_manager
from database.manager import trailerprofile
from database.models.event import EventSource
from database.models.media import MediaRead
from services.profiles import pick_profile_for_download
from services.trailers.trailers.service import (
    compute_file_hash,
    reanalyze_trailer_download,
    record_new_trailer_download,
    rename_trailer_download,
)
from services.files.media_scanner import MediaScanner
from services.files.files_handler import is_disk_available

logger = ModuleLogger("TrailersFilesScan")


def _ctime_matches_stored(ctime: float, stored: datetime) -> bool:
    """Compare filesystem st_ctime (UTC epoch float) to a stored datetime.
    SQLite returns naive datetimes in local time — use .astimezone() to convert
    to UTC, not .replace() which would mislabel local time as UTC."""
    if stored.tzinfo is None:
        stored = stored.astimezone(timezone.utc)
    return abs(ctime - stored.timestamp()) <= 1


def _has_folder_changed(folder_path: str, media_id: int, tz) -> bool:
    """Check root folder and immediate subdirs against stored modified times.
    Returns True if a scan is needed, False if nothing has changed."""
    stored = files_manager.get_folder_modified_times(media_id)
    if not stored:
        return True  # No stored data — first scan

    try:
        stored_root = stored.get(folder_path)
        if stored_root is None or not _ctime_matches_stored(
            os.stat(folder_path).st_ctime, stored_root
        ):
            return True

        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    stored_sub = stored.get(entry.path)
                    ctime = entry.stat(follow_symlinks=False).st_ctime
                    ctime_local = datetime.fromtimestamp(ctime, tz=tz)
                    ctime_utc = ctime_local.astimezone(timezone.utc)
                    if stored_sub is None or not _ctime_matches_stored(
                        ctime_utc.timestamp(), stored_sub
                    ):
                        return True
    except OSError:
        return True  # Can't stat — safer to scan

    return False


def _handle_folder_gone(media: MediaRead) -> None:
    """Reset stale flags when the media folder is inaccessible or deleted."""
    if media.media_exists:
        media_manager.update_media_exists(media.id, False)


# Moved to services.files.files_handler so the download task can share it; the alias
# keeps this module's historical import path and test patch targets working.
_is_disk_available = is_disk_available


async def _process_trailer_changes(
    media: MediaRead,
    trailer_paths: set[str],
    existing_downloads: list,
    source: EventSource,
) -> tuple[int, int, int, int]:
    """Detect new/renamed/modified trailers and mark deleted downloads.

    Matching is exact-path first; a disk path with no exact match is checked
    against still-unmatched "missing" downloads by content hash to recognize
    a rename/move (same file, keeps its history) before falling back to
    treating it as a genuinely new trailer. A path that matches exactly is
    additionally checked (cheap ctime pre-check, then hash) for in-place
    content edits made outside the app.

    Known limitation: a file that is both renamed *and* edited in the same
    scan window won't hash-match any missing download, so it falls through
    to "new" + "missing" rather than being recognized as one change — only
    pure renames and pure in-place edits are detected.

    Returns:
        tuple[int, int, int, int]: (new_trailer_count, missing_trailer_count,
            renamed_trailer_count, modified_trailer_count)
    """
    existing_paths = {d.path for d in existing_downloads}
    downloads_by_path = {d.path: d for d in existing_downloads}
    new_paths = [p for p in trailer_paths if p not in existing_paths]
    missing_downloads = [
        d for d in existing_downloads if d.path not in trailer_paths
    ]

    # --- Pass 1: rename/move detection — match new disk paths to unmatched
    # missing downloads by content hash, so the same row is updated in place
    # instead of deleting the old record and creating a brand-new one.
    renamed_count = 0
    claimed_ids: set[int] = set()
    still_new_paths = []
    for t_path in new_paths:
        match = None
        if missing_downloads:  # only hash if there's something to compare against
            t_hash = await asyncio.to_thread(compute_file_hash, t_path)
            match = next(
                (
                    d
                    for d in missing_downloads
                    if d.id not in claimed_ids
                    and d.file_hash
                    and d.file_hash == t_hash
                ),
                None,
            )
        if match:
            if await rename_trailer_download(match, t_path):
                renamed_count += 1
                claimed_ids.add(match.id)
                logger.info(
                    f"Trailer file renamed: '{match.path}' -> '{t_path}' for"
                    f" '{media.title}' [{media.id}]"
                )
                event_manager.track_trailer_renamed(
                    media_id=media.id,
                    old_path=match.path,
                    new_path=t_path,
                    source=source,
                    source_detail="FilesScan",
                )
                continue
        still_new_paths.append(t_path)

    # New trailer files found on disk that are not yet recorded as downloads.
    # Attribute each to the highest-priority matching profile that doesn't
    # already own an active download for this media (0 if none available).
    new_count = 0
    if still_new_paths:
        _profiles = trailerprofile.get_trailerprofiles()
        # Downloads whose file is gone get marked deleted below (same
        # condition as that loop) — their profiles are free to be claimed
        # by the new files, keeping ownership when a trailer is replaced.
        _stale_ids = {
            d.id
            for d in missing_downloads
            if d.id not in claimed_ids and not os.path.exists(d.path)
        }
        _used_profile_ids = {
            d.profile_id
            for d in existing_downloads
            if d.profile_id and d.id not in _stale_ids
        }
    for t_path in still_new_paths:
        new_count += 1
        _profile_id = pick_profile_for_download(
            media, _profiles, _used_profile_ids
        )
        if _profile_id:
            _used_profile_ids.add(_profile_id)
        logger.info(
            f"Found new trailer file: '{t_path}' for '{media.title}'"
            f" [{media.id}]"
        )
        await record_new_trailer_download(media, _profile_id, t_path)
        event_manager.track_trailer_detected(
            media_id=media.id,
            source=source,
            source_detail="FilesScan",
        )

    # Downloads whose file no longer exists on disk (renamed matches excluded)
    missing_count = 0
    for download in missing_downloads:
        if download.id in claimed_ids:
            continue
        if not os.path.exists(download.path):
            missing_count += 1
            logger.info(
                f"Trailer file deleted for download: '{download.path}' for"
                f" '{media.title}' [{media.id}]"
            )
            download_manager.mark_as_deleted(download.id)
            event_manager.track_trailer_deleted(
                media_id=media.id,
                reason="file_not_found",
                source=source,
                source_detail="FilesScan",
            )

    # --- Pass 4: in-place content-change detection for exact-path matches.
    # Cheap ctime pre-check (reusing the folder-change helper) gates the
    # expensive hash — zero extra cost in the common "nothing changed" case.
    modified_count = 0
    for t_path in trailer_paths:
        download = downloads_by_path.get(t_path)
        if download is None:
            continue
        try:
            ctime = os.stat(t_path).st_ctime
        except OSError:
            continue
        if _ctime_matches_stored(ctime, download.updated_at):
            continue  # unchanged — skip expensive hash
        new_hash = await asyncio.to_thread(compute_file_hash, t_path)
        if new_hash and new_hash != download.file_hash:
            if await reanalyze_trailer_download(download, t_path):
                modified_count += 1
                logger.info(
                    f"Trailer file content changed: '{t_path}' for"
                    f" '{media.title}' [{media.id}]"
                )
                event_manager.track_trailer_modified(
                    media_id=media.id,
                    old_hash=download.file_hash,
                    new_hash=new_hash,
                    source=source,
                    source_detail="FilesScan",
                )

    return new_count, missing_count, renamed_count, modified_count


async def scan_media_folder(
    media: MediaRead,
    scanner: MediaScanner | None = None,
    user_initiated: bool = True,
) -> tuple[int, int, int, int, int]:
    """Scan the media folder to find media files and trailers \
        and update the database with download records.
    Args:
        media (MediaRead): The media item to scan.
        scanner (MediaScanner | None): Optional scanner instance to use.
        user_initiated (bool): When False, skips scan if folder is unchanged.
    Returns:
        tuple[int, int, int, int, int]: Number of new, missing, renamed,
            content-modified, and disk-unavailable-skipped trailer files.
    """
    if not media.folder_path:
        return 0, 0, 0, 0, 0
    if scanner is None:
        scanner = MediaScanner()
    if not user_initiated and not _has_folder_changed(
        media.folder_path, media.id, scanner.tz
    ):
        return 0, 0, 0, 0, 0
    logger.debug(
        f"Scanning files for '{media.title}' [{media.id}] — folder changed"
    )

    all_downloads = [d for d in media.downloads if d.file_exists]
    files_info = await scanner.get_folder_files(media.folder_path, media.id)
    trailer_paths = (
        scanner.get_trailer_paths(files_info) if files_info else set()
    )

    # Guard: only pay for the reachability check at the moment a scan is
    # about to conclude "no trailers found" for a media that previously had
    # recorded downloads — the exact moment a disconnected network drive
    # would otherwise look identical to a genuine mass-deletion. Zero extra
    # cost in the common case (trailers still found, or nothing to lose).
    if not trailer_paths and all_downloads and not _is_disk_available(
        media.folder_path
    ):
        # TODO: once the planned "Issues" section exists, raise an issue
        # here to surface this to the user instead of only logging it.
        logger.error(
            f"Disk unavailable — cannot reach storage for '{media.title}' "
            f"[{media.id}] at '{media.folder_path}'. Skipping this scan to "
            "avoid marking existing trailers as missing; will retry on the "
            "next scheduled run. If this is a network drive, check the "
            "connection."
        )
        return 0, 0, 0, 0, 1

    if not files_info:
        _handle_folder_gone(media)
        return 0, 0, 0, 0, 0

    files_manager.update(media, files_info)

    disk_media_exists = await scanner.check_media_exists(files_info)
    if disk_media_exists != media.media_exists:
        media_manager.update_media_exists(media.id, disk_media_exists)

    source = EventSource.USER if user_initiated else EventSource.SYSTEM
    new, missing, renamed, modified = await _process_trailer_changes(
        media, trailer_paths, all_downloads, source
    )
    return new, missing, renamed, modified, 0


async def scan_all_media_folders(
    _stop_event: threading.Event | None = None,
) -> None:
    """Scan the disk for all media folders to find media files and trailers \
        and update the database with download records."""
    logger.info("Scanning disk for files and trailers.")

    force_full_scan = app_settings.files_full_scan
    if force_full_scan:
        logger.info(
            "FILES_FULL_SCAN is enabled — running full scan,"
            " bypassing folder-change check."
        )

    # Get all media items
    all_media = media_manager.read_all_generator

    # Get a FolderScan instance
    scanner = MediaScanner()

    # Scan each media item's folder to find files
    media_count = 0
    new_trailers = 0
    missing_trailers = 0
    renamed_trailers = 0
    modified_trailers = 0
    unavailable_count = 0
    for media in all_media():
        if _stop_event and _stop_event.is_set():
            logger.info("Stop event set, terminating scan of media folders.")
            return

        try:
            media_count += 1
            new, missing, renamed, modified, unavailable = await scan_media_folder(
                media, scanner, user_initiated=force_full_scan
            )
            new_trailers += new
            missing_trailers += missing
            renamed_trailers += renamed
            modified_trailers += modified
            unavailable_count += unavailable
        except Exception as e:
            logger.error(
                f"Error scanning media folder for '{media.title}'"
                f" [{media.id}]: {e}"
            )

    # Auto-reset so the optimisation resumes on future scans
    if force_full_scan:
        app_settings.files_full_scan = False
        logger.info("FILES_FULL_SCAN reset to False after full scan.")

    logger.info(
        "Completed scanning disk for files and trailers. "
        f"Total media scanned: {media_count}. "
        f"New trailers found: {new_trailers}. "
        f"Missing trailers: {missing_trailers}. "
        f"Renamed trailers: {renamed_trailers}. "
        f"Modified trailers: {modified_trailers}. "
        f"Skipped due to unavailable disk: {unavailable_count}."
    )
    if unavailable_count:
        # TODO: once the planned "Issues" section exists, raise an issue
        # here to surface this to the user instead of only logging it.
        logger.warning(
            f"{unavailable_count} media item(s) were skipped this run "
            "because their storage looked unreachable (e.g. a disconnected "
            "network drive) — see earlier errors for which ones. No "
            "existing trailers were marked missing for them."
        )
