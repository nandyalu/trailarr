"""Tests for the view-only field rule on filters (Phase 6).

Download and file-count fields are virtual fields evaluated from the media's
download/file rows. They are available to view filters only: a profile
(TRAILER) filter that matched on its own downloads would stop matching a
media item the moment it downloaded a trailer for it.

The rule is enforced backend-side (not just hidden in the UI), so raw API
calls are rejected too.
"""

import uuid

import pytest

import core.base.database.manager.customfilter as customfilter_manager
import core.base.database.manager.trailerprofile as trailerprofile_manager
from core.base.database.models.customfilter import (
    CustomFilterCreate,
    FilterType,
)
from core.base.database.models.filter import (
    VIEW_ONLY_COLS,
    FilterCondition,
    FilterCreate,
)
from core.base.database.models.trailerprofile import TrailerProfileCreate

VIEW_ONLY_SAMPLES = [
    ("has_downloads", FilterCondition.EQUALS, "true"),
    ("download_count", FilterCondition.GREATER_THAN, "1"),
    ("download_profile", FilterCondition.EQUALS, "2"),
    ("download_resolution", FilterCondition.LESS_THAN, "1080"),
    ("download_added_at", FilterCondition.IN_THE_LAST, "7"),
    ("download_file_missing", FilterCondition.EQUALS, "true"),
    ("has_unknown_profile_download", FilterCondition.EQUALS, "true"),
    ("file_count", FilterCondition.GREATER_THAN, "0"),
]


def _name(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _filter(field: str, condition: FilterCondition, value: str):
    return FilterCreate(
        filter_by=field, filter_condition=condition, filter_value=value
    )


# Profiles live in the shared test database, and the download-attribution
# tests attribute downloads to ANY matching profile. Every profile created
# here carries this filter so it matches no media in other tests.
_SCOPE_FILTER = ("txdb_id", FilterCondition.EQUALS, "phase6-view-only-scope")


def _profile_create(filters: list) -> TrailerProfileCreate:
    return TrailerProfileCreate(
        customfilter=CustomFilterCreate(
            filter_name=_name("Profile"),
            filter_type=FilterType.TRAILER,
            filters=[_filter(*_SCOPE_FILTER), *filters],
        )
    )


class TestViewOnlyFieldsRejectedOnProfiles:

    @pytest.mark.parametrize(
        "field,condition,value",
        VIEW_ONLY_SAMPLES,
        ids=[f[0] for f in VIEW_ONLY_SAMPLES],
    )
    def test_profile_create_rejects_field(self, field, condition, value):
        with pytest.raises(ValueError) as exc:
            trailerprofile_manager.create_trailerprofile(
                _profile_create([_filter(field, condition, value)])
            )
        assert field in str(exc.value)
        assert "view filters" in str(exc.value)

    def test_error_names_every_offending_field(self):
        with pytest.raises(ValueError) as exc:
            trailerprofile_manager.create_trailerprofile(
                _profile_create(
                    [
                        _filter("download_count", FilterCondition.EQUALS, "1"),
                        _filter(
                            "download_resolution",
                            FilterCondition.EQUALS,
                            "1080",
                        ),
                    ]
                )
            )
        assert "download_count" in str(exc.value)
        assert "download_resolution" in str(exc.value)

    def test_profile_update_rejects_field(self):
        profile = trailerprofile_manager.create_trailerprofile(
            _profile_create(
                [_filter("is_movie", FilterCondition.EQUALS, "true")]
            )
        )
        create = TrailerProfileCreate.model_validate(
            profile.model_dump()
            | {
                "customfilter": profile.customfilter.model_dump()
                | {
                    "filters": [
                        _filter(
                            "download_count", FilterCondition.EQUALS, "1"
                        ).model_dump()
                    ]
                }
            }
        )
        with pytest.raises(ValueError) as exc:
            trailerprofile_manager.update_trailerprofile(profile.id, create)
        assert "download_count" in str(exc.value)

    def test_profile_accepts_regular_fields(self):
        profile = trailerprofile_manager.create_trailerprofile(
            _profile_create(
                [
                    _filter("is_movie", FilterCondition.EQUALS, "true"),
                    _filter("year", FilterCondition.GREATER_THAN, "2000"),
                ]
            )
        )
        fields = {f.filter_by for f in profile.customfilter.filters}
        assert {"is_movie", "year"} <= fields

    def test_profile_still_accepts_has_file(self):
        """has_file/has_folder predate this rule and stay available to
        profiles — they describe the media folder, not profile output."""
        profile = trailerprofile_manager.create_trailerprofile(
            _profile_create(
                [_filter("has_file", FilterCondition.CONTAINS, "trailer")]
            )
        )
        fields = {f.filter_by for f in profile.customfilter.filters}
        assert "has_file" in fields


class TestViewFiltersAcceptViewOnlyFields:

    @pytest.mark.parametrize(
        "field,condition,value",
        VIEW_ONLY_SAMPLES,
        ids=[f[0] for f in VIEW_ONLY_SAMPLES],
    )
    def test_view_filter_accepts_field(self, field, condition, value):
        created = customfilter_manager.create_customfilter(
            CustomFilterCreate(
                filter_name=_name("View"),
                filter_type=FilterType.HOME,
                filters=[_filter(field, condition, value)],
            )
        )
        assert created.filters[0].filter_by == field

    def test_switching_a_view_filter_to_a_profile_type_is_rejected(self):
        created = customfilter_manager.create_customfilter(
            CustomFilterCreate(
                filter_name=_name("View"),
                filter_type=FilterType.HOME,
                filters=[
                    _filter("download_count", FilterCondition.EQUALS, "1")
                ],
            )
        )
        update = CustomFilterCreate(
            id=created.id,
            filter_name=created.filter_name,
            filter_type=FilterType.TRAILER,
            filters=[_filter("download_count", FilterCondition.EQUALS, "1")],
        )
        with pytest.raises(ValueError) as exc:
            customfilter_manager.update_customfilter(created.id, update)
        assert "download_count" in str(exc.value)


def test_every_view_only_field_has_a_sample():
    """Keeps this test honest when a new view-only field is added."""
    assert {f[0] for f in VIEW_ONLY_SAMPLES} == VIEW_ONLY_COLS
