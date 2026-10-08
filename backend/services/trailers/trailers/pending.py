"""Pending-downloads reconciliation view (Phase 3, design decision 3).

THE single source of truth shared by the download task and the UI: which
profiles match a media item, which are satisfied by which download, which
are pending, and which are backing off. It reuses the exact Phase-2
satisfaction helper (services/satisfaction.py) — never a parallel
reimplementation — and performs no writes: claims the task would apply are
reported as satisfied-via-claim, not persisted.
"""

from collections.abc import Iterator
from datetime import datetime

from pydantic import BaseModel

import database.manager.downloadattempt as attempt_manager
import database.manager.media as media_manager
import database.manager.mediavideo as video_manager
from database.manager import trailerprofile
from database.models.downloadattempt import (
    DownloadAttemptRead,
    is_eligible,
    next_eligible_at,
)
from database.models.media import MediaRead
from database.models.mediavideo import MediaVideoRead
from database.models.trailerprofile import TrailerProfileRead
from exceptions import ItemNotFoundError
from services.profiles import find_matching_profiles
from services.satisfaction import (
    SatisfactionResult,
    UpgradeState,
    evaluate_satisfaction,
    needs_videos,
)


class MediaPendingProfile(BaseModel):
    """One row of the per-media profile matrix."""

    profile_id: int
    profile_name: str
    enabled: bool
    matches: bool
    satisfied: bool
    satisfied_by: int | None  # download id
    satisfied_via: str | None  # "own_download" | "claim"
    pending: bool
    # Pending only because `Upgrade To TMDB Trailer` replaces the trailer.
    upgrade: bool = False
    # Why the upgrade replaces the trailer, or why it keeps it. None when
    # the upgrade is off or inert.
    upgrade_state: UpgradeState | None = None
    backing_off: bool
    attempt_count: int
    last_error: str | None
    next_eligible_at: datetime | None


class MediaPendingView(BaseModel):
    media_id: int
    monitor: bool
    # Whether the item has a TMDB id, and whether Trailarr has asked TMDB
    # about it. An upgrade that waits for TMDB reads differently in each
    # case, and the page says which.
    has_tmdb_id: bool = True
    tmdb_asked: bool = True
    profiles: list[MediaPendingProfile]


class PendingSummaryItem(BaseModel):
    """One (media, profile) pair the download task would act on."""

    media_id: int
    title: str
    is_movie: bool
    profile_id: int
    profile_name: str
    reason: str  # "pending" | "backoff"
    # A profile that waits for TMDB (W3: no known video suits it, and it
    # cannot search) is not in the list: the download task does not act
    # on it. `media_awaiting_tmdb` feeds those to the refresh task.
    # The trailer is on disk, and the download replaces it with a TMDB one.
    upgrade: bool = False
    # Why the download replaces the trailer, when it does.
    upgrade_state: UpgradeState | None = None
    next_eligible_at: datetime | None


class PendingSummary(BaseModel):
    """Library-wide preview of the download task's work list."""

    total_media: int
    pending_pairs: int
    backoff_pairs: int
    items: list[PendingSummaryItem]
    limit: int
    offset: int


def _profile_name(profile: TrailerProfileRead) -> str:
    return profile.customfilter.filter_name


def read_known_videos(
    profiles: list[TrailerProfileRead],
) -> dict[int, list[MediaVideoRead]]:
    """The known videos per media id, for a library-wide pass.

    Only a profile with `Upgrade To TMDB Trailer` on, or with `Search
    YouTube` off, reads them (`needs_videos`), so a library with no such
    profile makes no query at all.
    """
    if not needs_videos(profiles):
        return {}
    return video_manager.read_candidates_by_media()


