"""Pending-downloads reconciliation view (Phase 3, design decision 3).

THE single source of truth shared by the download task and the UI: which
profiles match a media item, which are satisfied by which download, which
are pending, and which are backing off. It reuses the exact Phase-2
satisfaction helper (core/base/utils/satisfaction.py) — never a parallel
reimplementation — and performs no writes: claims the task would apply are
reported as satisfied-via-claim, not persisted.
"""

from datetime import datetime

from pydantic import BaseModel

import core.base.database.manager.downloadattempt as attempt_manager
import core.base.database.manager.media as media_manager
from core.base.database.manager import trailerprofile
from core.base.database.models.downloadattempt import (
    DownloadAttemptRead,
    is_eligible,
    next_eligible_at,
)
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.base.utils.profiles import find_matching_profiles
from core.base.utils.satisfaction import evaluate_satisfaction


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
    backing_off: bool
    attempt_count: int
    last_error: str | None
    next_eligible_at: datetime | None


class MediaPendingView(BaseModel):
    media_id: int
    monitor: bool
    profiles: list[MediaPendingProfile]


class PendingSummaryItem(BaseModel):
    """One (media, profile) pair the download task would act on."""

    media_id: int
    title: str
    is_movie: bool
    profile_id: int
    profile_name: str
    reason: str  # "pending" | "backoff"
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
            a.profile_id: a
            for a in attempt_manager.read_for_media(media.id)
        }
    enabled_profiles = [p for p in all_profiles if p.enabled]

    # `matches` is display info for ALL profiles; the engine run below only
    # considers enabled ones (identical to the download task).
    matching_ids = {
        p.id for p in find_matching_profiles(media, all_profiles)
    }
    result = evaluate_satisfaction(
        media, find_matching_profiles(media, enabled_profiles)
    )
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
        if detail is not None:
            satisfied = detail.satisfied
            satisfied_by = detail.satisfied_by
            satisfied_via = detail.via
        else:
            satisfied_by = own_download_ids.get(profile.id)
            satisfied = satisfied_by is not None
            satisfied_via = "own_download" if satisfied else None
        pending = profile.id in unsatisfied_ids
        attempt = attempts.get(profile.id)
        backing_off = pending and attempt is not None and not is_eligible(
            attempt
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
                backing_off=backing_off,
                attempt_count=attempt.attempt_count if attempt else 0,
                last_error=attempt.last_error if attempt else None,
                next_eligible_at=next_eligible_at(attempt)
                if attempt
                else None,
            )
        )
    return MediaPendingView(
        media_id=media.id, monitor=media.monitor, profiles=rows
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
        for media in media_manager.read_all_generator(monitored_only=True):
            matching = find_matching_profiles(media, enabled_profiles)
            if not matching:
                continue
            result = evaluate_satisfaction(media, matching)
            if not result.unsatisfied:
                continue
            pending_media_ids.add(media.id)
            for profile in result.unsatisfied:
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
                        next_eligible_at=next_eligible_at(attempt)
                        if attempt
                        else None,
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
