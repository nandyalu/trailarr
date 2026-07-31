from collections import defaultdict

from app_logger import ModuleLogger
import core.base.database.manager.download as download_manager
import core.base.database.manager.media as media_manager
import core.base.database.manager.trailerprofile as trailerprofile_manager
from core.base.database.models.download import DownloadRead
from core.base.utils.profiles import find_matching_profiles

logger = ModuleLogger("DownloadAttribution")


async def attribute_unattributed_downloads() -> None:
    """Attribute active downloads recorded without a profile (profile_id=0)
    to the user's trailer profiles.

    For each media item with unattributed downloads, profiles matching the
    media are considered in priority order (ignoring filter conditions on
    download-state fields — see STATE_FILTER_FIELDS). Each
    unattributed download (oldest first) is assigned the next matching
    profile that doesn't already own an active download for that media.
    Downloads with no matching profile left to claim them stay at
    profile_id=0 and can be picked up by a later run (e.g. after the user
    adds a profile that matches).
    """
    unattributed = download_manager.read_unattributed()
    if not unattributed:
        logger.info("No unattributed trailer downloads found.")
        return

    profiles = trailerprofile_manager.get_trailerprofiles()
    if not profiles:
        logger.warning(
            f"Found {len(unattributed)} unattributed trailer download(s),"
            " but no trailer profiles exist to claim them."
        )
        return

    downloads_by_media: dict[int, list[DownloadRead]] = defaultdict(list)
    for download in unattributed:
        downloads_by_media[download.media_id].append(download)

    claimed_count = 0
    unclaimed_count = 0
    for media_id, downloads in downloads_by_media.items():
        try:
            media = media_manager.read(media_id)
        except Exception as e:
            logger.warning(
                f"Skipping attribution for media [{media_id}]: {e}"
            )
            unclaimed_count += len(downloads)
            continue

        used_profile_ids = {
            d.profile_id
            for d in media.downloads
            if d.file_exists and d.profile_id
        }
        matching_profiles = find_matching_profiles(
            media, profiles, ignore_state_filters=True
        )
        available_profiles = [
            p for p in matching_profiles if p.id not in used_profile_ids
        ]
        # Downloads are ordered oldest first; assign matching profiles in
        # priority order so the oldest download gets the highest priority.
        for download in downloads:
            if not available_profiles:
                unclaimed_count += 1
                # The two causes need different fixes, so name them apart:
                # no matching profile → adjust profile filters; all matching
                # profiles taken → extra/duplicate trailer file for media.
                if matching_profiles:
                    reason = (
                        "all matching profiles already have a download"
                        " (extra trailer file?)"
                    )
                else:
                    reason = "no profile filters match this media"
                logger.info(
                    f"Download '{download.file_name}' of '{media.title}'"
                    f" [{media_id}] left unattributed: {reason}. Assign a"
                    " profile manually from Media Details if needed."
                )
                continue
            profile = available_profiles.pop(0)
            download_manager.update_profile_id(download.id, profile.id)
            claimed_count += 1
            logger.info(
                f"Attributed download '{download.file_name}' of"
                f" '{media.title}' [{media_id}] to profile"
                f" '{profile.customfilter.filter_name}' [{profile.id}]"
            )

    logger.info(
        f"Download attribution complete: {claimed_count} download(s)"
        f" attributed, {unclaimed_count} left unattributed (see log lines"
        " above for per-download reasons)."
    )


def count_tracked_media() -> tuple[int, int]:
    """Count media that have at least one active download record.

    Returns (tracked_count, media_count). Phase 5 removed the stored
    mirror flags, so download rows are the only measure of
    downloaded-ness — this is telemetry, not a gate.
    """
    tracked_count = 0
    media_count = 0
    for media in media_manager.read_all_generator():
        media_count += 1
        if any(d.file_exists for d in media.downloads):
            tracked_count += 1
    return tracked_count, media_count


async def run_attribution_pass() -> None:
    """Run the download attribution pass.

    Phase 3 removed the mirror-flag fixup step that used to chain
    here; Phase 5 removed the mirror columns themselves, and with them the
    mirror-vs-downloads health report — download rows are the only record
    of downloaded-ness now.
    """
    await attribute_unattributed_downloads()
