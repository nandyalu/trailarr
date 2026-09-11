"""Tests for utils/error_classify.py."""

from utils.error_classify import is_video_unavailable


class TestVideoUnavailable:
    """Telling "that video is gone" apart from "your setup is broken"."""

    def test_the_wordings_youtube_uses(self):
        for text in (
            "ERROR: [youtube] abc: This video is unavailable",
            "ERROR: Video unavailable",
            "ERROR: Private video. Sign in if you've been granted access",
            "ERROR: This video has been removed by the uploader",
            "ERROR: The uploader has not made this video available in your country",
        ):
            assert is_video_unavailable(text), text

    def test_a_broken_setup_is_not_mistaken_for_it(self):
        for text in (
            "ERROR: Sign in to confirm you're not a bot",
            "ERROR: HTTP Error 429: Too Many Requests",
            "ERROR: nsig extraction failed",
            "yt-dlp was not found at '/usr/local/bin/yt-dlp'.",
        ):
            assert not is_video_unavailable(text), text

    def test_nothing_is_not_a_missing_video(self):
        assert is_video_unavailable("") is False
        assert is_video_unavailable(None) is False
