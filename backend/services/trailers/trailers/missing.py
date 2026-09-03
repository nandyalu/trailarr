"""Find the media items that still need a trailer, and download them.

For each media item, this module works out which profiles match, which of
those are already satisfied, and which are in backoff after a failure. What
is left is downloaded.

A media item whose storage is unreachable is skipped rather than failed. A
failure would count as an attempt and push the item into backoff for a
problem that is not its own.
"""

import os
import threading
from contextlib import closing
from dataclasses import dataclass

from app_logger import ModuleLogger
from config.settings import app_settings
from database.manager import trailerprofile
import database.manager.download as download_manager
import database.manager.downloadattempt as attempt_manager
import database.manager.event as event_manager
import database.manager.media as media_manager
from database.models.downloadattempt import (
    DownloadAttemptRead,
    is_eligible,
    next_eligible_at,
)
from database.models.media import MediaRead
from database.models.trailerprofile import TrailerProfileRead
from services.profiles import find_matching_profiles
from services.satisfaction import evaluate_satisfaction
from services.trailers import trailer as trailer_downloader
from services.trailers.inflight import inflight_registry
from services.trailers.trailers import utils
from services.files.files_handler import FilesHandler, is_disk_available
from tasks.startup_passes import downloads_ready
from exceptions import DownloadFailedError, ItemNotFoundError

logger = ModuleLogger("TrailerDownloadTasks")


@dataclass(frozen=True)
class _WorkItem:
    """Identify media and the profile pairs proposed by one sweep."""

    media_id: int
    profile_ids: frozenset[int]


def _is_valid_media(
    db_media: MediaRead,
    check_folder: bool = True,
) -> bool:
    """Check if a media item is valid for downloading."""
    if check_folder:
        if db_media.folder_path is None:
            logger.info(
                f"Trailarr skips '{db_media.title}'. It has no folder path.",
                **logger.media(db_media.id),
            )
            event_manager.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Missing folder path",
                source_detail="DownloadMissingTrailers",
            )
            return False

        if not FilesHandler.check_folder_exists(db_media.folder_path):
            # Distinguish "folder genuinely missing" from "the storage
            # backing it is unreachable" (disconnected network mount) —
            # an offline drive must not be treated like a normal missing
            # folder, and must never lead to writes into a dead mount.
            if not is_disk_available(db_media.folder_path):
                logger.info(
                    f"Trailarr skips '{db_media.title}'. It cannot reach the storage"
                    " of the media folder.",
                    **logger.media(db_media.id),
                )
                event_manager.track_download_skipped(
                    media_id=db_media.id,
                    skip_reason="Storage unreachable",
                    source_detail="DownloadMissingTrailers",
                )
                return False
            # The storage is reachable, so the folder is genuinely
            # missing. Create it when the user asked for that; otherwise
            # skip as before.
            if app_settings.create_missing_folders:
                if FilesHandler.create_folder(db_media.folder_path):
                    logger.info(
                        f"Trailarr created the missing folder for '{db_media.title}':"
                        f" '{db_media.folder_path}'.",
                        **logger.media(db_media.id),
                    )
                    return True
                logger.info(
                    f"Trailarr skips '{db_media.title}'. It could not create the"
                    " missing folder.",
                    **logger.media(db_media.id),
                )
                event_manager.track_download_skipped(
                    media_id=db_media.id,
                    skip_reason="Could not create folder",
                    source_detail="DownloadMissingTrailers",
                )
                return False
            logger.info(
                f"Trailarr skips '{db_media.title}'. Its folder does not exist.",
                **logger.media(db_media.id),
            )
            event_manager.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Folder does not exist",
                source_detail="DownloadMissingTrailers",
            )
            return False

        # Folder exists — confirm it is actually readable. A stale handle
        # on a half-dead network mount can pass the isdir check but fail
        # on first read; downloading would then fail mid-write and be
        # recorded as a failed *attempt* (accruing backoff) when the real
        # problem is storage, which must be a skip instead.
        try:
            os.listdir(db_media.folder_path)
        except OSError as exc:
            logger.info(
                f"Trailarr skips '{db_media.title}'. It cannot read the media"
                f" folder ({exc}). The storage may be down.",
                **logger.media(db_media.id),
            )
            event_manager.track_download_skipped(
                media_id=db_media.id,
                skip_reason="Storage unreachable",
                source_detail="DownloadMissingTrailers",
            )
            return False

    if not app_settings.wait_for_media:
        return True

    if not db_media.folder_path:
        logger.info(
            f"Trailarr skips '{db_media.title}'. It has no folder path.",
            **logger.media(db_media.id),
        )
        event_manager.track_download_skipped(
            media_id=db_media.id,
            skip_reason="Missing media folder path",
            source_detail="DownloadMissingTrailers",
        )
        return False

    if not FilesHandler.check_media_exists(db_media.folder_path):
        logger.info(
            f"Trailarr skips '{db_media.title}'. Its media file does not"
            " exist.",
            **logger.media(db_media.id),
        )
        event_manager.track_download_skipped(
            media_id=db_media.id,
            skip_reason="Media file not found",
            source_detail="DownloadMissingTrailers",
        )
        return False

    return True


