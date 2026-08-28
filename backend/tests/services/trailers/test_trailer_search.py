import pytest
from database.models.customfilter import CustomFilterRead, FilterType
from database.models.trailerprofile import TrailerProfileRead
from services.trailers.trailers.utils import extract_youtube_id
from services.trailers.trailer_search import _yt_search_filter
from services.trailers.trailer_search import __replace_media_options
from services.trailers.trailer_search import __has_all_words
from services.trailers.trailer_search import __has_any_words


@pytest.mark.parametrize(
    "url,expected",
    [
        # Standard YouTube watch URLs
        ("https://www.youtube.com/watch?v=abcdefghijk", "abcdefghijk"),
        ("https://youtube.com/watch?v=abcdefghijk", "abcdefghijk"),
        ("https://m.youtube.com/watch?v=abcdefghijk", "abcdefghijk"),
        (
            "https://www.youtube.com/watch?v=abcdefghijk&feature=related",
            "abcdefghijk",
        ),
        # Short youtu.be URLs
        ("https://youtu.be/abcdefghijk", "abcdefghijk"),
        # Embed URLs
        ("https://www.youtube.com/embed/abcdefghijk", "abcdefghijk"),
        # /v/ URLs
        ("https://www.youtube.com/v/abcdefghijk", "abcdefghijk"),
        # /u/1/ URLs
        ("https://www.youtube.com/u/1/abcdefghijk", "abcdefghijk"),
        # With additional parameters
        (
            "https://www.youtube.com/watch?v=abcdefghijk&list=PL1234567890",
            "abcdefghijk",
        ),
        # Invalid: wrong length
        ("https://www.youtube.com/watch?v=abcde", None),
        ("https://youtu.be/abcde", None),
        # Invalid: no video id
        ("https://www.youtube.com/", None),
        ("https://youtu.be/", None),
        # Invalid: not a YouTube URL
        ("https://vimeo.com/123456789", None),
        ("", None),
        (None, None),
    ],
)
def test_extract_youtube_id(url, expected):
    if url is None:
        result = extract_youtube_id("")
    else:
        result = extract_youtube_id(url)
    assert result == expected


class DummyMedia:
    def __init__(
        self,
        title="Test Movie",
        is_movie=True,
        year=2022,
        media_filename="test_movie.mp4",
        language="en",
    ):
        self.title = title
        self.is_movie = is_movie
        self.year = year
        self.media_filename = media_filename
        self.language = language

    def model_dump(self):
        return {
            "title": self.title,
            "is_movie": self.is_movie,
            "year": self.year,
            "media_filename": self.media_filename,
            "language": self.language,
        }


@pytest.mark.parametrize(
    "query,media,expected",
    [
        # Basic replacement
        (
            "{title} {year} {is_movie} {media_filename} {language}",
            DummyMedia(),
            "Test Movie 2022 movie test_movie English",
        ),
        # Year is 0, should be blank
        (
            "{title} {year} {is_movie} {media_filename} {language}",
            DummyMedia(year=0),
            "Test Movie movie test_movie English",
        ),
        # is_movie False, should be 'series'
        (
            "{title} {year} {is_movie} {media_filename} {language}",
            DummyMedia(is_movie=False),
            "Test Movie 2022 series test_movie English",
        ),
        # media_filename with extension, should remove extension
        (
            "{media_filename}",
            DummyMedia(media_filename="something.mkv"),
            "something",
        ),
        # language not in language_names, fallback to code
        ("{language}", DummyMedia(language="xx"), "xx"),
        # Extra spaces should be removed
        (
            "{title}  {year}   {is_movie} ",
            DummyMedia(),
            "Test Movie 2022 movie",
        ),
        # Empty query returns empty string
        ("", DummyMedia(), ""),
        # None media returns query unchanged
        ("test {title}", None, "test {title}"),
    ],
)
def test_replace_media_options(query, media, expected):
    result = __replace_media_options(query, media)
    assert result == expected


@pytest.mark.parametrize(
    "words,title,expected",
    [
        # All words present
        (["foo", "bar"], "This is foo and bar", True),
        # One word missing
        (["foo", "baz"], "foo bar", False),
        # Case insensitive match
        (["Foo", "BAR"], "foo bar", True),
        # Extra spaces in word
        ([" foo ", "bar "], "foo bar", True),
        # Empty words list
        ([], "anything", True),
        # Empty title
        (["foo"], "", False),
        # Word with '||' (should match any subword)
        (["foo||bar"], "bar", True),
        (["foo||bar"], "baz", False),
        (["foo||bar", "baz"], "bar baz", True),
        (["foo||bar", "baz"], "bar", False),
        # Multiple '||' words, one matches
        (["foo||bar||baz"], "baz", True),
        # Combination: one '||' matches, other word present
        (["foo||bar", "baz"], "foo baz", True),
        # Combination: one '||' matches, other word missing
        (["foo||bar", "baz"], "foo", False),
        # Word with only spaces
        ([" "], "anything", True),
    ],
)
def test_has_all_words(words, title, expected):
    assert __has_all_words(words, title) == expected


