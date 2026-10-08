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
        video_type="trailer",
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
        upgrade_to_tmdb=False,
        replace_unknown_videos=False,
        video_type="trailer",
        customfilter=SimpleNamespace(
            filter_name=name or f"Profile {profile_id}",
            filters=filters or [],
        ),
    )


def make_media(
    downloads: list,
    media_id: int = 1,
    monitor: bool = True,
    tmdb_id: int | None = 1,
    tmdb_asked: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=media_id,
        title=f"Media {media_id}",
        is_movie=True,
        monitor=monitor,
        downloads=downloads,
        tmdb_id=tmdb_id,
        last_videos_refresh=NOW if tmdb_asked else None,
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

    def test_the_view_says_whether_tmdb_was_asked(self):
        """An upgrade that waits for TMDB reads differently when the item
        has no TMDB id, when TMDB was not asked yet, and when it listed
        nothing. The page needs both facts to say which."""
        asked = compute_media_pending(make_media([]), [], attempts={})
        assert (asked.has_tmdb_id, asked.tmdb_asked) == (True, True)
        never = compute_media_pending(
            make_media([], tmdb_id=None, tmdb_asked=False), [], attempts={}
        )
        assert (never.has_tmdb_id, never.tmdb_asked) == (False, False)

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
        assert [
            (i.media_id, i.profile_id, i.reason) for i in summary.items
        ] == [(2, 1, "pending")]

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


class TestUpgradeInThePendingView:
    """plans/track-tmdb-upgrade.md: the pending view and the refresh task
    see an upgrade exactly as the download task does."""

    @staticmethod
    def _upgrade_profile():
        profile = make_profile(1)
        profile.upgrade_to_tmdb = True
        profile.always_search = False
        profile.language = ""
        return profile

    @staticmethod
    def _with_trailer(media_id: int, youtube_id: str):
        download = make_download(media_id, 1)
        download.youtube_id = youtube_id
        return make_media([download], media_id=media_id)

    def _run(self, fn, media_list, videos_by_media):
        profile = self._upgrade_profile()
        patches = _patch_managers([profile], media_list)
        with (
            patches[0],
            patches[1],
            patches[2],
            patch(
                "services.trailers.trailers.pending.video_manager"
                ".read_upgrade_candidates_by_media",
                return_value=videos_by_media,
            ),
            patch(
                "services.trailers.resolver.app_settings",
                SimpleNamespace(tmdb_api_key="k"),
            ),
        ):
            return fn()

    def test_a_replacement_is_pending_and_marked(self):
        from services.trailers.trailers.pending import compute_library_pending

        from database.models.mediavideo import VideoSource

        tmdb = [
            SimpleNamespace(
                video_id="tmdb1",
                source=VideoSource.TMDB,
                language="en",
                video_type="trailer",
            )
        ]
        summary = self._run(
            compute_library_pending,
            [
                self._with_trailer(1, "search1"),
                self._with_trailer(2, "tmdb1"),
            ],
            {1: tmdb, 2: tmdb},
        )
        assert [(i.media_id, i.upgrade) for i in summary.items] == [(1, True)]
        assert summary.items[0].upgrade_state == "replace_not_tmdb"

    def test_items_without_a_tmdb_list_await_tmdb(self):
        from services.trailers.trailers.pending import media_awaiting_tmdb

        awaiting = self._run(
            media_awaiting_tmdb,
            [self._with_trailer(1, "search1"), make_media([], media_id=2)],
            {},
        )
        # Item 2 has no trailer: it is a plain download, not an upgrade.
        assert awaiting == [1]

    def test_no_upgrade_profile_reads_no_videos(self):
        from services.trailers.trailers.pending import read_upgrade_videos

        with patch(
            "services.trailers.trailers.pending.video_manager"
            ".read_upgrade_candidates_by_media"
        ) as read:
            assert read_upgrade_videos([make_profile(1)]) == {}
        read.assert_not_called()


class TestFailingDownloads:
    """The library banner: downloads that failed on two runs or more, and
    that the download task would still act on."""

    def _run(self, attempts, media_by_id, profiles=None):
        from exceptions import ItemNotFoundError
        from services.trailers.trailers.pending import (
            compute_failing_downloads,
        )

        def read(media_id):
            if media_id not in media_by_id:
                raise ItemNotFoundError("Media", media_id)
            return media_by_id[media_id]

        with (
            patch(
                "services.trailers.trailers.pending.attempt_manager.read_all",
                return_value=attempts,
            ),
            patch(
                "services.trailers.trailers.pending.trailerprofile"
                ".get_trailerprofiles",
                return_value=profiles or [make_profile(1)],
            ),
            patch(
                "services.trailers.trailers.pending.media_manager.read",
                side_effect=read,
            ),
        ):
            return compute_failing_downloads()

    def test_two_failed_runs_put_an_item_in_the_list(self):
        once = make_attempt(media_id=2, attempt_count=1)
        twice = make_attempt(
            media_id=1, attempt_count=2, last_error="YouTube said no"
        )
        failing = self._run(
            [once, twice],
            {1: make_media([], media_id=1), 2: make_media([], media_id=2)},
        )
        assert [
            (f.media_id, f.attempt_count, f.last_error) for f in failing
        ] == [(1, 2, "YouTube said no")]
        assert failing[0].profile_name == "Profile 1"
        assert failing[0].upgrade is False
        assert failing[0].next_eligible_at > twice.last_attempt_at

    def test_a_fixed_or_unmonitored_item_drops_off(self):
        """The attempt row stays until a download succeeds. The banner
        must not show an item the download task would not act on."""
        fixed = make_media([make_download(5, profile_id=1)], media_id=1)
        unmonitored = make_media([], media_id=2, monitor=False)
        attempts = [
            make_attempt(media_id=1, attempt_count=3),
            make_attempt(media_id=2, attempt_count=3),
        ]
        assert self._run(attempts, {1: fixed, 2: unmonitored}) == []

    def test_a_deleted_item_is_skipped(self):
        assert self._run([make_attempt(media_id=9, attempt_count=2)], {}) == []

    def test_items_come_by_title(self):
        attempts = [
            make_attempt(media_id=1, attempt_count=2),
            make_attempt(media_id=2, attempt_count=2),
        ]
        zed = make_media([], media_id=1)
        zed.title = "Zed"
        abe = make_media([], media_id=2)
        abe.title = "Abe"
        failing = self._run(attempts, {1: zed, 2: abe})
        assert [f.title for f in failing] == ["Abe", "Zed"]
