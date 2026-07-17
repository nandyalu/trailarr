"""Phase 3: the in-flight download registry — DOWNLOADING as runtime-only
state (plans/phase-03-dynamic-status.md, design decision 2)."""

import threading

import pytest

from core.download.inflight import InflightRegistry, inflight_registry


@pytest.fixture(autouse=True)
def clean_global_registry():
    inflight_registry.clear()
    yield
    inflight_registry.clear()


class TestInflightRegistry:

    def test_start_and_snapshot(self):
        registry = InflightRegistry()
        registry.start(1, 10)
        registry.start(2, 20)
        assert registry.snapshot() == {1: 10, 2: 20}

    def test_finish_removes_entry(self):
        registry = InflightRegistry()
        registry.start(1, 10)
        registry.finish(1)
        assert registry.snapshot() == {}

    def test_finish_is_idempotent(self):
        registry = InflightRegistry()
        registry.finish(999)  # never started — no error
        assert registry.snapshot() == {}

    def test_restart_overwrites_profile(self):
        """Manual + task overlap on the same media: later start wins."""
        registry = InflightRegistry()
        registry.start(1, 10)
        registry.start(1, 20)
        assert registry.snapshot() == {1: 20}

    def test_clear(self):
        registry = InflightRegistry()
        registry.start(1, 10)
        registry.start(2, 20)
        registry.clear()
        assert registry.snapshot() == {}

    def test_is_downloading(self):
        registry = InflightRegistry()
        registry.start(1, 10)
        assert registry.is_downloading(1)
        assert not registry.is_downloading(2)

    def test_snapshot_is_a_copy(self):
        registry = InflightRegistry()
        registry.start(1, 10)
        snap = registry.snapshot()
        snap[99] = 99
        assert registry.snapshot() == {1: 10}

    def test_thread_safety_under_concurrent_churn(self):
        registry = InflightRegistry()

        def churn(media_id: int):
            for _ in range(500):
                registry.start(media_id, media_id * 10)
                registry.finish(media_id)

        threads = [
            threading.Thread(target=churn, args=(i,)) for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert registry.snapshot() == {}


class TestDownloadingEndpoint:

    @pytest.mark.asyncio
    async def test_returns_inflight_pairs(self):
        from api.v1.media import get_downloading

        inflight_registry.start(5, 3)
        result = await get_downloading()
        assert [(r.media_id, r.profile_id) for r in result] == [(5, 3)]

    @pytest.mark.asyncio
    async def test_empty_when_nothing_in_flight(self):
        """W2: zero in-flight downloads returns an empty list, not an error."""
        from api.v1.media import get_downloading

        assert await get_downloading() == []