@pytest.mark.parametrize(
    "words,title,expected",
    [
        # Any word present
        (["foo", "bar"], "This is foo and baz", True),
        (["foo", "bar"], "This is baz", False),
        # Case insensitive match
        (["Foo", "BAR"], "foo bar", True),
        (["Foo", "BAR"], "baz", False),
        # Extra spaces in word
        ([" foo ", "bar "], "foo bar", True),
        # Empty words list
        ([], "anything", False),
        # Empty title
        (["foo"], "", False),
        # Word with '&&' (should match all subwords)
        (["foo&&bar"], "foo bar", True),
        (["foo&&bar"], "foo baz", False),
        (["foo&&bar", "baz"], "foo baz", True),
        (["foo&&bar", "baz"], "foo", False),
        # Multiple '&&' words, all present
        (["foo&&bar&&baz"], "foo bar baz", True),
        # Multiple '&&' words, one missing
        (["foo&&bar&&baz"], "foo bar", False),
        # Combination: one '&&' matches, other word present
        (["foo&&bar", "baz"], "foo bar baz", True),
        # Combination: one '&&' matches, other word missing
        (["foo&&bar", "baz"], "foo bar", True),
        # Word with only spaces
        ([" "], "anything", True),
    ],
)
def test_has_any_words(words, title, expected):
    assert __has_any_words(words, title) == expected


@pytest.fixture
def trailer_profile():
    cf = CustomFilterRead(
        id=1,
        filter_name="Test CF",
        filter_type=FilterType.TRAILER,
        filters=[],
    )
    return TrailerProfileRead(
        id=1,
        customfilter=cf,
        customfilter_id=cf.id,
        video_format="h264",
        audio_format="aac",
        subtitles_format="srt",
        file_format="mkv",
        video_resolution=1080,
        audio_volume_level=100,
        subtitles_enabled=True,
        subtitles_language="en",
        embed_metadata=True,
        ytdlp_extra_options="",
    )


def _video_info(**overrides) -> dict:
    """A search result info dict for a normal trailer video."""
    info = {
        "id": "abcdefghijk",
        "url": "https://www.youtube.com/watch?v=abcdefghijk",
        "title": "Test Movie Trailer",
        "duration": 120,
        "live_status": "not_live",
    }
    info.update(overrides)
    return info


class TestYtSearchFilterLiveContent:
    """Livestreams/premieres must never match as trailers (#626)."""

    def _run(self, info, profile):
        return _yt_search_filter(
            info,
            incomplete=False,
            media=DummyMedia(),
            profile=profile,
            exclude=None,
        )

    def test_normal_video_passes(self, trailer_profile):
        assert self._run(_video_info(), trailer_profile) is None

    def test_is_live_flag_rejected(self, trailer_profile):
        info = _video_info(is_live=True, duration=None)
        result = self._run(info, trailer_profile)
        assert result == "The video is a livestream or premiere"

    @pytest.mark.parametrize("live_status", ["is_live", "is_upcoming"])
    def test_live_status_rejected(self, trailer_profile, live_status):
        info = _video_info(live_status=live_status, duration=None)
        result = self._run(info, trailer_profile)
        assert result == "The video is a livestream or premiere"

    def test_finished_livestream_vod_passes(self, trailer_profile):
        # A VOD of an ended stream has a bounded duration — allowed
        info = _video_info(live_status="was_live", duration=120)
        assert self._run(info, trailer_profile) is None

    def test_none_duration_rejected(self, trailer_profile):
        # Livestreams report duration as None — must reject, not crash
        info = _video_info(duration=None)
        result = self._run(info, trailer_profile)
        assert result == "The video duration is unknown"

    def test_missing_duration_rejected(self, trailer_profile):
        info = _video_info()
        del info["duration"]
        result = self._run(info, trailer_profile)
        assert result == "The video duration is unknown"

    def test_zero_duration_rejected(self, trailer_profile):
        info = _video_info(duration=0)
        result = self._run(info, trailer_profile)
        assert result == "The video duration is unknown"

    def test_short_video_rejected(self, trailer_profile):
        info = _video_info(duration=30)
        result = self._run(info, trailer_profile)
        assert result == "The video is shorter than 60 seconds"

    def test_long_video_rejected(self, trailer_profile):
        info = _video_info(duration=700)
        result = self._run(info, trailer_profile)
        assert result == "The video is longer than 600 seconds"