def _apply_claims(
    media: MediaRead,
    claims: list[tuple[int, int]],
    profiles_by_id: dict[int, TrailerProfileRead],
) -> None:
    """Attribute unattributed existing downloads to the matching profiles
    that would otherwise download again (satisfaction rule claims)."""
    for download_id, profile_id in claims:
        download_manager.update_profile_id(download_id, profile_id)
        profile = profiles_by_id.get(profile_id)
        _name = (
            profile.customfilter.filter_name if profile else str(profile_id)
        )
        logger.info(
            f"'{media.title}' already has a trailer from download"
            f" {download_id}. Trailarr assigned it to profile '{_name}'"
            " and did not download it again.",
            **logger.media(media.id),
        )


def _filter_backoff_eligible(
    media: MediaRead,
    unsatisfied: list[TrailerProfileRead],
    attempts: dict[int, DownloadAttemptRead] | None = None,
) -> list[TrailerProfileRead]:
    """Drop profiles whose (media, profile) key is still backing off after
    previous failed download attempts."""
    if not unsatisfied:
        return []
    if attempts is None:
        attempts = {
            a.profile_id: a for a in attempt_manager.read_for_media(media.id)
        }
    eligible: list[TrailerProfileRead] = []
    for profile in unsatisfied:
        attempt = attempts.get(profile.id)
        if is_eligible(attempt):
            eligible.append(profile)
        else:
            assert attempt is not None
            logger.debug(
                f"Trailarr waits before it tries '{media.title}' again with the"
                f" profile {profile.id}. {attempt.attempt_count} attempts have"
                f" failed. The next attempt is at"
                f" {next_eligible_at(attempt)}.",
                **logger.media(media.id),
            )
    return eligible


