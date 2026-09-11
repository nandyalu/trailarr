"""Filter-evaluation parity tests (Phase 6).

The backend `matches_filters` and the frontend `applyCustomFilter` are two
implementations of the same rules. They drift silently, so both run the SAME
fixture: `tests/fixtures/filter-cases.json`. The frontend half lives in
`frontend/src/app/media/utils/filter-parity.spec.ts`.

When you add a case, add it to the JSON — never to only one side.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from database.models.download import DownloadRead
from database.models.filter import FilterCondition, FilterRead
from database.models.media import MediaRead
from services.filters import matches_filters

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "filter-cases.json"
)
FIXTURE = json.loads(FIXTURE_PATH.read_text())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _build_download(spec: dict, index: int) -> DownloadRead:
    """Build a DownloadRead from a fixture download spec."""
    added_at = _now() - timedelta(days=spec.get("days_ago", 0))
    return DownloadRead(
        id=index + 1,
        media_id=1,
        path=f"/nonexistent/d{index}.mkv",
        file_name=f"d{index}.mkv",
        file_hash=f"h{index}",
        size=1000,
        resolution=spec.get("resolution", 1080),
        file_format="mkv",
        video_format="vp9",
        audio_format="opus",
        duration=120,
        youtube_id="ytid",
        youtube_channel="chan",
        file_exists=spec.get("file_exists", True),
        profile_id=spec.get("profile_id", 1),
        added_at=added_at,
        updated_at=added_at,
    )


def _build_media(overrides: dict) -> MediaRead:
    """Build a MediaRead from a fixture media spec."""
    added_at = _now() - timedelta(days=overrides.get("added_at_days_ago", 1))
    downloads = [
        _build_download(spec, i)
        for i, spec in enumerate(overrides.get("downloads", []))
    ]
    return MediaRead(
        id=1,
        connection_id=1,
        arr_id=1,
        is_movie=True,
        title="Parity Movie",
        year=2024,
        language="en",
        runtime=100,
        txdb_id="parity-1",
        folder_path="/nonexistent/parity",
        added_at=added_at,
        updated_at=added_at,
        downloaded_at=None,
        monitor=True,
        arr_monitored=True,
        downloads=downloads,
    )


def _build_filter(case: dict) -> FilterRead:
    return FilterRead(
        id=1,
        customfilter_id=1,
        filter_by=case["filter_by"],
        filter_condition=FilterCondition(case["filter_condition"]),
        filter_value=case["filter_value"],
    )


@pytest.mark.parametrize(
    "case", FIXTURE["cases"], ids=lambda c: c["name"]
)
def test_filter_parity_case(case: dict):
    """Each shared case evaluates to its expected result."""
    media = _build_media(FIXTURE["media"][case["media"]])
    result = matches_filters(media, [_build_filter(case)])
    assert result is case["expected"]


def test_fixture_covers_every_download_field():
    """Every virtual download field has at least one shared case.

    Stops a new field from shipping without parity coverage.
    """
    from database.models.filter import (
        VIRTUAL_BOOL_COLS,
        VIRTUAL_DATE_COLS,
        VIRTUAL_INT_COLS,
    )

    covered = {c["filter_by"] for c in FIXTURE["cases"]}
    expected = set(VIRTUAL_BOOL_COLS + VIRTUAL_INT_COLS + VIRTUAL_DATE_COLS)
    assert expected <= covered, expected - covered
