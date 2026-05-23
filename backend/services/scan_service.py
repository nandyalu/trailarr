"""Scan service — business logic for detecting trailer and media-file changes on disk.

Tasks call scan_media_folder() per media item; scan_all_media_folders() in
tasks/files_scan.py is the orchestration loop that drives it.
"""
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from app_logger import ModuleLogger
import db.repos.download as download_repo
import db.repos.file_info as file_info_repo
import db.repos.issue as issue_repo
import db.repos.media as media_repo
import db.repos.trailer_profile as trailer_profile_repo
import db.repos.trailer_status as trailer_status_repo
from db.models.event import EventSource
from db.models.issue import EntityType, IssueType
from db.models.media import MediaRead
from download.pipeline import record_new_trailer_download
from services import event_service
from utils.media_scanner import MediaScanner
from ws.manager import broadcast as ws_broadcast

logger = ModuleLogger("ScanService")


# ─── Tier 1 — Template reverse-match ──────────────────────────────────────────

def _build_filename_pattern(template: str) -> re.Pattern:
    """Convert a file_name template into a regex for reverse-matching filenames."""
    parts = re.split(r"\{(\w+)\}", template)
    seen: set[str] = set()
    result = ["^"]
    for i, part in enumerate(parts):
        if i % 2 == 0:
            result.append(re.escape(part))
        else:
            var = part
            if var == "ii":
                result.append(r"(?:\d+)?")
                continue
            named = var not in seen
            seen.add(var)
            if var in ("season", "sequence", "year"):
                result.append(f"(?P<{var}>\\d+)" if named else r"(?:\d+)")
            elif var == "ext":
                result.append(f"(?P<{var}>[a-zA-Z0-9]+)" if named else r"(?:[a-zA-Z0-9]+)")
            else:
                result.append(f"(?P<{var}>.+?)" if named else r"(?:.+?)")
    result.append("$")
    return re.compile("".join(result), re.IGNORECASE)


def _attribute_tier1(
    filename: str,
    profiles: list,
    media: MediaRead,
) -> list[tuple[int, int, int]]:
    """Return list of (profile_id, season, sequence) via template reverse-match."""
    matches = []
    for profile in profiles:
        if not profile.enabled:
            continue
        if media.is_movie != profile.for_movies:
            continue
        try:
            pattern = _build_filename_pattern(profile.file_name)
        except re.error:
            logger.debug(f"Could not build pattern for profile {profile.id}: {profile.file_name!r}")
            continue
        m = pattern.match(filename)
        if m:
            groups = m.groupdict()
            season = int(groups["season"]) if groups.get("season") is not None else 0
            sequence = int(groups["sequence"]) if groups.get("sequence") is not None else 1
            matches.append((profile.id, season, sequence))
    return matches


# ─── Tier 2 — Metadata match ──────────────────────────────────────────────────

def _attribute_tier2(
    file_path: str,
    profiles: list,
    media: MediaRead,
) -> list[int]:
    """Return profile_ids whose resolution/duration requirements the file satisfies."""
    from download.analysis import get_media_info
    from download.pipeline import get_resolution_label

    info = get_media_info(file_path)
    if not info:
        return []
    video_stream = next((s for s in info.streams if s.codec_type == "video"), None)
    height = video_stream.coded_height if video_stream else 0
    file_resolution = get_resolution_label(height)
    duration = info.duration_seconds

    satisfied = []
    for profile in profiles:
        if not profile.enabled:
            continue
        if media.is_movie != profile.for_movies:
            continue
        if file_resolution < profile.video_resolution:
            continue
        if not (profile.min_duration <= duration <= profile.max_duration):
            continue
        satisfied.append(profile.id)
    return satisfied


def _ctime_matches_stored(ctime: float, stored: datetime) -> bool:
    if stored.tzinfo is None:
        stored = stored.astimezone(timezone.utc)
    return abs(ctime - stored.timestamp()) <= 1


def has_folder_changed(folder_path: str, media_id: int, tz) -> bool:
    stored = file_info_repo.get_folder_modified_times(media_id)
    if not stored:
        return True
    try:
        stored_root = stored.get(folder_path)
        if stored_root is None or not _ctime_matches_stored(os.stat(folder_path).st_ctime, stored_root):
            return True
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    stored_sub = stored.get(entry.path)
                    ctime = entry.stat(follow_symlinks=False).st_ctime
                    ctime_local = datetime.fromtimestamp(ctime, tz=tz)
                    ctime_utc = ctime_local.astimezone(timezone.utc)
                    if stored_sub is None or not _ctime_matches_stored(ctime_utc.timestamp(), stored_sub):
                        return True
    except OSError:
        return True
    return False


