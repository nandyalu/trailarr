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
    media are considered in priority order (ignoring download-state filter
    conditions like trailer_exists — see STATE_FILTER_FIELDS). Each
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
        available_profiles = [
            p
            for p in find_matching_profiles(
                media, profiles, ignore_state_filters=True
            )
            if p.id not in used_profile_ids
        ]
        # Downloads are ordered oldest first; assign matching profiles in
        # priority order so the oldest download gets the highest priority.
        for download in downloads:
            if not available_profiles:
                unclaimed_count += 1
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
        f" attributed, {unclaimed_count} left unattributed (no matching"
        " profile available)."
    )


async def report_attribution_health() -> None:
    """Log how many media items have trailer_exists=True without any active
    download record backing it.

    These media would be treated as having no trailers once downloads become
    the source of truth for which profiles are satisfied — a non-zero count
    means the files scan hasn't recorded their trailers yet and needs to run
    before downloads can be trusted for download decisions.
    """
    untracked_count = 0
    trailer_exists_count = 0
    for media in media_manager.read_all_generator():
        if not media.trailer_exists:
            continue
        trailer_exists_count += 1
        if not any(d.file_exists for d in media.downloads):
            untracked_count += 1

    if untracked_count:
        logger.warning(
            f"{untracked_count} of {trailer_exists_count} media item(s) with"
            " trailer_exists=True have no tracked download record. Their"
            " trailers should be picked up by the next files scan; if this"
            " count persists across scans, those folders may be unreachable."
        )
    else:
        logger.info(
            f"All {trailer_exists_count} media item(s) with"
            " trailer_exists=True have tracked download records."
        )


async def run_attribution_pass() -> None:
    """Run the download attribution pass, then report attribution health."""
    await attribute_unattributed_downloads()
    await report_attribution_health()