def _build_work_list(
    attempted_pairs: set[tuple[int, int]],
    enabled_profiles: list[TrailerProfileRead],
    profiles_by_id: dict[int, TrailerProfileRead],
    _stop_event: threading.Event | None = None,
) -> tuple[list[_WorkItem], int]:
    """Build one sweep without holding a database session during downloads.

    The scan walks every monitored row, so it checks the stop event as it
    goes — a run cancelled here must not wait for a whole library."""
    attempts_by_key = {
        (attempt.media_id, attempt.profile_id): attempt
        for attempt in attempt_manager.read_all()
    }
    work_items: list[_WorkItem] = []
    scanned_media = 0

    with closing(
        media_manager.read_all_generator(monitored_only=True)
    ) as media_rows:
        for media in media_rows:
            if _stop_event and _stop_event.is_set():
                break
            scanned_media += 1
            matching_profiles = find_matching_profiles(media, enabled_profiles)
            if not matching_profiles:
                continue
            result = evaluate_satisfaction(media, matching_profiles)
            if result.claims:
                # Claims write to the database. A row deleted by a
                # concurrent Arr refresh must cost this media item, not
                # the whole run.
                try:
                    _apply_claims(media, result.claims, profiles_by_id)
                except Exception:
                    logger.exception(
                        "Trailarr could not attribute the existing downloads"
                        f" of '{media.title}'.",
                        **logger.media(media.id),
                    )
            attempts = {
                profile.id: attempts_by_key[(media.id, profile.id)]
                for profile in result.unsatisfied
                if profile.id is not None
                and (media.id, profile.id) in attempts_by_key
            }
            eligible_profiles = _filter_backoff_eligible(
                media, result.unsatisfied, attempts
            )
            profile_ids = frozenset(
                profile.id
                for profile in eligible_profiles
                if profile.id is not None
                and (media.id, profile.id) not in attempted_pairs
            )
            if profile_ids:
                work_items.append(_WorkItem(media.id, profile_ids))

    return work_items, scanned_media


def _read_current_eligible_profiles(
    media_id: int,
) -> tuple[MediaRead, list[TrailerProfileRead]]:
    """Re-read media and profiles before deciding what to download."""
    media = media_manager.read(media_id)
    if not media.monitor:
        return media, []

    all_profiles = trailerprofile.get_trailerprofiles()
    enabled_profiles = [profile for profile in all_profiles if profile.enabled]
    matching_profiles = find_matching_profiles(media, enabled_profiles)
    result = evaluate_satisfaction(media, matching_profiles)
    if result.claims:
        profiles_by_id = {
            profile.id: profile
            for profile in all_profiles
            if profile.id is not None
        }
        # Guarded separately so that an ItemNotFoundError raised by a claim
        # write is never mistaken for "this media item is gone".
        try:
            _apply_claims(media, result.claims, profiles_by_id)
        except Exception:
            logger.exception(
                "Trailarr could not attribute the existing downloads of"
                f" '{media.title}'.",
                **logger.media(media.id),
            )
    return media, _filter_backoff_eligible(media, result.unsatisfied)


_PREVIEW_LOG_LIMIT = 25


async def _run_preview_pass() -> None:
    """Downloads disabled: publish the would-download list instead.

    Uses the same library-wide pending computation as GET /media/pending,
    which itself reuses the task's exact satisfaction rule — the preview is
    the real work list, not an estimate."""
    from api.v1.websockets import ws_manager
    from services.trailers.trailers.pending import compute_library_pending

    summary = compute_library_pending(limit=1000)
    would_download = [i for i in summary.items if i.reason == "pending"]
    for item in would_download[:_PREVIEW_LOG_LIMIT]:
        logger.info(
            f"Preview: Trailarr would download '{item.title}' with the"
            f" profile '{item.profile_name}'.",
            **logger.media(item.media_id),
        )
    if len(would_download) > _PREVIEW_LOG_LIMIT:
        logger.info(
            f"Preview: and {len(would_download) - _PREVIEW_LOG_LIMIT} more."
            " The pending downloads view lists them all."
        )
    msg = (
        f"Preview mode: {summary.pending_pairs} trailer(s) across"
        f" {summary.total_media} media item(s) would be downloaded"
        f" ({summary.backoff_pairs} backing off). Enable downloads in"
        " settings to perform them."
    )
    logger.info(msg)
    await ws_manager.broadcast(msg, "Info", reload="none")


