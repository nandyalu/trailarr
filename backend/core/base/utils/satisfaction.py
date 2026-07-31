from dataclasses import dataclass, field

from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead


@dataclass
class ProfileSatisfaction:
    """Per-profile explanation of the satisfaction decision (Phase 3).

    Built inside the SAME loop as the decision itself, so the pending
    endpoint / details matrix can never disagree with the download task.
    `via` is one of "own_download", "claim" when satisfied; None when the
    profile is unsatisfied (pending).
    """

    profile_id: int
    satisfied: bool
    satisfied_by: int | None = None  # download id
    via: str | None = None


@dataclass
class SatisfactionResult:
    """Outcome of evaluating which matching profiles still need a download.

    - `unsatisfied`: matching profiles with no active download of their own
      (priority order) — the profiles the download task should act on.
    - `claims`: (download_id, profile_id) pairs where an unattributed active
      download should be attributed to a matching profile instead of
      downloading again. The caller persists these.
    - `details`: one ProfileSatisfaction per matching profile (Phase 3) —
      the explanation feed for the pending endpoint.
    """

    unsatisfied: list[TrailerProfileRead] = field(default_factory=list)
    claims: list[tuple[int, int]] = field(default_factory=list)
    details: list[ProfileSatisfaction] = field(default_factory=list)


def evaluate_satisfaction(
    media: MediaRead,
    matching_profiles: list[TrailerProfileRead],
) -> SatisfactionResult:
    """THE Phase-2 rule: a profile is satisfied iff an active
    (file_exists=True) download exists with its profile_id, or an
    unattributed active download can be claimed for it. Downloads — not any
    stored flag — decide what still needs downloading.

    Phase 4 removed the legacy stop-monitoring carve-out: satisfaction is
    purely per-profile ownership now. Users with multiple profiles matching
    the same media get one download per profile — exactly what overlapping
    profiles configure.

    Pure function: no I/O, no writes. `media.downloads` must be loaded.
    """
    active = [d for d in media.downloads if d.file_exists]

    used_profile_ids = {d.profile_id for d in active if d.profile_id}
    own_download_ids = {}
    for download in active:
        if download.profile_id and download.profile_id not in own_download_ids:
            own_download_ids[download.profile_id] = download.id
    unattributed = sorted(
        (d for d in active if d.profile_id == 0),
        key=lambda d: d.added_at,
    )

    result = SatisfactionResult()
    for profile in sorted(matching_profiles, key=lambda p: p.priority):
        if profile.id in used_profile_ids:
            # satisfied by its own download
            result.details.append(
                ProfileSatisfaction(
                    profile_id=profile.id,
                    satisfied=True,
                    satisfied_by=own_download_ids.get(profile.id),
                    via="own_download",
                )
            )
            continue
        if unattributed:
            # satisfied by claiming an existing file
            claimed = unattributed.pop(0)
            result.claims.append((claimed.id, profile.id))
            used_profile_ids.add(profile.id)
            result.details.append(
                ProfileSatisfaction(
                    profile_id=profile.id,
                    satisfied=True,
                    satisfied_by=claimed.id,
                    via="claim",
                )
            )
            continue
        result.unsatisfied.append(profile)
        result.details.append(
            ProfileSatisfaction(profile_id=profile.id, satisfied=False)
        )
    return result
