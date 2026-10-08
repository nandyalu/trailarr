"""Tests for `Upgrade To TMDB Trailer` in the satisfaction rule —
plans/track-tmdb-upgrade.md, decisions 2–6 and 11, wargame W6 and W8."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from database.models.mediavideo import VideoSource
from services.satisfaction import evaluate_satisfaction

NOW = datetime.now(timezone.utc)


def make_download(
    download_id: int,
    profile_id: int,
    youtube_id: str,
    file_exists: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=download_id,
        profile_id=profile_id,
        file_exists=file_exists,
        youtube_id=youtube_id,
        added_at=NOW - timedelta(hours=download_id),
        video_type="trailer",
    )


def make_profile(
    profile_id: int = 1,
    upgrade: bool = True,
    language: str = "",
    always_search: bool = False,
    replace_unknown: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=100,
        upgrade_to_tmdb=upgrade,
        language=language,
        always_search=always_search,
        replace_unknown_videos=replace_unknown,
        video_type="trailer",
    )


def video(
    video_id: str, source: VideoSource = VideoSource.TMDB, language="en"
) -> SimpleNamespace:
    return SimpleNamespace(
        video_id=video_id,
        source=source,
        language=language,
        video_type="trailer",
    )


def make_media(downloads: list) -> SimpleNamespace:
    return SimpleNamespace(id=1, title="Test", downloads=downloads)


TMDB = [video("tmdb1"), video("tmdb2")]


@pytest.fixture(autouse=True)
def _with_a_tmdb_key():
    with patch("services.trailers.resolver.app_settings") as settings:
        settings.tmdb_api_key = "a-key"
        yield settings


class TestUpgradeSatisfaction:

    def test_setting_off_keeps_any_trailer(self):
        profile = make_profile(upgrade=False)
        media = make_media([make_download(1, 1, "search1")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == []
        assert not result.details[0].upgrade
        assert result.details[0].upgrade_state is None

    def test_any_tmdb_trailer_is_a_match_not_only_the_first(self):
        """Decision 2."""
        profile = make_profile()
        media = make_media([make_download(1, 1, "tmdb2")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == []
        assert result.details[0].upgrade_state == "matched"

    def test_a_trailer_that_is_not_from_tmdb_is_replaced(self):
        profile = make_profile()
        media = make_media([make_download(1, 1, "search1")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == [profile]
        detail = result.details[0]
        assert detail.upgrade and not detail.satisfied
        assert detail.satisfied_by is None and detail.via is None
        assert detail.upgrade_state == "replace_not_tmdb"

    def test_an_unknown_video_stays_unless_the_profile_replaces_it(self):
        """Decision 4, amended: most files with no known video id came from
        the id that Radarr reports, which is a TMDB trailer. Replacing
        them all downloaded a large part of a library again for nothing.
        They stay unless `Replace Unknown Videos` is on, and the pending
        view says why."""
        media = make_media([make_download(1, 1, "unknown0000")])

        kept = evaluate_satisfaction(media, [make_profile()], TMDB)
        assert kept.unsatisfied == []
        assert kept.details[0].upgrade_state == "unknown_kept"

        profile = make_profile(replace_unknown=True)
        replaced = evaluate_satisfaction(media, [profile], TMDB)
        assert replaced.unsatisfied == [profile]
        assert replaced.details[0].upgrade_state == "replace_unknown"

    def test_a_known_trailer_goes_and_an_unknown_one_stays(self):
        """With `Replace Unknown Videos` off, a profile that owns both is
        replaced for the known trailer. The download task leaves the
        unknown one out of the replacement."""
        profile = make_profile()
        media = make_media(
            [
                make_download(1, 1, "unknown0000"),
                make_download(2, 1, "search1"),
            ]
        )
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == [profile]
        assert result.details[0].upgrade_state == "replace_not_tmdb"

    def test_a_video_the_user_chose_is_a_match(self):
        """Decision 3."""
        profile = make_profile()
        media = make_media([make_download(1, 1, "mine")])
        videos = [video("mine", VideoSource.USER)] + TMDB
        result = evaluate_satisfaction(media, [profile], videos)
        assert result.unsatisfied == []

    def test_a_video_the_user_chose_is_kept_in_any_language(self):
        """Decision 3: the language filter picks what to download. It never
        deletes a video a person picked — one added with no language, or
        in another language, stays (Copilot review on #696)."""
        profile = make_profile(language="it")
        media = make_media([make_download(1, 1, "mine")])
        videos = [
            video("mine", VideoSource.USER, language=None),
            video("tmdb_it", language="it"),
        ]
        result = evaluate_satisfaction(media, [profile], videos)
        assert result.unsatisfied == []

    def test_an_arr_id_is_not_a_target(self):
        profile = make_profile()
        media = make_media([make_download(1, 1, "search1")])
        videos = [video("arr1", VideoSource.ARR)]
        result = evaluate_satisfaction(media, [profile], videos)
        assert result.unsatisfied == []
        assert result.details[0].awaiting_tmdb

    def test_no_tmdb_list_keeps_the_trailer_and_waits(self):
        """Decision 6: never asked, or TMDB lists nothing."""
        profile = make_profile()
        media = make_media([make_download(1, 1, "search1")])
        for videos in (None, []):
            result = evaluate_satisfaction(media, [profile], videos)
            assert result.unsatisfied == []
            assert result.details[0].satisfied
            assert result.details[0].awaiting_tmdb
            assert result.details[0].upgrade_state == "awaiting_tmdb"

    def test_a_trailer_in_another_language_is_not_a_target(self):
        """Decision 2: the language of the profile filters the targets."""
        profile = make_profile(language="it")
        media = make_media([make_download(1, 1, "search1")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == []
        assert result.details[0].awaiting_tmdb

    def test_an_english_trailer_is_replaced_for_an_italian_profile(self):
        """W5: a changed language replaces the trailers of the old one."""
        profile = make_profile(language="it")
        media = make_media([make_download(1, 1, "tmdb1")])
        videos = TMDB + [video("tmdb_it", language="it")]
        result = evaluate_satisfaction(media, [profile], videos)
        assert result.unsatisfied == [profile]

    def test_no_key_means_no_upgrade(self, _with_a_tmdb_key):
        """Decision 11. An inert upgrade is not waiting for TMDB either."""
        _with_a_tmdb_key.tmdb_api_key = ""
        profile = make_profile()
        media = make_media([make_download(1, 1, "search1")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == []
        assert not result.details[0].awaiting_tmdb

    def test_always_search_means_no_upgrade(self):
        """Decision 11. With Always Search on, the upgrade is inert, so the
        refresh task must not ask TMDB about the item every seven days
        (Copilot review on #696)."""
        profile = make_profile(always_search=True)
        media = make_media([make_download(1, 1, "search1")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == []
        assert not result.details[0].awaiting_tmdb
        assert result.details[0].upgrade_state is None

    def test_a_kept_old_trailer_does_not_replace_again(self):
        """W6: the old file stays next to the TMDB one."""
        profile = make_profile()
        media = make_media(
            [make_download(1, 1, "search1"), make_download(2, 1, "tmdb1")]
        )
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == []

    def test_a_claimed_file_is_upgraded_and_still_claimed(self):
        """W8."""
        profile = make_profile()
        media = make_media([make_download(7, 0, "search1")])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.claims == [(7, 1)]
        assert result.unsatisfied == [profile]
        assert result.details[0].upgrade

    def test_only_the_downloads_of_the_profile_count(self):
        """W7: another profile's TMDB trailer does not satisfy this one."""
        upgrading = make_profile(1)
        other = make_profile(2, upgrade=False)
        media = make_media(
            [make_download(1, 1, "search1"), make_download(2, 2, "tmdb1")]
        )
        result = evaluate_satisfaction(media, [upgrading, other], TMDB)
        assert result.unsatisfied == [upgrading]

    def test_a_missing_trailer_is_a_plain_download_not_an_upgrade(self):
        profile = make_profile()
        media = make_media([])
        result = evaluate_satisfaction(media, [profile], TMDB)
        assert result.unsatisfied == [profile]
        assert not result.details[0].upgrade
