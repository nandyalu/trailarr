"""Profile validation for video types and the duration cap —
plans/phase-09-video-types.md decisions 5 and 10 (hygiene H24)."""

import pytest
from pydantic import ValidationError

from database.models.customfilter import CustomFilterCreate, FilterType
from database.models.trailerprofile import (
    MAX_DURATION_LIMIT,
    TrailerProfile,
    TrailerProfileCreate,
)


def _profile(**kw) -> TrailerProfile:
    """Validate the way the managers do: the validators live on the table
    model and run in `model_validate`, which create and update call."""
    return TrailerProfile.model_validate(
        TrailerProfileCreate(
            customfilter=CustomFilterCreate(
                filter_name="Video Type Test",
                filter_type=FilterType.TRAILER,
                filters=[],
            ),
            **kw,
        )
    )


class TestVideoType:
    def test_the_default_is_a_trailer(self):
        assert _profile().video_type == "trailer"

    def test_the_stored_form_is_lowercase(self):
        assert _profile(video_type="Featurette").video_type == "featurette"

    def test_an_unknown_type_is_refused(self):
        with pytest.raises(ValidationError, match="Invalid video type"):
            _profile(video_type="interview")

    def test_always_search_needs_search_youtube(self):
        """Decision 5 as amended: Always Search is a mode of the search,
        so without the search it would mean "never download"."""
        with pytest.raises(ValidationError, match="Search YouTube"):
            _profile(search_youtube=False, always_search=True)

    def test_always_search_stays_fine_with_the_search_on(self):
        assert _profile(video_type="trailer", always_search=True).always_search

    def test_a_featurette_profile_may_search_when_asked(self):
        profile = _profile(
            video_type="featurette", search_youtube=True, always_search=True
        )
        assert profile.search_youtube and profile.always_search

    def test_the_search_is_on_by_default(self):
        assert _profile().search_youtube is True

    def test_the_file_name_token(self):
        profile = _profile(file_name="{title}-{video_type}.{ext}")
        assert "{video_type}" in profile.file_name


class TestMaxDuration:
    """The old check `90 > max > 600` could never be true, so the API took
    any value. A test for each edge, because this line runs only on the
    error path."""

    def test_the_limit_is_1200(self):
        assert MAX_DURATION_LIMIT == 1200

    @pytest.mark.parametrize("value", [90, 600, 1200])
    def test_values_inside_the_range_pass(self, value):
        assert _profile(min_duration=30, max_duration=value).max_duration == (
            value
        )

    @pytest.mark.parametrize("value", [89, 1201, 5000])
    def test_values_outside_the_range_fail(self, value):
        with pytest.raises(ValidationError, match="max_duration"):
            _profile(min_duration=30, max_duration=value)

    def test_the_gap_rule_still_holds(self):
        with pytest.raises(ValidationError, match="60 seconds"):
            _profile(min_duration=1150, max_duration=1200)
