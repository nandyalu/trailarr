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


class TestTheTwoListsAgree:
    """Everything the classifier calls unavailable must read as unavailable.

    `classify_ytdlp_error` turns an error into a sentence for the user, and
    `is_video_unavailable` decides whether the health test blames the video
    or the setup. They read the same output, so a signature in one and not
    the other makes the Health page report a broken setup for a video that
    was simply deleted — `HTTP Error 410` did exactly that.
    """

    def test_every_unavailable_signature_reads_as_unavailable(self):
        from utils import error_classify

        group = next(
            fragments
            for fragments, reason in error_classify._SIGNATURES
            if "unavailable (removed, private" in reason
        )
        for fragment in group:
            assert error_classify.is_video_unavailable(
                f"ERROR: [youtube] {fragment}"
            ), f"'{fragment}' is unavailable to the classifier, not to the test"

    def test_a_deleted_video_is_not_the_users_fault(self):
        from utils.error_classify import is_video_unavailable

        assert is_video_unavailable("ERROR: unable to download: HTTP Error 410: Gone")
        assert is_video_unavailable(
            "ERROR: [youtube] abc: This video is not available"
        )