async def _process_trailer_changes(
    media: MediaRead,
    trailer_paths: set[str],
    existing_downloads: list,
    deleted_downloads: list,
    source: EventSource,
) -> tuple[int, int]:
    existing_paths = {d.path for d in existing_downloads}
    deleted_by_path = {d.path: d for d in deleted_downloads}

    for t_path in trailer_paths:
        if t_path in deleted_by_path:
            old_download = deleted_by_path[t_path]
            resolved = issue_repo.resolve(IssueType.FILE_DELETED, EntityType.DOWNLOAD, old_download.id)
            if resolved:
                logger.info(
                    f"Trailer file restored: '{t_path}' for '{media.title}' [{media.id}]"
                    " — FILE_DELETED issue resolved."
                )
                ws_broadcast("", reload="issues")

    profiles = trailer_profile_repo.read_all()
    new_count = 0
    for t_path in trailer_paths:
        if t_path in existing_paths:
            continue
        new_count += 1
        logger.info(f"Found new trailer file: '{t_path}' for '{media.title}' [{media.id}]")

        filename = Path(t_path).name
        tier1_matches = _attribute_tier1(filename, profiles, media)
        if tier1_matches:
            profile_id, season, sequence = tier1_matches[0]
            matched_profile = next((p for p in profiles if p.id == profile_id), None)
            vt = (matched_profile.video_type.value if matched_profile and hasattr(matched_profile.video_type, "value") else str(matched_profile.video_type)) if matched_profile else "trailer"
            row = trailer_status_repo.get_first_pending_row_for_profile(media.id, profile_id, season)
            status_row_id = row.id if row else None
            await record_new_trailer_download(media, profile_id, t_path, status_row_id=status_row_id, video_type=vt)
        else:
            tier2_matches = _attribute_tier2(t_path, profiles, media)
            if tier2_matches:
                profile_id = tier2_matches[0]
                matched_profile = next((p for p in profiles if p.id == profile_id), None)
                vt = (matched_profile.video_type.value if matched_profile and hasattr(matched_profile.video_type, "value") else str(matched_profile.video_type)) if matched_profile else "trailer"
                row = trailer_status_repo.get_first_pending_row_for_profile(media.id, profile_id)
                status_row_id = row.id if row else None
                await record_new_trailer_download(media, profile_id, t_path, status_row_id=status_row_id, video_type=vt)
            else:
                await record_new_trailer_download(media, 0, t_path, video_type="other")

        event_service.track_trailer_detected(
            media_id=media.id,
            source=source,
            source_detail="FilesScan",
        )

    missing_count = 0
    for download in existing_downloads:
        if download.path in trailer_paths:
            continue
        if not os.path.exists(download.path):
            missing_count += 1
            logger.info(
                f"Trailer file deleted for download: '{download.path}'"
                f" for '{media.title}' [{media.id}]"
            )
            download_repo.mark_as_deleted(download.id)
            event_service.track_trailer_deleted(
                media_id=media.id,
                reason="file_not_found",
                source=source,
                source_detail="FilesScan",
            )
            issue_repo.upsert(
                issue_type=IssueType.FILE_DELETED,
                entity_type=EntityType.DOWNLOAD,
                entity_id=download.id,
                description=(
                    f"Trailer file for '{media.title}' was deleted externally."
                    f" Path: {download.path}"
                ),
                details=download.path,
            )
            ws_broadcast("", reload="issues")

    return new_count, missing_count


async def scan_media_folder(
    media: MediaRead,
    scanner: MediaScanner | None = None,
    user_initiated: bool = True,
) -> tuple[int, int]:
    if not media.folder_path:
        return 0, 0
    if scanner is None:
        scanner = MediaScanner()
    if not user_initiated and not has_folder_changed(media.folder_path, media.id, scanner.tz):
        return 0, 0
    logger.debug(f"Scanning files for '{media.title}' [{media.id}] — folder changed")

    files_info = await scanner.get_folder_files(media.folder_path, media.id)
    if not files_info:
        if media.media_exists:
            media_repo.update_media_exists(media.id, False)
        return 0, 0

    file_info_repo.upsert(media, files_info)

    disk_media_exists = await scanner.check_media_exists(files_info)
    if disk_media_exists != media.media_exists:
        media_repo.update_media_exists(media.id, disk_media_exists)

    trailer_paths = scanner.get_trailer_paths(files_info)
    existing_downloads = [d for d in media.downloads if d.file_exists]
    deleted_downloads = [d for d in media.downloads if not d.file_exists]
    source = EventSource.USER if user_initiated else EventSource.SYSTEM
    return await _process_trailer_changes(media, trailer_paths, existing_downloads, deleted_downloads, source)
