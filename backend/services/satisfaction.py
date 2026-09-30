"""Decide whether a profile already has the trailer it wants.

A profile is satisfied when a download for it exists and its file is still
on disk. An existing download with no profile can be claimed by a profile
that matches, so Trailarr does not download the same trailer again.

A profile with `Upgrade To TMDB Trailer` on asks one more thing: is one of
its downloads a video that the upgrade accepts? When TMDB lists a trailer
for it and none of its downloads is one, it is not satisfied, and the
download task replaces the trailer (plans/track-tmdb-upgrade.md).
"""

from dataclasses import dataclass, field

from database.models.media import MediaRead
from database.models.mediavideo import MediaVideoRead
from database.models.trailerprofile import TrailerProfileRead
from services.trailers.resolver import upgrade_keeps, upgrade_targets


@dataclass
class ProfileSatisfaction:
    """Per-profile explanation of the satisfaction decision (Phase 3).

    Built inside the SAME loop as the decision itself, so the pending
    endpoint / details matrix can never disagree with the download task.
    `via` is one of "own_download", "claim" when satisfied; None when the
    profile is unsatisfied (pending).

    `upgrade` is True when the profile is unsatisfied only because its
    trailer is not a TMDB trailer and TMDB lists one. `awaiting_tmdb` is
    True when an upgrade profile keeps its trailer because TMDB lists
    nothing for it yet — the refresh task asks TMDB again about these.
    """

    profile_id: int
    satisfied: bool
    satisfied_by: int | None = None  # download id
    via: str | None = None
    upgrade: bool = False
    awaiting_tmdb: bool = False


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
    videos: list[MediaVideoRead] | None = None,
) -> SatisfactionResult:
    """THE Phase-2 rule: a profile is satisfied iff an active
    (file_exists=True) download exists with its profile_id, or an
    unattributed active download can be claimed for it. Downloads — not any
    stored flag — decide what still needs downloading.

    Phase 4 removed the legacy stop-monitoring carve-out: satisfaction is
    purely per-profile ownership now. Users with multiple profiles matching
    the same media get one download per profile — exactly what overlapping
    profiles configure.

    A profile with `Upgrade To TMDB Trailer` on is satisfied only when one
    of its downloads is a video that the upgrade accepts, or when there is
    no such video to upgrade to. `videos` holds the USER and TMDB rows of
    the media item; without them no upgrade can be decided, and the profile
    keeps its trailer.

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
            owned = [d for d in active if d.profile_id == profile.id]
            detail = ProfileSatisfaction(
                profile_id=profile.id,
                satisfied=True,
                satisfied_by=own_download_ids.get(profile.id),
                via="own_download",
            )
            _check_upgrade(detail, profile, owned, videos)
            _add(result, profile, detail)
            continue
        if unattributed:
            # satisfied by claiming an existing file. The claim stands
            # even when the file is then upgraded: it is the file of
            # this profile either way.
            claimed = unattributed.pop(0)
            result.claims.append((claimed.id, profile.id))
            used_profile_ids.add(profile.id)
            detail = ProfileSatisfaction(
                profile_id=profile.id,
                satisfied=True,
                satisfied_by=claimed.id,
                via="claim",
            )
            _check_upgrade(detail, profile, [claimed], videos)
            _add(result, profile, detail)
            continue
        result.unsatisfied.append(profile)
        result.details.append(
            ProfileSatisfaction(profile_id=profile.id, satisfied=False)
        )
    return result


def _check_upgrade(
    detail: ProfileSatisfaction,
    profile: TrailerProfileRead,
    owned: list,
    videos: list[MediaVideoRead] | None,
) -> None:
    """Apply `Upgrade To TMDB Trailer` to a satisfied profile, in place.

    A download whose video the upgrade accepts keeps the profile
    satisfied, and so does a video the user chose, in any language. A
    download with no known video id is not a match: nothing shows that it
    is a TMDB trailer. With no video to upgrade to, the trailer stays, and
    the refresh task asks TMDB about it again.
    """
    if not profile.upgrade_to_tmdb:
        return
    targets = upgrade_targets(videos or [], profile)
    if not targets:
        detail.awaiting_tmdb = True
        return
    kept = upgrade_keeps(videos or [], targets)
    if any(d.youtube_id in kept for d in owned):
        return
    detail.satisfied = False
    detail.satisfied_by = None
    detail.via = None
    detail.upgrade = True


def _add(
    result: SatisfactionResult,
    profile: TrailerProfileRead,
    detail: ProfileSatisfaction,
) -> None:
    """Record a detail, and the profile as unsatisfied when it is."""
    result.details.append(detail)
    if not detail.satisfied:
        result.unsatisfied.append(profile)
