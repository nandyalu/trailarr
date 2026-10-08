"""The download task and the pending view for a profile that waits for
TMDB — Phase 9, wargame W3."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.trailers.trailers import missing, pending


def _profile(profile_id: int, search_youtube: bool) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=100,
        enabled=True,
        video_type="trailer",
        search_youtube=search_youtube,
        always_search=False,
        language="",
        upgrade_to_tmdb=False,
        replace_unknown_videos=False,
        customfilter=SimpleNamespace(filter_name=f"Profile {profile_id}", filters=[]),
    )


def _media() -> SimpleNamespace:
    return SimpleNamespace(
        id=1, title="Waiting Movie", monitor=True, downloads=[], tmdb_id=603,
        last_videos_refresh=None, is_movie=True,
    )


class TestDownloadTask:
    def test_a_waiting_profile_is_not_attempted(self):
        waiting, searching = _profile(1, False), _profile(2, True)
        with (
            patch.object(missing.media_manager, "read", return_value=_media()),
            patch.object(
                missing.trailerprofile,
                "get_trailerprofiles",
                return_value=[waiting, searching],
            ),
            patch.object(
                missing, "find_matching_profiles", return_value=[waiting, searching]
            ),
            patch.object(
                missing.video_manager, "read_candidates", return_value=[]
            ) as read,
            patch.object(
                missing, "_filter_backoff_eligible", side_effect=lambda m, u: u
            ),
        ):
            _, to_download = missing._read_current_eligible_profiles(1)
        read.assert_called_once_with(1, video_type=None)
        assert [p.id for p in to_download] == [2]


class TestPendingView:
    def test_the_matrix_says_the_profile_waits(self):
        waiting = _profile(1, False)
        with (
            patch.object(pending, "find_matching_profiles", return_value=[waiting]),
            patch.object(pending.video_manager, "read_candidates", return_value=[]),
            patch.object(pending.attempt_manager, "read_for_media", return_value=[]),
        ):
            view = pending.compute_media_pending(_media(), [waiting])
        [row] = view.profiles
        assert row.pending is True
        assert row.upgrade_state == "awaiting_tmdb"
