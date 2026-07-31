from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.base.utils.filters import matches_filters

# Media fields that change with download state rather than describing which
# media a profile is for. Filters on these fields say "when to download",
# not "which media this profile is for" — so they must be ignored when
# deciding which profile should own a trailer that already exists on disk.
# (Phase 5 removed the stored mirror columns; has_downloads is their
# virtual successor for view filters and is state by definition.)
STATE_FILTER_FIELDS = {"monitor", "has_downloads"}


def find_matching_profiles(
    media: MediaRead,
    profiles: list[TrailerProfileRead],
    ignore_state_filters: bool = False,
) -> list[TrailerProfileRead]:
    """Find all profiles whose filters match a media item.\n
    Args:
        media (MediaRead): The media item to match against.
        profiles (list[TrailerProfileRead]): Profiles to consider.
        ignore_state_filters (bool): Skip filter conditions on download-state
            fields (see STATE_FILTER_FIELDS). Use when attributing existing
            downloads to profiles, where those conditions are meaningless.\n
    Returns:
        list[TrailerProfileRead]: Matching profiles sorted by priority
            (lower number = higher priority)."""
    matching_profiles = []
    for profile in profiles:
        filters = profile.customfilter.filters
        if ignore_state_filters:
            filters = [
                f for f in filters if f.filter_by not in STATE_FILTER_FIELDS
            ]
        if matches_filters(media, filters):
            matching_profiles.append(profile)

    matching_profiles.sort(key=lambda p: p.priority)
    return matching_profiles


def pick_profile_for_download(
    media: MediaRead,
    profiles: list[TrailerProfileRead],
    used_profile_ids: set[int],
) -> int:
    """Pick the profile that should own a trailer download found on disk.\n
    Args:
        media (MediaRead): The media item the trailer belongs to.
        profiles (list[TrailerProfileRead]): All profiles to consider.
        used_profile_ids (set[int]): Profile ids that already own an active
            download for this media item.\n
    Returns:
        int: Id of the highest-priority matching profile that doesn't already
            own a download, or 0 if no matching profile is available."""
    matching = find_matching_profiles(media, profiles, ignore_state_filters=True)
    for profile in matching:
        if profile.id not in used_profile_ids:
            return profile.id
    return 0
