"""File names and folders per video type — plans/phase-09-video-types.md
decision 6."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.trailers import trailer_file
from services.trailers.trailer_file import (
    _type_suffix_at_end,
    get_trailer_filename,
    move_trailer_to_folder,
)


def _media(tmp_path: Path) -> MagicMock:
    media = MagicMock()
    media.id = 1
    media.title = "Test Movie"
    media.year = 2020
    media.is_movie = True
    media.media_filename = "Test.Movie.2020.mkv"
    media.folder_path = str(tmp_path)
    media.youtube_trailer_id = "abc123"
    media.model_dump.return_value = {
        "title": "Test Movie",
        "year": 2020,
        "clean_title": "testmovie",
        "imdb_id": "tt1",
        "language": "en",
        "studio": "S",
        "title_slug": "1",
        "txdb_id": "1",
        "media_filename": "Test.Movie.2020.mkv",
    }
    return media


def _profile(video_type: str, **kw) -> MagicMock:
    profile = MagicMock()
    profile.id = 1
    profile.video_type = video_type
    profile.file_name = kw.get("file_name", "{title} ({year})-{video_type}.{ext}")
    profile.file_format = "mkv"
    profile.folder_enabled = kw.get("folder_enabled", True)
    profile.folder_name = kw.get("folder_name", "")
    profile.custom_folder = "{media_folder}"
    profile.video_resolution = 1080
    profile.video_format = "h264"
    profile.audio_format = "aac"
    return profile


class TestVideoTypeToken:
    @pytest.mark.parametrize(
        "video_type, suffix",
        [
            ("trailer", "trailer"),
            ("teaser", "trailer"),
            ("clip", "scene"),
            ("featurette", "featurette"),
            ("behind_the_scenes", "behindthescenes"),
            ("bloopers", "other"),
        ],
    )
    def test_the_token_writes_the_name_both_players_read(
        self, tmp_path, video_type, suffix
    ):
        name = get_trailer_filename(
            _media(tmp_path), _profile(video_type), "mkv", 1
        )
        assert name == f"Test Movie (2020)-{suffix}.mkv"

    def test_the_default_template_still_says_trailer(self, tmp_path):
        profile = _profile("featurette", file_name="{title} ({year})-trailer.{ext}")
        name = get_trailer_filename(_media(tmp_path), profile, "mkv", 1)
        assert name == "Test Movie (2020)-trailer.mkv"


class TestIncrementIndexBeforeTheSuffix:
    """A player reads the type from the end of the name, so the index goes
    before the suffix."""

    @pytest.mark.parametrize(
        "template, expected",
        [
            ("{title}-trailer.{ext}", "Test Movie 2-trailer.mkv"),
            ("{title}-featurette.{ext}", "Test Movie 2-featurette.mkv"),
            ("{title}-{video_type}.{ext}", "Test Movie 2-featurette.mkv"),
            ("{title}.{ext}", "Test Movie 2.mkv"),
        ],
    )
    def test_second_file(self, tmp_path, template, expected):
        profile = _profile("featurette", file_name=template)
        name = get_trailer_filename(_media(tmp_path), profile, "mkv", 2)
        assert name == expected

    def test_suffix_detection(self):
        assert _type_suffix_at_end("{title}-trailer.{ext}") == "-trailer.{ext}"
        assert _type_suffix_at_end("{title}-{video_type}.{ext}") == (
            "-{video_type}.{ext}"
        )
        assert _type_suffix_at_end("{title}-scene.{ext}") == "-scene.{ext}"
        assert _type_suffix_at_end("{title}.{ext}") is None


class TestFolderPerType:
    @pytest.mark.parametrize(
        "video_type, folder",
        [
            ("trailer", "Trailers"),
            ("teaser", "Trailers"),
            ("clip", "Scenes"),
            ("featurette", "Featurettes"),
            ("behind_the_scenes", "Behind The Scenes"),
            ("other", "Other"),
        ],
    )
    def test_an_empty_folder_name_takes_the_folder_of_the_type(
        self, tmp_path, video_type, folder
    ):
        src = tmp_path / "src.mkv"
        src.write_bytes(b"x")
        with patch.object(trailer_file, "get_folder_permissions", return_value=None):
            dst = move_trailer_to_folder(
                src, _media(tmp_path), _profile(video_type, folder_name="")
            )
        assert Path(dst).parent.name == folder
        assert Path(dst).exists()

    def test_the_folder_token(self, tmp_path):
        src = tmp_path / "src.mkv"
        src.write_bytes(b"x")
        profile = _profile("featurette", folder_name="Extras/{video_type}")
        with patch.object(trailer_file, "get_folder_permissions", return_value=None):
            dst = move_trailer_to_folder(src, _media(tmp_path), profile)
        assert Path(dst).parent == tmp_path / "Extras" / "Featurettes"

    def test_a_named_folder_is_kept(self, tmp_path):
        src = tmp_path / "src.mkv"
        src.write_bytes(b"x")
        profile = _profile("featurette", folder_name="Bonus")
        with patch.object(trailer_file, "get_folder_permissions", return_value=None):
            dst = move_trailer_to_folder(src, _media(tmp_path), profile)
        assert Path(dst).parent.name == "Bonus"