async def download_missing_trailers(
    _stop_event: threading.Event | None = None,
) -> None:
    """Download missing trailers for monitored media items.

    Phase 2 engine: downloads are decided per profile from download records
    (see services/satisfaction.py), never from the legacy mirror
    flags (removed in Phase 5). Failed downloads back off exponentially per (media, profile).
    """
    # Exit if monitoring is disabled
    if not app_settings.monitor_enabled:
        logger.warning(
            "Monitoring is off. Trailarr does not download any trailer."
        )
        return

    # Upgrade guard: required startup passes (attribution, full-scan check)
    # must have completed on this database before downloads may run —
    # protects version-skipping upgrades from mass re-downloads.
    if not downloads_ready():
        logger.warning(
            "The startup passes are not complete. Trailarr does not download"
            " now. It downloads after the passes finish."
        )
        return

    # Preview mode (Phase 3): compute and publish what this run WOULD do,
    # download nothing. Gates ONLY the scheduled downloads — scans, syncs
    # and attribution keep running, and manual downloads still work.
    if not app_settings.downloads_enabled:
        await _run_preview_pass()
        return

    # Defensive: no in-flight entries can survive between runs (the registry
    # is process-local and download_trailer cleans up in finally), but a
    # fresh task run must never start with a stale overlay.
    inflight_registry.clear()

    # Prune attempt rows for profiles that no longer exist (lazy cleanup)
    all_profiles = trailerprofile.get_trailerprofiles()
    valid_ids = {p.id for p in all_profiles if p.id is not None}
    pruned = attempt_manager.prune_for_missing_profiles(valid_ids)
    if pruned:
        logger.info(
            f"Trailarr removed {pruned} download attempt records. Their"
            " profiles no longer exist."
        )

    scanned_media = 0
    attempted_downloads = 0
    successful_downloads = 0
    skipped_items = 0
    attempted_pairs: set[tuple[int, int]] = set()

    while True:
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Trailarr stopped the download of the missing trailers. A stop"
                " was requested."
            )
            return

        trailer_profiles = trailerprofile.get_trailerprofiles()

        if not trailer_profiles:
            logger.warning(
                "There are no trailer profiles. Trailarr does not download any"
                " trailer."
            )
            return

        enabled_profiles = [p for p in trailer_profiles if p.enabled]

        if not enabled_profiles:
            logger.warning(
                "No trailer profile is enabled. Trailarr does not download any"
                " trailer."
            )
            return

        # All profiles (incl. disabled) — used for claim logging; download
        # ownership is about identity, not activity: a disabled profile's
        # downloads still satisfy it.
        profiles_by_id = {
            p.id: p for p in trailer_profiles if p.id is not None
        }
        work_items, sweep_scanned = _build_work_list(
            attempted_pairs,
            enabled_profiles,
            profiles_by_id,
            _stop_event=_stop_event,
        )
        scanned_media += sweep_scanned
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Stop event set, terminating download of missing trailers."
            )
            return
        if not work_items:
            logger.info("There are no more media items to examine.")
            break

        for work_item in work_items:
            if _stop_event and _stop_event.is_set():
                logger.info(
                    "Trailarr stopped the download of the missing trailers. A stop"
                    " was requested."
                )
                return

            proposed_pairs = {
                (work_item.media_id, profile_id)
                for profile_id in work_item.profile_ids
            }
            attempted_pairs.update(proposed_pairs)

            try:
                media, current_profiles = _read_current_eligible_profiles(
                    work_item.media_id
                )
            except ItemNotFoundError:
                skipped_items += len(work_item.profile_ids)
                logger.info(
                    "Trailarr skipped a media item. It is no longer in the"
                    " database.",
                    **logger.media(work_item.media_id),
                )
                continue
            except Exception:
                skipped_items += len(work_item.profile_ids)
                logger.exception(
                    "Trailarr could not re-check a media item before its"
                    " download.",
                    **logger.media(work_item.media_id),
                )
                continue

            current_profile_ids = {
                profile.id
                for profile in current_profiles
                if profile.id is not None
            }
            skipped_items += len(
                work_item.profile_ids.difference(current_profile_ids)
            )
            profiles_to_process = [
                profile
                for profile in current_profiles
                if profile.id is not None
                and (
                    profile.id in work_item.profile_ids
                    or (media.id, profile.id) not in attempted_pairs
                )
            ]
            attempted_pairs.update(
                (media.id, profile.id)
                for profile in profiles_to_process
                if profile.id is not None
            )
            if not profiles_to_process:
                continue

            # One call for the whole media item, with every profile it still
            # needs. Calling once per profile would re-run the folder and
            # storage checks — and their skip events — once per profile.
            try:
                downloads, skips, attempts = await _process_single_media_item(
                    media,
                    profiles_to_process,
                    attempted_downloads,
                    _stop_event=_stop_event,
                )
                successful_downloads += downloads
                skipped_items += skips
                attempted_downloads += attempts
            except Exception:
                logger.exception(
                    f"Trailarr could not process media '{media.title}'.",
                    **logger.media(media.id),
                )

    logger.info(
        "Trailarr finished the missing-trailer task. It scanned"
        f" {scanned_media} media rows, attempted {attempted_downloads}"
        f" downloads, downloaded {successful_downloads} trailers, and"
        f" skipped {skipped_items} profile items."
    )