def compute_media_pending(
    media: MediaRead,
    all_profiles: list[TrailerProfileRead],
    attempts: dict[int, DownloadAttemptRead] | None = None,
) -> MediaPendingView:
    """Build the per-profile matrix for one media item.

    Every profile gets a row (the matrix shows non-matching and disabled
    profiles too); engine truth (satisfied/pending) comes from the same
    evaluate_satisfaction call the download task makes.
    """
    if attempts is None:
        attempts = {
            a.profile_id: a for a in attempt_manager.read_for_media(media.id)
        }
    enabled_profiles = [p for p in all_profiles if p.enabled]

    # `matches` is display info for ALL profiles; the engine run below only
    # considers enabled ones (identical to the download task).
    matching_ids = {p.id for p in find_matching_profiles(media, all_profiles)}
    matching_enabled = find_matching_profiles(media, enabled_profiles)
    videos = None
    if needs_videos(matching_enabled):
        videos = video_manager.read_candidates(media.id, video_type=None)
    result = evaluate_satisfaction(media, matching_enabled, videos)
    details_by_id = {d.profile_id: d for d in result.details}
    unsatisfied_ids = {p.id for p in result.unsatisfied}

    # Downloads owned outside the engine run (disabled/non-matching
    # profiles) still show as satisfied-by-own-download in the matrix.
    own_download_ids: dict[int, int] = {}
    for download in media.downloads:
        if download.file_exists and download.profile_id:
            own_download_ids.setdefault(download.profile_id, download.id)

    rows: list[MediaPendingProfile] = []
    for profile in sorted(all_profiles, key=lambda p: p.priority):
        detail = details_by_id.get(profile.id)
        upgrade = False
        upgrade_state = None
        if detail is not None:
            satisfied = detail.satisfied
            satisfied_by = detail.satisfied_by
            satisfied_via = detail.via
            upgrade = detail.upgrade
            upgrade_state = detail.upgrade_state
        else:
            satisfied_by = own_download_ids.get(profile.id)
            satisfied = satisfied_by is not None
            satisfied_via = "own_download" if satisfied else None
        pending = profile.id in unsatisfied_ids
        attempt = attempts.get(profile.id)
        backing_off = (
            pending and attempt is not None and not is_eligible(attempt)
        )
        rows.append(
            MediaPendingProfile(
                profile_id=profile.id,
                profile_name=_profile_name(profile),
                enabled=profile.enabled,
                matches=profile.id in matching_ids,
                satisfied=satisfied,
                satisfied_by=satisfied_by,
                satisfied_via=satisfied_via,
                pending=pending,
                upgrade=upgrade,
                upgrade_state=upgrade_state,
                backing_off=backing_off,
                attempt_count=attempt.attempt_count if attempt else 0,
                last_error=attempt.last_error if attempt else None,
                next_eligible_at=(
                    next_eligible_at(attempt) if attempt else None
                ),
            )
        )
    return MediaPendingView(
        media_id=media.id,
        monitor=media.monitor,
        has_tmdb_id=bool(media.tmdb_id),
        tmdb_asked=media.last_videos_refresh is not None,
        profiles=rows,
    )


def compute_library_pending(
    limit: int = 100, offset: int = 0
) -> PendingSummary:
    """Library-wide pending view — exactly the download task's work list
    (monitored media, enabled profiles, satisfaction, backoff), computed
    without writes. Powers preview mode and the summary endpoint (W8)."""
    offset = max(0, offset)
    limit = max(1, min(limit, 1000))
    all_profiles = trailerprofile.get_trailerprofiles()
    enabled_profiles = [p for p in all_profiles if p.enabled]

    items: list[PendingSummaryItem] = []
    pending_media_ids: set[int] = set()
    pending_pairs = 0
    backoff_pairs = 0

    if enabled_profiles:
        # One query for every attempt row — the loop below must not issue
        # per-media attempt queries (W8: interactive on 1,700+ items).
        attempts_by_key = {
            (a.media_id, a.profile_id): a for a in attempt_manager.read_all()
        }
        for media, result in _evaluate_library(enabled_profiles):
            # A profile that waits for TMDB is not work: the download task
            # skips it without an attempt, so it is not counted either.
            waiting = {
                d.profile_id
                for d in result.details
                if d.awaiting_tmdb and not d.satisfied
            }
            to_act = [p for p in result.unsatisfied if p.id not in waiting]
            if not to_act:
                continue
            pending_media_ids.add(media.id)
            upgrades = {d.profile_id for d in result.details if d.upgrade}
            states = {d.profile_id: d.upgrade_state for d in result.details}
            for profile in to_act:
                attempt = attempts_by_key.get((media.id, profile.id))
                eligible = is_eligible(attempt)
                if eligible:
                    pending_pairs += 1
                else:
                    backoff_pairs += 1
                items.append(
                    PendingSummaryItem(
                        media_id=media.id,
                        title=media.title,
                        is_movie=media.is_movie,
                        profile_id=profile.id,
                        profile_name=_profile_name(profile),
                        reason="pending" if eligible else "backoff",
                        upgrade=profile.id in upgrades,
                        upgrade_state=states.get(profile.id),
                        next_eligible_at=(
                            next_eligible_at(attempt) if attempt else None
                        ),
                    )
                )

    return PendingSummary(
        total_media=len(pending_media_ids),
        pending_pairs=pending_pairs,
        backoff_pairs=backoff_pairs,
        items=items[offset : offset + limit],
        limit=limit,
        offset=offset,
    )


