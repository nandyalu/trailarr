"""Tests for the extras-profile nudge — plans/phase-09-video-types.md
decision 7: a nudge, never a change."""

from types import SimpleNamespace
from unittest.mock import patch

from tasks import profile_nudge
from tasks.profile_nudge import nudge_extras_profiles

PKG = "tasks.profile_nudge"


def _profile(
    name: str,
    *,
    video_type: str = "trailer",
    search_query: str = "{title} {year} {is_movie} trailer",
    file_name: str = "{title} ({year})-trailer.{ext}",
    folder_name: str = "Trailers",
    include_words: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        video_type=video_type,
        search_query=search_query,
        file_name=file_name,
        folder_name=folder_name,
        include_words=include_words,
        customfilter=SimpleNamespace(filter_name=name),
    )


def test_a_plain_trailer_profile_gets_no_nudge():
    with patch(
        f"{PKG}.trailerprofile_manager.get_trailerprofiles",
        return_value=[_profile("Movies")],
    ):
        assert nudge_extras_profiles() == 0


def test_a_hacky_profile_is_named_once(caplog):
    profiles = [
        _profile("Movies"),
        _profile("Extras", search_query="{title} featurette"),
        _profile("Bonus", folder_name="Featurettes"),
        _profile("Teasers", include_words="teaser"),
    ]
    with (
        patch(
            f"{PKG}.trailerprofile_manager.get_trailerprofiles",
            return_value=profiles,
        ),
        patch.object(profile_nudge, "logger") as logger,
    ):
        assert nudge_extras_profiles() == 3
    names = " ".join(str(c) for c in logger.warning.call_args_list)
    assert "'Extras'" in names
    assert "'Bonus'" in names
    assert "'Teasers'" in names
    assert "'Movies'" not in names


def test_a_profile_that_already_has_a_type_is_left_alone():
    with patch(
        f"{PKG}.trailerprofile_manager.get_trailerprofiles",
        return_value=[
            _profile(
                "Featurettes",
                video_type="featurette",
                search_query="{title} featurette",
            )
        ],
    ):
        assert nudge_extras_profiles() == 0


def test_the_nudge_changes_nothing():
    """Log only: no manager write is called."""
    with (
        patch(
            f"{PKG}.trailerprofile_manager.get_trailerprofiles",
            return_value=[_profile("Extras", folder_name="Featurettes")],
        ),
        patch(
            f"{PKG}.trailerprofile_manager.update_trailerprofile_setting",
            create=True,
        ) as update,
    ):
        nudge_extras_profiles()
    update.assert_not_called()
