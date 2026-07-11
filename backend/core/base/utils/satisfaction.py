from dataclasses import dataclass, field

from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead


@dataclass
class SatisfactionResult:
    """Outcome of evaluating which matching profiles still need a download.

    - `unsatisfied`: matching profiles with no active download of their own
      (priority order) — the profiles the download task should act on.
    - `claims`: (download_id, profile_id) pairs where an unattributed active
      download should be attributed to a matching profile instead of
      downloading again. The caller persists these.
    - `fully_satisfied_by_stop_monitoring`: legacy stop_monitoring carve-out
      hit (see below) — media needs nothing regardless of other profiles.
    """

    unsatisfied: list[TrailerProfileRead] = field(default_factory=list)
    claims: list[tuple[int, int]] = field(default_factory=list)
    fully_satisfied_by_stop_monitoring: bool = False


def evaluate_satisfaction(
    media: MediaRead,
    matching_profiles: list[TrailerProfileRead],
    profiles_by_id: dict[int, TrailerProfileRead],
) -> SatisfactionResult:
    """THE Phase-2 rule: a profile is satisfied iff an active
    (file_exists=True) download exists with its profile_id, or an
    unattributed active download can be claimed for it. Downloads — not the
    trailer_exists flag — decide what still needs downloading.

    Legacy carve-out (preserves pre-v0.10 download volume): if ANY active
    download belongs to a profile with stop_monitoring=True, the media is
    fully satisfied — previously that download would have disabled
    monitoring, so the remaining profiles never ran. Users who configured
    stop_monitoring=False (multi-trailer setups) get one download per
    matching profile, exactly as they configured.

    Pure function: no I/O, no writes. `media.downloads` must be loaded.
    """
    active = [d for d in media.downloads if d.file_exists]

    for download in active:
        owner = profiles_by_id.get(download.profile_id)
        if owner is not None and owner.stop_monitoring:
            return SatisfactionResult(fully_satisfied_by_stop_monitoring=True)

    used_profile_ids = {d.profile_id for d in active if d.profile_id}
    unattributed = sorted(
        (d for d in active if d.profile_id == 0),
        key=lambda d: d.added_at,
    )

    result = SatisfactionResult()
    for profile in sorted(matching_profiles, key=lambda p: p.priority):
        if profile.id in used_profile_ids:
            continue  # satisfied by its own download
        if unattributed:
            claimed = unattributed.pop(0)
            result.claims.append((claimed.id, profile.id))
            used_profile_ids.add(profile.id)
            continue  # satisfied by claiming an existing file
        result.unsatisfied.append(profile)
    return result