def media_awaiting_tmdb() -> list[int]:
    """The media items that wait for TMDB to list a video.

    A profile with `Upgrade To TMDB Trailer` keeps its trailer while TMDB
    lists nothing for it, and that includes a media item that Trailarr
    never asked TMDB about. A profile with `Search YouTube` off has
    nothing to download while no known video of its type suits it (W3).
    Neither is in the pending list, so the refresh task asks TMDB about
    these, so that the upgrade or the download can happen at all.

    Returns:
        list[int]: The media ids, in library order.
    """
    enabled_profiles = [
        p for p in trailerprofile.get_trailerprofiles() if p.enabled
    ]
    if not needs_videos(enabled_profiles):
        return []
    return [
        media.id
        for media, result in _evaluate_library(enabled_profiles)
        if any(d.awaiting_tmdb for d in result.details)
    ]


# A (media, profile) pair reaches the library banner after this many failed
# runs. One failure can be a bad day at YouTube. Two runs are at least a day
# apart, so a second failure says the cause did not go away on its own.
FAILING_MIN_ATTEMPTS = 2


class FailingDownload(BaseModel):
    """One (media, profile) pair whose downloads keep failing."""

    media_id: int
    title: str
    is_movie: bool
    profile_id: int
    profile_name: str
    attempt_count: int
    # The reason of the last failure, with the fix when Trailarr knows it.
    last_error: str | None
    next_eligible_at: datetime
    # The trailer is on disk, and the failing download replaces it.
    upgrade: bool = False


def compute_failing_downloads() -> list[FailingDownload]:
    """The downloads that failed on `FAILING_MIN_ATTEMPTS` runs or more.

    The library page shows these in a banner, with a quick filter, so a
    user finds the items to fix without reading the log. Only a pair that
    the download task would still act on counts: an item that was fixed by
    hand, an unmonitored item, or a profile that no longer matches drops
    off. Reads the attempt rows, which exist only while a download keeps
    failing, so this costs one query plus one read per failing item.

    Returns:
        list[FailingDownload]: One row per pair, by title.
    """
    attempts = [
        attempt
        for attempt in attempt_manager.read_all()
        if attempt.attempt_count >= FAILING_MIN_ATTEMPTS
    ]
    if not attempts:
        return []
    enabled_profiles = [
        p for p in trailerprofile.get_trailerprofiles() if p.enabled
    ]
    by_media: dict[int, list[DownloadAttemptRead]] = {}
    for attempt in attempts:
        by_media.setdefault(attempt.media_id, []).append(attempt)

    failing: list[FailingDownload] = []
    for media_id, media_attempts in by_media.items():
        try:
            media = media_manager.read(media_id)
        except ItemNotFoundError:
            # The item is gone. Its attempt rows go with it.
            continue
        if not media.monitor:
            continue
        matching = find_matching_profiles(media, enabled_profiles)
        if not matching:
            continue
        videos = None
        if needs_videos(matching):
            videos = video_manager.read_candidates(media.id, video_type=None)
        result = evaluate_satisfaction(media, matching, videos)
        unsatisfied = {p.id: p for p in result.unsatisfied}
        upgrades = {d.profile_id for d in result.details if d.upgrade}
        for attempt in media_attempts:
            profile = unsatisfied.get(attempt.profile_id)
            if profile is None:
                continue
            failing.append(
                FailingDownload(
                    media_id=media.id,
                    title=media.title,
                    is_movie=media.is_movie,
                    profile_id=attempt.profile_id,
                    profile_name=_profile_name(profile),
                    attempt_count=attempt.attempt_count,
                    last_error=attempt.last_error,
                    next_eligible_at=next_eligible_at(attempt),
                    upgrade=attempt.profile_id in upgrades,
                )
            )
    failing.sort(key=lambda f: (f.title.lower(), f.profile_name.lower()))
    return failing


def _evaluate_library(
    enabled_profiles: list[TrailerProfileRead],
) -> Iterator[tuple[MediaRead, SatisfactionResult]]:
    """Run the satisfaction rule over every monitored media item.

    The same rule, with the same inputs, as the download task. A media
    item that no enabled profile matches is left out.

    When the profiles need the known videos, an item with no rows gets an
    empty list, not None: an empty list is an answer ("TMDB lists
    nothing"), and None would leave the item undecided.
    """
    videos_needed = needs_videos(enabled_profiles)
    videos_by_media = read_known_videos(enabled_profiles)
    for media in media_manager.read_all_generator(monitored_only=True):
        matching = find_matching_profiles(media, enabled_profiles)
        if not matching:
            continue
        videos = videos_by_media.get(media.id, []) if videos_needed else None
        yield media, evaluate_satisfaction(media, matching, videos)
