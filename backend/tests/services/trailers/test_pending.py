"""Phase 3: the pending-downloads reconciliation view
(plans/phase-03-dynamic-status.md, design decision 3) — shared by the
download task and the UI, reusing the exact satisfaction helper."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from services.trailers.trailers.pending import (
    compute_library_pending,
    compute_media_pending,
)

NOW = datetime.now(timezone.utc)


def make_download(
    download_id: int,
    profile_id: int = 0,
    file_exists: bool = True,
    age_hours: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=download_id,
        profile_id=profile_id,
        file_exists=file_exists,
        added_at=NOW - timedelta(hours=age_hours),
    )


def make_profile(
    profile_id: int,
    priority: int = 100,
    enabled: bool = True,
    name: str | None = None,
    filters: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=priority,
        enabled=enabled,
        customfilter=SimpleNamespace(
            filter_name=name or f"Profile {profile_id}",
            filters=filters or [],
        ),
    )


def make_media(
    downloads: list, media_id: int = 1, monitor: bool = True
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        title=f"Media {media_id}",
        is_movie=True,
        monitor=monitor,
        downloads=downloads,
    )


def make_attempt(
    media_id: int = 1,
    profile_id: int = 1,
    attempt_count: int = 1,
    hours_ago: int = 0,
    last_error: str | None = "boom",
) -> SimpleNamespace:
    return SimpleNamespace(
        media_id=media_id,
        profile_id=profile_id,
        attempt_count=attempt_count,
        last_attempt_at=NOW - timedelta(hours=hours_ago),
        last_error=last_error,
    )


class TestComputeMediaPending:

    def test_satisfied_and_pending_rows(self):
        p1 = make_profile(1, priority=10)
        p2 = make_profile(2, priority=20)
        media = make_media([make_download(7, profile_id=1)])
        view = compute_media_pending(media, [p1, p2], attempts={})

        assert view.media_id == 1
        row1, row2 = view.profiles
        assert (row1.profile_id, row1.satisfied, row1.pending) == (
            1,
            True,
            False,
        )
        assert row1.satisfied_by == 7
        assert row1.satisfied_via == "own_download"
        assert (row2.profile_id, row2.satisfied, row2.pending) == (
            2,
            False,
            True,
        )
        assert row2.backing_off is False
        assert row2.attempt_count == 0

    def test_backing_off_row_carries_attempt_info(self):
        p1 = make_profile(1)
        media = make_media([])
        attempt = make_attempt(profile_id=1, attempt_count=2, hours_ago=1)
        view = compute_media_pending(media, [p1], attempts={1: attempt})

        row = view.profiles[0]
        assert row.pending is True
        assert row.backing_off is True  # 2 attempts -> 2d backoff, 1h ago
        assert row.attempt_count == 2
        assert row.last_error == "boom"
        assert row.next_eligible_at is not None

    def test_failed_but_eligible_again_is_not_backing_off(self):
        p1 = make_profile(1)
        media = make_media([])
        # 1 attempt -> 1 day backoff; failed 50 hours ago -> eligible again
        attempt = make_attempt(profile_id=1, attempt_count=1, hours_ago=50)
        view = compute_media_pending(media, [p1], attempts={1: attempt})

        row = view.profiles[0]
        assert row.pending is True
        assert row.backing_off is False
        assert row.attempt_count == 1

    def test_claimable_unattributed_reported_as_satisfied_via_claim(self):
        """The task would claim, not download — the view must agree, while
        performing no writes (pure computation)."""
        p1 = make_profile(1)
        media = make_media([make_download(9, profile_id=0)])
        view = compute_media_pending(media, [p1], attempts={})

        row = view.profiles[0]
        assert row.satisfied is True
        assert row.satisfied_via == "claim"
        assert row.satisfied_by == 9
        assert row.pending is False

    def test_disabled_profile_with_own_download_shown_satisfied(self):
        """Disabled profiles are outside the engine run but their downloads
        still show in the matrix (ownership is identity, not activity)."""
        disabled = make_profile(1, enabled=False)
        media = make_media([make_download(3, profile_id=1)])
        view = compute_media_pending(media, [disabled], attempts={})

        row = view.profiles[0]
        assert row.enabled is False
        assert row.satisfied is True
        assert row.satisfied_by == 3
        assert row.pending is False

    def test_rows_sorted_by_priority(self):
        low = make_profile(1, priority=500)
        high = make_profile(2, priority=10)
        media = make_media([])
        view = compute_media_pending(media, [low, high], attempts={})
        assert [row.profile_id for row in view.profiles] == [2, 1]


def _patch_managers(profiles, media_list, attempts=None):
    return (
        patch(
            "services.trailers.trailers.pending.trailerprofile"
            ".get_trailerprofiles",
            return_value=profiles,
        ),
        patch(
            "services.trailers.trailers.pending.media_manager"
            ".read_all_generator",
            return_value=iter(media_list),
        ),
        patch(
            "services.trailers.trailers.pending.attempt_manager.read_all",
            return_value=attempts or [],
        ),
    )


class TestComputeLibraryPending:

    def test_work_list_matches_engine_semantics(self):
        p1 = make_profile(1)
        satisfied_media = make_media([make_download(1, 1)], media_id=1)
        pending_media = make_media([], media_id=2)
        patches = _patch_managers([p1], [satisfied_media, pending_media])
        with patches[0], patches[1], patches[2]:
            summary = compute_library_pending()

        assert summary.total_media == 1
        assert summary.pending_pairs == 1
        assert summary.backoff_pairs == 0
        assert [(i.media_id, i.profile_id, i.reason) for i in summary.items] \
            == [(2, 1, "pending")]

    def test_backoff_pairs_counted_separately(self):
        p1 = make_profile(1)
        media = make_media([], media_id=2)
        attempt = make_attempt(media_id=2, profile_id=1, attempt_count=3)
        patches = _patch_managers([p1], [media], [attempt])
        with patches[0], patches[1], patches[2]:
            summary = compute_library_pending()

        assert summary.pending_pairs == 0
        assert summary.backoff_pairs == 1
        assert summary.items[0].reason == "backoff"
        assert summary.items[0].next_eligible_at is not None

    def test_no_enabled_profiles_returns_empty(self):
        disabled = make_profile(1, enabled=False)
        patches = _patch_managers([disabled], [])
        with patches[0], patches[1], patches[2]:
            summary = compute_library_pending()
        assert summary.total_media == 0
        assert summary.items == []

    def test_pagination(self):
        p1 = make_profile(1)
        media_list = [make_media([], media_id=i) for i in range(1, 6)]
        patches = _patch_managers([p1], media_list)
        with patches[0], patches[1], patches[2]:
            summary = compute_library_pending(limit=2, offset=2)

        assert summary.total_media == 5  # counts are for the whole library
        assert summary.pending_pairs == 5
        assert [i.media_id for i in summary.items] == [3, 4]
