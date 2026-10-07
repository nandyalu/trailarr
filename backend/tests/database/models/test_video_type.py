"""Tests for the video type tables — plans/phase-09-video-types.md
decisions 1, 2, 4 and 6, wargame W2.

The classifier reads the names of Plex and Jellyfin; the writer uses only
the names both players read.
"""

import pytest

from database.models.video_type import (
    VIDEO_TYPES,
    VideoType,
    classify_by_folder,
    classify_by_suffix,
    classify_extra_name,
    file_suffix,
    folder_name,
    hacky_profile_keyword,
    is_trailer_type,
    normalize_video_type,
    video_type_from_tmdb,
    video_type_label,
)


class TestStoredForm:
    def test_the_values_are_lowercase_strings(self):
        assert VIDEO_TYPES == [
            "trailer",
            "teaser",
            "clip",
            "featurette",
            "behind_the_scenes",
            "bloopers",
            "other",
        ]

    @pytest.mark.parametrize(
        "value, expected",
        [
            (None, "trailer"),
            ("", "trailer"),
            ("  ", "trailer"),
            ("Trailer", "trailer"),
            ("FEATURETTE", "featurette"),
            (VideoType.CLIP, "clip"),
            (" behind_the_scenes ", "behind_the_scenes"),
        ],
    )
    def test_normalize(self, value, expected):
        assert normalize_video_type(value) == expected

    def test_an_unknown_type_is_refused(self):
        with pytest.raises(ValueError, match="Invalid video type"):
            normalize_video_type("interview")

    def test_is_trailer_type(self):
        assert is_trailer_type(None)
        assert is_trailer_type("TRAILER")
        assert not is_trailer_type("teaser")

    def test_labels(self):
        assert video_type_label("behind_the_scenes") == "Behind the Scenes"
        assert video_type_label(None) == "Trailer"


class TestTmdbMapping:
    @pytest.mark.parametrize(
        "tmdb_type, expected",
        [
            ("Trailer", VideoType.TRAILER),
            ("Teaser", VideoType.TEASER),
            ("Clip", VideoType.CLIP),
            ("Featurette", VideoType.FEATURETTE),
            ("Behind the Scenes", VideoType.BEHIND_THE_SCENES),
            ("Bloopers", VideoType.BLOOPERS),
            ("Opening Credits", VideoType.OTHER),
            ("Something New", VideoType.OTHER),
            (" trailer ", VideoType.TRAILER),
        ],
    )
    def test_map(self, tmdb_type, expected):
        assert video_type_from_tmdb(tmdb_type) is expected


class TestWriter:
    """Decision 6: write only names that BOTH players read."""

    @pytest.mark.parametrize(
        "video_type, suffix, folder",
        [
            ("trailer", "trailer", "Trailers"),
            ("teaser", "trailer", "Trailers"),
            ("clip", "scene", "Scenes"),
            ("featurette", "featurette", "Featurettes"),
            ("behind_the_scenes", "behindthescenes", "Behind The Scenes"),
            ("bloopers", "other", "Other"),
            ("other", "other", "Other"),
        ],
    )
    def test_names(self, video_type, suffix, folder):
        assert file_suffix(video_type) == suffix
        assert folder_name(video_type) == folder

    def test_every_type_has_a_name(self):
        for video_type in VIDEO_TYPES:
            assert file_suffix(video_type)
            assert folder_name(video_type)


class TestClassifier:
    """Decisions 2 and 4, wargame W2: the suffix wins over the folder."""

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("/m/Movie (2020)/Movie (2020)-trailer.mkv", VideoType.TRAILER),
            ("/m/Movie (2020)/Trailers/Movie-teaser.mkv", VideoType.TEASER),
            ("/m/Movie/Movie-TEASER.MKV", VideoType.TEASER),
            ("/m/Movie/Movie-clip.mp4", VideoType.CLIP),
            ("/m/Movie/Movie-scene.mp4", VideoType.CLIP),
            ("/m/Movie/Movie-featurette.mp4", VideoType.FEATURETTE),
            ("/m/Movie/Movie-interview.mp4", VideoType.FEATURETTE),
            ("/m/Movie/Movie-behindthescenes.mp4", VideoType.BEHIND_THE_SCENES),
            ("/m/Movie/Movie-bloopers.mp4", VideoType.BLOOPERS),
            ("/m/Movie/Movie-short.mp4", VideoType.OTHER),
            ("/m/Movie/Movie-deleted.mp4", VideoType.OTHER),
            ("/m/Movie/Movie-extra.mp4", VideoType.OTHER),
            ("/m/Movie/Movie-other.mp4", VideoType.OTHER),
            ("/m/Movie/Featurettes/Making Of.mkv", VideoType.FEATURETTE),
            ("/m/Movie/Behind The Scenes/x.mkv", VideoType.BEHIND_THE_SCENES),
            ("/m/Movie/Deleted Scenes/x.mkv", VideoType.OTHER),
            ("/m/Movie/Interviews/x.mkv", VideoType.FEATURETTE),
            ("/m/Movie/Scenes/x.mkv", VideoType.CLIP),
            ("/m/Movie/clips/x.mkv", VideoType.CLIP),
            ("/m/Movie/Shorts/x.mkv", VideoType.OTHER),
            ("/m/Movie/Other/x.mkv", VideoType.OTHER),
            ("/m/Movie/Others/x.mkv", VideoType.OTHER),
            ("/m/Movie/extras/x.mkv", VideoType.OTHER),
            ("/m/Movie/Trailers/x.mkv", VideoType.TRAILER),
            ("/m/Movie/Movie Official Trailer.mkv", VideoType.TRAILER),
            ("/m/Movie/Movie (2020).mkv", None),
            ("/m/Movie/Bonus/x.mkv", None),
        ],
    )
    def test_classify(self, path, expected):
        assert classify_extra_name(path) is expected

    def test_a_suffix_is_read_only_at_the_end_of_the_stem(self):
        assert classify_by_suffix("/m/Movie/featurette of Movie.mkv") is None
        assert classify_by_suffix("/m/Movie/Movie-featurette.mkv") is (
            VideoType.FEATURETTE
        )

    def test_behindthescenes_is_not_read_as_scene(self):
        assert classify_by_suffix("/m/x-behindthescenes.mkv") is (
            VideoType.BEHIND_THE_SCENES
        )

    def test_folder_names_are_case_insensitive(self):
        assert classify_by_folder("/m/Movie/FEATURETTES/x.mkv") is (
            VideoType.FEATURETTE
        )

    def test_a_windows_style_path(self):
        assert (
            classify_extra_name(r"D:\Movies\Movie (2020)\Movie-featurette.mkv")
            is VideoType.FEATURETTE
        )


class TestHackyProfileKeywords:
    """Decision 7: the words that mark a trailer profile as an extras
    profile."""

    def test_finds_a_keyword_in_any_field(self):
        assert hacky_profile_keyword("{title} featurette", "", "") == (
            "featurette"
        )
        assert hacky_profile_keyword("", "", "Featurettes") == "featurette"
        assert hacky_profile_keyword("", "", "", "teaser,clip") == "teaser"

    def test_a_plain_trailer_profile_has_none(self):
        assert (
            hacky_profile_keyword(
                "{title} {year} {is_movie} trailer",
                "{title} ({year})-trailer.{ext}",
                "Trailers",
                "",
            )
            is None
        )

    def test_empty_values_are_fine(self):
        assert hacky_profile_keyword("", None, "") is None  # type: ignore
