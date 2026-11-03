"""Profile validation for the placeholders of the file name, the custom
folder and the search query (#735)."""

import pytest
from pydantic import ValidationError

from database.models.customfilter import CustomFilterCreate, FilterType
from database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
)


def _profile(**kw) -> TrailerProfile:
    """Validate the way the managers do: the validators live on the table
    model and run in `model_validate`, which create and update call."""
    return TrailerProfile.model_validate(
        TrailerProfileCreate(
            customfilter=CustomFilterCreate(
                filter_name="Template Test",
                filter_type=FilterType.TRAILER,
                filters=[],
            ),
            **kw,
        )
    )


@pytest.mark.parametrize("key", ["tmdb_id", "tvdb_id"])
class TestIdPlaceholders:
    def test_the_file_name_accepts_the_id(self, key):
        template = f"{{title}} ({{year}}) [{key}-{{{key}}}]-trailer.{{ext}}"
        assert _profile(file_name=template).file_name == template

    def test_the_custom_folder_accepts_the_id(self, key):
        template = f"/trailers/{{{key}}}"
        assert _profile(custom_folder=template).custom_folder == template

    def test_the_search_query_accepts_the_id(self, key):
        template = f"{{title}} {{{key}}} trailer"
        assert _profile(search_query=template).search_query == template


def test_an_unknown_placeholder_is_still_refused():
    with pytest.raises(ValidationError, match="Invalid file name template"):
        _profile(file_name="{title} {imdbid}-trailer.{ext}")