async def _process_single_media_item(
    media: MediaRead,
    profiles: list[TrailerProfileRead],
    total_processed: int = 0,
    _stop_event: threading.Event | None = None,
) -> tuple[int, int, int]:
    """Download trailers for a media item's unsatisfied, backoff-eligible
    profiles. Successes clear the attempt record; hard failures record one.

    Returns the number of successful downloads, the number of skipped
    profiles, and the number of profiles a download was really attempted
    for. Only that last count advances the delay ladder — a validation skip
    never reaches the network, so it must not push the next real download
    further away."""
    logger.info(
        f"Trailarr examines '{media.title}' for trailer downloads.",
        **logger.media(media.id),
    )
    successful_downloads = 0
    skipped_items = 0
    download_attempts = 0

    for profile in profiles:
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Trailarr stopped work on this media item. A stop was requested."
            )
            return successful_downloads, skipped_items, download_attempts

        check_folder = profile.custom_folder == "{media_folder}"
        if not _is_valid_media(media, check_folder):
            # Validation skips are NOT failed attempts — no backoff recorded
            return (
                successful_downloads,
                skipped_items + 1,
                download_attempts,
            )

        _profile_name = profile.customfilter.filter_name
        download_attempted = False
        try:
            logger.info(
                f"Trailarr downloads a trailer for '{media.title}' with the"
                f" profile '{_profile_name}'.",
                **logger.media(media.id),
            )
            download_successful = await trailer_downloader.download_trailer(
                media, profile, profile.retry_count, _stop_event=_stop_event
            )
            if download_successful:
                download_attempted = True
                successful_downloads += 1
                # (attempt record cleared inside download_trailer on success)
                # Phase 4: profiles no longer stop monitoring on success —
                # every unsatisfied matching profile gets its download.
        except (DownloadFailedError, Exception) as e:
            download_attempted = True
            attempt = attempt_manager.record_failure(
                media.id, profile.id, str(e) or type(e).__name__
            )
            logger.warning(
                f"Trailarr could not download a trailer for '{media.title}' with"
                f" the profile '{_profile_name}'. Attempt"
                f" {attempt.attempt_count}.",
                **logger.media(media.id),
            )
            skipped_items += 1
        finally:
            # Count only a real attempt. `download_trailer` returns False
            # without touching the network when Plex already holds the
            # trailer (`skip_if_plex_trailer`) or when the stop event is
            # set. Those must not report a download, and must not advance
            # the delay ladder — the ladder paces network requests, and
            # a skip makes none.
            if download_attempted:
                total_processed += 1
                download_attempts += 1
                await utils.sleep_between_downloads(total_processed, logger)

    _profile_count = len(profiles)
    _msg = f"Trailarr finished the work on '{media.title}'."
    _msg += f" Downloads: {successful_downloads}/{_profile_count}"
    _msg += f", Skipped: {skipped_items}/{_profile_count}"
    logger.info(_msg)
    return successful_downloads, skipped_items, download_attempts
