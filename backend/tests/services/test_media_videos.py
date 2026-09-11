"""The two ways to choose a video must agree — Phase 8, decision 5b.

A user can type an id into the YouTube ID field, or post a link to the
videos endpoint. Both are the same act, so both create the USER row, set
the legacy column that Phase 9 removes, and record the event that the
Events page shows.
"""

from unittest.mock import MagicMock, patch

import pytest

from services import media as media_service

PKG = "services.media"


@pytest.fixture
def managers():
    with patch(f"{PKG}.media_manager") as media_manager:
        with patch(f"{PKG}.video_manager") as video_manager:
            with patch(f"{PKG}.event_manager") as event_manager:
                media_manager.read.return_value = MagicMock(
                    youtube_trailer_id="old_id"
                )
                yield media_manager, video_manager, event_manager


class TestAddVideo:

    def test_the_row_the_column_and_the_event(self, managers):
        media_manager, video_manager, event_manager = managers

        media_service.add_video(7, "new_id")

        video_manager.add_user_video.assert_called_once_with(7, "new_id")
        media_manager.update_ytid.assert_called_once_with(7, "new_id")
        assert event_manager.track_youtube_id_changed.call_count == 1

    def test_no_event_when_the_video_is_the_one_already_stored(self, managers):
        media_manager, video_manager, event_manager = managers
        media_manager.read.return_value = MagicMock(
            youtube_trailer_id="same_id"
        )

        media_service.add_video(7, "same_id")

        video_manager.add_user_video.assert_called_once()
        event_manager.track_youtube_id_changed.assert_not_called()


class TestSetYoutubeId:

    def test_typing_an_id_also_creates_the_user_row(self, managers):
        _, video_manager, _ = managers

        media_service.set_youtube_id(7, "typed_id")

        video_manager.add_user_video.assert_called_once_with(7, "typed_id")

    def test_clearing_the_field_creates_no_row(self, managers):
        media_manager, video_manager, _ = managers

        media_service.set_youtube_id(7, "")

        media_manager.update_ytid.assert_called_once_with(7, "")
        video_manager.add_user_video.assert_not_called()


class TestRemoveVideo:

    def test_removing_reports_whether_it_was_there(self, managers):
        _, video_manager, _ = managers
        video_manager.delete_video.return_value = False

        assert media_service.remove_video(7, "gone") is False
