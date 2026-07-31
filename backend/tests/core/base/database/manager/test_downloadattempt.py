"""Tests for the DownloadAttempt manager and backoff eligibility."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

import core.base.database.manager.downloadattempt as attempt_manager
import core.base.database.manager.media as media_manager
from core.base.database.models.connection import (
    ArrType,
    Connection,
)
from core.base.database.models.downloadattempt import (
    DownloadAttemptRead,
    is_eligible,
    next_eligible_at,
)
from core.base.database.models.media import MediaCreate
from core.base.database.utils.engine import write_session


@write_session
def _make_connection(*, _session: Session = None) -> Connection:  # type: ignore
    conn = Connection(
        name="Attempt Test Connection",
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="test_key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn


@pytest.fixture(scope="module")
def media_id() -> int:
    conn = _make_connection()
    media = media_manager.create(
        MediaCreate(
            connection_id=conn.id,  # type: ignore[arg-type]
            arr_id=80001,
            is_movie=True,
            title="Attempt Movie",
            txdb_id="attempt-1",
        )
    )
    return media.id


class TestAttemptManager:

    def test_record_failure_creates_then_increments(self, media_id):
        first = attempt_manager.record_failure(media_id, 1, "no results")
        assert (first.attempt_count, first.last_error) == (1, "no results")

        second = attempt_manager.record_failure(media_id, 1, "still nothing")
        assert second.id == first.id
        assert second.attempt_count == 2
        assert second.last_error == "still nothing"

    def test_error_truncated(self, media_id):
        attempt = attempt_manager.record_failure(media_id, 2, "x" * 2000)
        assert len(attempt.last_error) == 500

    def test_units_are_independent(self, media_id):
        a = attempt_manager.record_failure(media_id, 3, "e", unit="default")
        b = attempt_manager.record_failure(media_id, 3, "e", unit="s01")
        assert a.id != b.id

    def test_clear_removes_row(self, media_id):
        attempt_manager.record_failure(media_id, 4, "boom")
        attempt_manager.clear(media_id, 4)
        attempts = attempt_manager.read_for_media(media_id)
        assert all(a.profile_id != 4 for a in attempts)

    def test_prune_for_missing_profiles(self, media_id):
        attempt_manager.record_failure(media_id, 91, "e")
        attempt_manager.record_failure(media_id, 92, "e")
        pruned = attempt_manager.prune_for_missing_profiles({1, 2, 3, 92})
        assert pruned >= 1
        remaining = {
            a.profile_id for a in attempt_manager.read_for_media(media_id)
        }
        assert 91 not in remaining
        assert 92 in remaining


class TestBackoffEligibility:

    def _attempt(self, count: int, hours_ago: float) -> DownloadAttemptRead:
        return DownloadAttemptRead(
            id=1,
            media_id=1,
            profile_id=1,
            attempt_count=count,
            last_attempt_at=datetime.now(timezone.utc)
            - timedelta(hours=hours_ago),
        )

    def test_no_attempt_row_is_eligible(self):
        assert is_eligible(None) is True

    def test_backoff_ladder(self):
        # attempts → delay days: 1→1, 2→2, 3→4, 4→7 (cap), 10→7 (cap)
        for count, days in [(1, 1), (2, 2), (3, 4), (4, 7), (10, 7)]:
            attempt = self._attempt(count, hours_ago=0)
            expected = attempt.last_attempt_at + timedelta(days=days)
            assert next_eligible_at(attempt) == expected, count

    def test_eligible_after_backoff_elapses(self):
        assert is_eligible(self._attempt(1, hours_ago=25)) is True
        assert is_eligible(self._attempt(1, hours_ago=23)) is False
        assert is_eligible(self._attempt(4, hours_ago=7 * 24 + 1)) is True
        assert is_eligible(self._attempt(4, hours_ago=6 * 24)) is False
