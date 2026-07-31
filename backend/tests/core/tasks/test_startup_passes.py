"""Tests for the startup-pass registry (core/tasks/startup_passes.py) —
plans/README.md "Upgrade-safety rules"."""

from unittest.mock import AsyncMock, patch

import pytest

import core.base.database.manager.startuppass as startuppass_manager
from core.tasks import startup_passes
from core.tasks.startup_passes import (
    DOWNLOADS_REQUIRED_PASSES,
    downloads_ready,
    run_startup_passes,
)

PKG = "core.tasks.startup_passes"


@pytest.fixture(autouse=True)
def clean_registry_records():
    """Each test starts with no completion records (shared test DB)."""
    from sqlmodel import Session, delete

    from core.base.database.models.startuppass import StartupPass
    from core.base.database.utils.engine import engine

    with Session(engine) as session:
        session.exec(delete(StartupPass))  # type: ignore[call-overload]
        session.commit()
    yield


class TestRunStartupPasses:

    @pytest.mark.asyncio
    async def test_all_passes_run_and_recorded_on_fresh_db(self):
        order = []

        async def fake_attr():
            order.append("attribute")

        async def fake_scan_guard():
            order.append("scan-guard")

        with (
            patch(f"{PKG}._pass_attribute_downloads", side_effect=fake_attr),
            patch(f"{PKG}._pass_full_scan_guard", side_effect=fake_scan_guard),
            patch.object(
                startup_passes,
                "REGISTRY",
                [
                    ("attribute-downloads-v0.9.9", fake_attr, "always"),
                    ("full-scan-before-downloads-v0.10", fake_scan_guard, "once"),
                ],
            ),
        ):
            assert downloads_ready() is False
            await run_startup_passes()

        assert order == ["attribute", "scan-guard"]
        assert downloads_ready() is True

    @pytest.mark.asyncio
    async def test_once_pass_skipped_when_recorded_always_reruns(self):
        calls = {"always": 0, "once": 0}

        async def always_pass():
            calls["always"] += 1

        async def once_pass():
            calls["once"] += 1

        registry = [
            ("p-always", always_pass, "always"),
            ("p-once", once_pass, "once"),
        ]
        with patch.object(startup_passes, "REGISTRY", registry):
            await run_startup_passes()
            await run_startup_passes()

        assert calls == {"always": 2, "once": 1}
        assert startuppass_manager.is_completed("p-always")
        assert startuppass_manager.is_completed("p-once")

    @pytest.mark.asyncio
    async def test_failure_stops_remaining_passes_and_records_nothing(self):
        """Order is a dependency guarantee: a failed pass must not let its
        dependents run, and it retries next boot (not recorded)."""
        ran = []

        async def failing():
            ran.append("failing")
            raise RuntimeError("disk exploded")

        async def dependent():
            ran.append("dependent")

        registry = [
            ("p-failing", failing, "once"),
            ("p-dependent", dependent, "once"),
        ]
        with patch.object(startup_passes, "REGISTRY", registry):
            await run_startup_passes()

        assert ran == ["failing"]
        assert not startuppass_manager.is_completed("p-failing")
        assert not startuppass_manager.is_completed("p-dependent")

    @pytest.mark.asyncio
    async def test_version_skipper_runs_all_missed_passes(self):
        """A user jumping several versions has several unrecorded passes —
        all run in order on first boot of the new version."""
        ran = []

        def make(name):
            async def _pass():
                ran.append(name)

            return _pass

        registry = [(f"p-{i}", make(f"p-{i}"), "once") for i in range(4)]
        # Simulate: only the first pass was known/recorded on the old version
        startuppass_manager.mark_completed("p-0")
        with patch.object(startup_passes, "REGISTRY", registry):
            await run_startup_passes()

        assert ran == ["p-1", "p-2", "p-3"]


class TestFullScanGuardPass:

    @pytest.mark.asyncio
    async def test_unrecorded_pass_always_runs_full_scan(self):
        """Phase 5: the stored mirror flags are gone, so there is no cheap
        pre-check anymore — an unrecorded pass runs one full disk scan
        unconditionally (a fresh install has no media, so the scan is a
        no-op there; the "once" policy keeps it from repeating)."""
        with patch(
            "core.tasks.files_scan.scan_all_media_folders",
            new=AsyncMock(),
        ) as mock_scan:
            await startup_passes._pass_full_scan_guard()
        mock_scan.assert_awaited_once()


class TestDownloadsReady:

    def test_requires_all_required_passes(self):
        assert downloads_ready() is False
        for name in DOWNLOADS_REQUIRED_PASSES:
            startuppass_manager.mark_completed(name)
        assert downloads_ready() is True
