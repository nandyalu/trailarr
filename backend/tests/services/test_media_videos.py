"""Adding a video that the user chose — Phase 8 decision 5b, Phase 9 H9.

Phase 9 dropped `media.youtube_trailer_id`, so `POST /media/{id}/videos`
is the only way to choose a video. It creates the USER row and records a
YOUTUBE_ID_CHANGED event that names the video a download of that type took
before, so the Events page says what the choice replaced.
"""

from unittest.mock import MagicMock, patch

import pytest

from services import media as media_service

PKG = "services.media"


def _candidate(video_id: str):
    return MagicMock(video_id=video_id)


@pytest.fixture
def managers():
    with patch(f"{PKG}.media_manager") as media_manager:
        with patch(f"{PKG}.video_manager") as video_manager:
            with patch(f"{PKG}.event_manager") as event_manager:
                video_manager.read_candidates.return_value = [
                    _candidate("old_id")
                ]
                yield media_manager, video_manager, event_manager


class TestAddVideo:

    def test_the_row_and_the_event(self, managers):
        media_manager, video_manager, event_manager = managers

        media_service.add_video(7, "new_id")

        video_manager.add_user_video.assert_called_once_with(
            7, "new_id", language=None, video_type="trailer"
        )
        event_manager.track_youtube_id_changed.assert_called_once()
        kwargs = event_manager.track_youtube_id_changed.call_args.kwargs
        assert kwargs["old_yt_id"] == "old_id"
        assert kwargs["new_yt_id"] == "new_id"

    def test_the_event_helper_gets_the_same_id_when_nothing_changes(
        self, managers
    ):
        """Choosing the video a download already takes: the helper gets
        equal ids and records nothing (that check lives in the helper)."""
        _, video_manager, event_manager = managers
        video_manager.read_candidates.return_value = [_candidate("same_id")]

        media_service.add_video(7, "same_id")

        kwargs = event_manager.track_youtube_id_changed.call_args.kwargs
        assert kwargs["old_yt_id"] == kwargs["new_yt_id"] == "same_id"

    def test_the_first_known_video_is_none_for_an_empty_list(self, managers):
        _, video_manager, event_manager = managers
        video_manager.read_candidates.return_value = []

        media_service.add_video(7, "first_id")

        kwargs = event_manager.track_youtube_id_changed.call_args.kwargs
        assert kwargs["old_yt_id"] is None
        assert kwargs["new_yt_id"] == "first_id"

    def test_a_failing_read_does_not_stop_the_add(self, managers):
        _, video_manager, _ = managers
        video_manager.read_candidates.side_effect = RuntimeError("db gone")

        media_service.add_video(7, "new_id")

        video_manager.add_user_video.assert_called_once()


class TestNoLegacyColumnPath:

    def test_the_manager_has_no_update_ytid(self):
        """Phase 9 (H9): nothing writes a YouTube id onto the media row."""
        import database.manager.media as real_media_manager

        assert not hasattr(real_media_manager, "update_ytid")


class TestRemoveVideo:

    def test_removing_reports_whether_it_was_there(self, managers):
        _, video_manager, _ = managers
        video_manager.delete_video.return_value = False

        assert media_service.remove_video(7, "gone") is False


class TestAddVideoWithALanguage:

    def test_the_language_reaches_the_row(self, managers):
        """Two profiles, one per language, each need their own video."""
        _, video_manager, _ = managers

        media_service.add_video(7, "italian_id", "it")

        video_manager.add_user_video.assert_called_once_with(
            7, "italian_id", language="it", video_type="trailer"
        )

    def test_a_featurette_compares_against_featurettes(self, managers):
        """Phase 9: the old id named in the event is the first video of the
        SAME type, not the first trailer."""
        _, video_manager, event_manager = managers

        media_service.add_video(7, "feat_id", video_type="featurette")

        video_manager.add_user_video.assert_called_once_with(
            7, "feat_id", language=None, video_type="featurette"
        )
        video_manager.read_candidates.assert_called_once_with(
            7, video_type="featurette"
        )
        event_manager.track_youtube_id_changed.assert_called_once()


class TestFirstVideoId:

    def test_reads_the_first_candidate_of_the_type(self, managers):
        _, video_manager, _ = managers
        video_manager.read_candidates.return_value = [
            _candidate("a"),
            _candidate("b"),
        ]

        assert media_service.first_video_id(7, "teaser") == "a"
        video_manager.read_candidates.assert_called_once_with(
            7, video_type="teaser"
        )

    def test_none_when_there_is_nothing(self, managers):
        _, video_manager, _ = managers
        video_manager.read_candidates.return_value = []

        assert media_service.first_video_id(7) is None
