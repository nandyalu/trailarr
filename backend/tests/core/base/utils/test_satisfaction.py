"""Table-driven tests for the Phase-2 satisfaction rule
(plans/phase-02-downloads-engine.md wargame scenarios S1-S12)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from core.base.utils.satisfaction import evaluate_satisfaction

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
    profile_id: int, priority: int = 100, stop_monitoring: bool = False
) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id, priority=priority, stop_monitoring=stop_monitoring
    )


def make_media(downloads: list) -> SimpleNamespace:
    return SimpleNamespace(id=1, title="Test", downloads=downloads)


def by_id(*profiles) -> dict:
    return {p.id: p for p in profiles}


class TestSatisfaction:

    def test_s1_all_satisfied_nothing_pending(self):
        p1, p2 = make_profile(1), make_profile(2)
        media = make_media([make_download(1, 1), make_download(2, 2)])
        result = evaluate_satisfaction(media, [p1, p2], by_id(p1, p2))
        assert result.unsatisfied == []
        assert result.claims == []
        assert not result.fully_satisfied_by_stop_monitoring

    def test_s2_monitored_forever_never_redownloads(self):
        """Satisfied media stays satisfied on every run — idempotency core."""
        p1 = make_profile(1)
        media = make_media([make_download(1, 1)])
        for _ in range(3):
            result = evaluate_satisfaction(media, [p1], by_id(p1))
            assert result.unsatisfied == []

    def test_s3_deleted_file_makes_profile_pending_again(self):
        p1 = make_profile(1)
        media = make_media([make_download(1, 1, file_exists=False)])
        result = evaluate_satisfaction(media, [p1], by_id(p1))
        assert result.unsatisfied == [p1]

    def test_s4_unattributed_claimed_not_downloaded(self):
        p1 = make_profile(1)
        media = make_media([make_download(7, 0)])
        result = evaluate_satisfaction(media, [p1], by_id(p1))
        assert result.unsatisfied == []
        assert result.claims == [(7, 1)]

    def test_s4b_two_profiles_one_unattributed(self):
        """Highest priority claims the file; the other downloads."""
        high = make_profile(1, priority=10)
        low = make_profile(2, priority=500)
        media = make_media([make_download(7, 0)])
        result = evaluate_satisfaction(media, [low, high], by_id(high, low))
        assert result.claims == [(7, 1)]
        assert result.unsatisfied == [low]

    def test_s4c_oldest_unattributed_claimed_first(self):
        p1 = make_profile(1, priority=10)
        p2 = make_profile(2, priority=20)
        older = make_download(8, 0, age_hours=48)
        newer = make_download(9, 0, age_hours=1)
        media = make_media([newer, older])
        result = evaluate_satisfaction(media, [p1, p2], by_id(p1, p2))
        assert result.claims == [(8, 1), (9, 2)]

    def test_s5_dead_profile_downloads_satisfy_nothing(self):
        """Download owned by a deleted profile: doesn't satisfy the living
        profile, and (owner unknown) can't trigger the stop_monitoring
        carve-out. It is NOT claimable either (it's attributed)."""
        p2 = make_profile(2)
        media = make_media([make_download(1, profile_id=99)])
        result = evaluate_satisfaction(media, [p2], by_id(p2))
        assert result.unsatisfied == [p2]
        assert result.claims == []

    def test_s10_stop_monitoring_download_fully_satisfies(self):
        """Legacy volume preserved: any active download owned by a
        stop_monitoring profile ends all pending work for the media."""
        stopper = make_profile(1, stop_monitoring=True)
        other = make_profile(2)
        media = make_media([make_download(1, 1)])
        result = evaluate_satisfaction(
            media, [stopper, other], by_id(stopper, other)
        )
        assert result.fully_satisfied_by_stop_monitoring
        assert result.unsatisfied == []

    def test_s10b_stop_monitoring_false_gets_one_per_profile(self):
        multi1 = make_profile(1, stop_monitoring=False)
        multi2 = make_profile(2, stop_monitoring=False)
        media = make_media([make_download(1, 1)])
        result = evaluate_satisfaction(
            media, [multi1, multi2], by_id(multi1, multi2)
        )
        assert result.unsatisfied == [multi2]

    def test_s10c_carveout_applies_even_if_owner_no_longer_matches(self):
        """Owner profile exists but is not in matching_profiles (filters
        changed) — its stop_monitoring download still fully satisfies."""
        stopper = make_profile(1, stop_monitoring=True)
        other = make_profile(2)
        media = make_media([make_download(1, 1)])
        result = evaluate_satisfaction(media, [other], by_id(stopper, other))
        assert result.fully_satisfied_by_stop_monitoring

    def test_s12_duplicate_downloads_same_profile(self):
        """Historical duplicates (multiple rows, same profile) — satisfied,
        no assumption of uniqueness."""
        p1 = make_profile(1)
        media = make_media([make_download(1, 1), make_download(2, 1)])
        result = evaluate_satisfaction(media, [p1], by_id(p1))
        assert result.unsatisfied == []

    def test_deleted_files_never_claimable(self):
        p1 = make_profile(1)
        media = make_media([make_download(1, 0, file_exists=False)])
        result = evaluate_satisfaction(media, [p1], by_id(p1))
        assert result.claims == []
        assert result.unsatisfied == [p1]

    def test_no_matching_profiles(self):
        media = make_media([make_download(1, 0)])
        result = evaluate_satisfaction(media, [], {})
        assert result.unsatisfied == []
        assert result.claims == []
