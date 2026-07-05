"""Tests for core/base/utils/profiles.py — profile matching and
download-ownership picking."""

from types import SimpleNamespace

from core.base.database.models.filter import FilterCondition, FilterRead
from core.base.utils.profiles import (
    find_matching_profiles,
    pick_profile_for_download,
)


def make_filter(
    filter_by: str, filter_value: str, filter_id: int = 1
) -> FilterRead:
    return FilterRead(
        id=filter_id,
        customfilter_id=1,
        filter_by=filter_by,
        filter_condition=FilterCondition.EQUALS,
        filter_value=filter_value,
    )


def make_profile(
    profile_id: int, priority: int = 100, filters: list | None = None
) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=priority,
        customfilter=SimpleNamespace(
            filter_name=f"Profile {profile_id}",
            filters=filters if filters is not None else [],
        ),
    )


def make_media(
    is_movie: bool = True, trailer_exists: bool = False, monitor: bool = False
) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        title="Test Movie",
        is_movie=is_movie,
        trailer_exists=trailer_exists,
        monitor=monitor,
    )


class TestFindMatchingProfiles:
    def test_empty_filters_match_all(self):
        profiles = [make_profile(1)]
        assert find_matching_profiles(make_media(), profiles) == profiles

    def test_non_matching_filter_excludes_profile(self):
        profiles = [make_profile(1, filters=[make_filter("is_movie", "true")])]
        media = make_media(is_movie=False)
        assert find_matching_profiles(media, profiles) == []

    def test_sorted_by_priority_lower_first(self):
        low = make_profile(1, priority=500)
        high = make_profile(2, priority=10)
        assert find_matching_profiles(make_media(), [low, high]) == [high, low]

    def test_state_filter_blocks_match_by_default(self):
        """A trailer_exists=false filter (as shipped in the default profiles)
        excludes media that already has a trailer."""
        profiles = [
            make_profile(1, filters=[make_filter("trailer_exists", "false")])
        ]
        media = make_media(trailer_exists=True)
        assert find_matching_profiles(media, profiles) == []

    def test_ignore_state_filters_skips_trailer_exists_condition(self):
        """With ignore_state_filters=True, download-state conditions are
        skipped while media-identity conditions still apply."""
        profiles = [
            make_profile(
                1,
                filters=[
                    make_filter("trailer_exists", "false"),
                    make_filter("is_movie", "true", filter_id=2),
                ],
            )
        ]
        movie = make_media(is_movie=True, trailer_exists=True)
        series = make_media(is_movie=False, trailer_exists=True)
        assert (
            find_matching_profiles(movie, profiles, ignore_state_filters=True)
            == profiles
        )
        assert (
            find_matching_profiles(series, profiles, ignore_state_filters=True)
            == []
        )

    def test_ignore_state_filters_skips_monitor_condition(self):
        profiles = [make_profile(1, filters=[make_filter("monitor", "true")])]
        media = make_media(monitor=False)
        assert find_matching_profiles(media, profiles) == []
        assert (
            find_matching_profiles(media, profiles, ignore_state_filters=True)
            == profiles
        )


class TestPickProfileForDownload:
    def test_picks_highest_priority_matching_profile(self):
        profiles = [make_profile(1, priority=500), make_profile(2, priority=10)]
        assert pick_profile_for_download(make_media(), profiles, set()) == 2

    def test_skips_profiles_already_owning_a_download(self):
        profiles = [make_profile(1, priority=10), make_profile(2, priority=500)]
        assert pick_profile_for_download(make_media(), profiles, {1}) == 2

    def test_returns_zero_when_all_matching_profiles_used(self):
        profiles = [make_profile(1), make_profile(2)]
        assert pick_profile_for_download(make_media(), profiles, {1, 2}) == 0

    def test_returns_zero_when_nothing_matches(self):
        profiles = [make_profile(1, filters=[make_filter("is_movie", "true")])]
        media = make_media(is_movie=False)
        assert pick_profile_for_download(media, profiles, set()) == 0

    def test_ignores_state_filters_when_picking(self):
        """Ownership picking must treat 'trailer_exists=false' profiles as
        matching — the trailer existing is exactly why we're attributing."""
        profiles = [
            make_profile(1, filters=[make_filter("trailer_exists", "false")])
        ]
        media = make_media(trailer_exists=True)
        assert pick_profile_for_download(media, profiles, set()) == 1
