"""Table-driven tests for the satisfaction rule
(plans/phase-02-downloads-engine.md wargame scenarios S1-S12;
ownership is purely per profile)."""

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


def make_profile(profile_id: int, priority: int = 100) -> SimpleNamespace:
    return SimpleNamespace(id=profile_id, priority=priority)


def make_media(downloads: list) -> SimpleNamespace:
    return SimpleNamespace(id=1, title="Test", downloads=downloads)


class TestSatisfaction:

    def test_s1_all_satisfied_nothing_pending(self):
        p1, p2 = make_profile(1), make_profile(2)
        media = make_media([make_download(1, 1), make_download(2, 2)])
        result = evaluate_satisfaction(media, [p1, p2])
        assert result.unsatisfied == []
        assert result.claims == []

    def test_s2_monitored_forever_never_redownloads(self):
        """Satisfied media stays satisfied on every run — idempotency core."""
        p1 = make_profile(1)
        media = make_media([make_download(1, 1)])
        for _ in range(3):
            result = evaluate_satisfaction(media, [p1])
            assert result.unsatisfied == []

    def test_s3_deleted_file_makes_profile_pending_again(self):
        p1 = make_profile(1)
        media = make_media([make_download(1, 1, file_exists=False)])
        result = evaluate_satisfaction(media, [p1])
        assert result.unsatisfied == [p1]

    def test_s4_unattributed_claimed_not_downloaded(self):
        p1 = make_profile(1)
        media = make_media([make_download(7, 0)])
        result = evaluate_satisfaction(media, [p1])
        assert result.unsatisfied == []
        assert result.claims == [(7, 1)]

    def test_s4b_two_profiles_one_unattributed(self):
        """Highest priority claims the file; the other downloads."""
        high = make_profile(1, priority=10)
        low = make_profile(2, priority=500)
        media = make_media([make_download(7, 0)])
        result = evaluate_satisfaction(media, [low, high])
        assert result.claims == [(7, 1)]
        assert result.unsatisfied == [low]

    def test_s4c_oldest_unattributed_claimed_first(self):
        p1 = make_profile(1, priority=10)
        p2 = make_profile(2, priority=20)
        older = make_download(8, 0, age_hours=48)
        newer = make_download(9, 0, age_hours=1)
        media = make_media([newer, older])
        result = evaluate_satisfaction(media, [p1, p2])
        assert result.claims == [(8, 1), (9, 2)]

    def test_s5_dead_profile_downloads_satisfy_nothing(self):
        """Download owned by a deleted profile: doesn't satisfy the living
        profile. It is NOT claimable either (it's attributed)."""
        p2 = make_profile(2)
        media = make_media([make_download(1, profile_id=99)])
        result = evaluate_satisfaction(media, [p2])
        assert result.unsatisfied == [p2]
        assert result.claims == []

    def test_s10_owner_download_satisfies_only_its_profile(self):
        """Each profile is judged on its own downloads — a download owned
        by one profile changes nothing for other matching profiles."""
        owner = make_profile(1)
        other = make_profile(2)
        media = make_media([make_download(1, 1)])
        result = evaluate_satisfaction(media, [owner, other])
        assert result.unsatisfied == [other]

    def test_s10c_non_matching_owner_download_satisfies_nothing(self):
        """A download owned by profile 1 (not in matching_profiles — filters
        changed) — it satisfies only its owner, so the other matching
        profile is pending."""
        other = make_profile(2)
        media = make_media([make_download(1, 1)])
        result = evaluate_satisfaction(media, [other])
        assert result.unsatisfied == [other]

    def test_s12_duplicate_downloads_same_profile(self):
        """Historical duplicates (multiple rows, same profile) — satisfied,
        no assumption of uniqueness."""
        p1 = make_profile(1)
        media = make_media([make_download(1, 1), make_download(2, 1)])
        result = evaluate_satisfaction(media, [p1])
        assert result.unsatisfied == []

    def test_deleted_files_never_claimable(self):
        p1 = make_profile(1)
        media = make_media([make_download(1, 0, file_exists=False)])
        result = evaluate_satisfaction(media, [p1])
        assert result.claims == []
        assert result.unsatisfied == [p1]

    def test_no_matching_profiles(self):
        media = make_media([make_download(1, 0)])
        result = evaluate_satisfaction(media, [])
        assert result.unsatisfied == []
        assert result.claims == []


class TestSatisfactionDetails:
    """Phase 3: per-profile explanations built in the SAME decision loop —
    the pending endpoint feed can never disagree with the download task."""

    def test_own_download_detail(self):
        p1 = make_profile(1)
        media = make_media([make_download(7, 1)])
        result = evaluate_satisfaction(media, [p1])
        detail = result.details[0]
        assert (detail.profile_id, detail.satisfied) == (1, True)
        assert detail.satisfied_by == 7
        assert detail.via == "own_download"

    def test_claim_detail(self):
        p1 = make_profile(1)
        media = make_media([make_download(9, 0)])
        result = evaluate_satisfaction(media, [p1])
        detail = result.details[0]
        assert detail.satisfied
        assert detail.satisfied_by == 9
        assert detail.via == "claim"

    def test_pending_detail(self):
        p1 = make_profile(1)
        media = make_media([])
        result = evaluate_satisfaction(media, [p1])
        detail = result.details[0]
        assert not detail.satisfied
        assert detail.satisfied_by is None
        assert detail.via is None

    def test_owner_detail_does_not_leak_to_other_profiles(self):
        """The owner shows own_download; the other matching profile is
        plainly pending."""
        owner = make_profile(1, priority=10)
        other = make_profile(2, priority=20)
        media = make_media([make_download(5, 1)])
        result = evaluate_satisfaction(media, [owner, other])
        assert [d.profile_id for d in result.details] == [1, 2]
        assert result.details[0].via == "own_download"
        assert result.details[0].satisfied_by == 5
        assert result.details[1].satisfied is False
        assert result.details[1].via is None

    def test_details_cover_every_matching_profile_in_priority_order(self):
        p_own = make_profile(1, priority=10)
        p_claim = make_profile(2, priority=20)
        p_pending = make_profile(3, priority=30)
        media = make_media([make_download(1, 1), make_download(2, 0)])
        result = evaluate_satisfaction(media, [p_pending, p_claim, p_own])
        assert [d.profile_id for d in result.details] == [1, 2, 3]
        assert [d.via for d in result.details] == [
            "own_download",
            "claim",
            None,
        ]
