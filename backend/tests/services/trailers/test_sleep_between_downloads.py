"""The wait between two downloads must stop when the job is stopped.

The wait can be 11 minutes, and the `Download Missing Trailers` task spends
most of its time in it. The wait ignored the stop event, so a stop of
Trailarr could not end the job: `shutdown()` gave up on it after its
timeout, and Python then waited for the thread of the job before the
process could exit. `docker stop` ran into its timeout and killed Trailarr.
"""

import threading
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from quiv import JobCancelledError, Quiv

from services.trailers.trailers import utils
from services.trailers.trailers.batch import batch_download_task


class _Clock:
    """A clock that the fake sleep moves forward, so a test of a 2-minute
    wait takes no time."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def _patch_clock(clock: _Clock, sleep=None):
    """Give `utils` the fake clock. Only the module under test sees it, so
    the event loop of the test keeps the real one."""
    return (
        patch.object(
            utils, "time", SimpleNamespace(monotonic=clock.monotonic)
        ),
        patch.object(
            utils, "asyncio", SimpleNamespace(sleep=sleep or clock.sleep)
        ),
    )


@pytest.mark.asyncio
async def test_the_wait_runs_its_full_time_without_a_stop():
    clock = _Clock()
    time_patch, asyncio_patch = _patch_clock(clock)
    with time_patch, asyncio_patch, patch.object(
        utils, "randint", return_value=30
    ):
        await utils.sleep_between_downloads(
            1, MagicMock(), stop_event=threading.Event()
        )

    # 30 seconds of jitter and 120 seconds for the first ten downloads.
    assert sum(clock.slept) == pytest.approx(150)
    assert max(clock.slept) <= utils._POLL_SECONDS


@pytest.mark.asyncio
async def test_the_wait_runs_its_full_time_outside_a_job():
    clock = _Clock()
    time_patch, asyncio_patch = _patch_clock(clock)
    with time_patch, asyncio_patch, patch.object(
        utils, "randint", return_value=0
    ):
        await utils.sleep_between_downloads(1, MagicMock())

    assert sum(clock.slept) == pytest.approx(120)


@pytest.mark.asyncio
async def test_a_stop_during_the_wait_ends_it():
    clock = _Clock()
    stop_event = threading.Event()

    async def sleep(seconds: float) -> None:
        await clock.sleep(seconds)
        if len(clock.slept) == 3:
            stop_event.set()

    time_patch, asyncio_patch = _patch_clock(clock, sleep)
    with time_patch, asyncio_patch, pytest.raises(JobCancelledError):
        await utils.sleep_between_downloads(
            1, MagicMock(), stop_event=stop_event
        )

    # The wait ends at the first check after the stop, not after 2 minutes.
    assert len(clock.slept) == 3


@pytest.mark.asyncio
async def test_a_stop_before_the_wait_skips_it():
    clock = _Clock()
    stop_event = threading.Event()
    stop_event.set()

    time_patch, asyncio_patch = _patch_clock(clock)
    with time_patch, asyncio_patch, pytest.raises(JobCancelledError):
        await utils.sleep_between_downloads(
            1, MagicMock(), stop_event=stop_event
        )

    assert clock.slept == []


def test_shutdown_ends_a_batch_that_waits_between_downloads():
    """The real path: a quiv job in the wait after its first download,
    then the shutdown that the lifespan in main.py runs on a stop.

    Before the fix, the shutdown gave up after its timeout and the job
    kept its thread for 2 more minutes. That thread kept the process
    alive after uvicorn returned.
    """
    profile = MagicMock()
    profile.video_type = "trailer"
    profile.retry_count = 0
    media_list = [MagicMock(id=1, title="One"), MagicMock(id=2, title="Two")]
    first_download = threading.Event()
    finished = threading.Event()
    outcome: list[BaseException | None] = []

    async def download_trailer(*args, **kwargs) -> bool:
        first_download.set()
        return True

    async def job(stop_event: threading.Event) -> None:
        try:
            await batch_download_task(
                media_list, profile, stop_event=stop_event
            )
            outcome.append(None)
        except BaseException as e:
            outcome.append(e)
            raise
        finally:
            finished.set()

    scheduler = Quiv()
    with patch(
        "services.trailers.trailers.batch.download_trailer",
        new=AsyncMock(side_effect=download_trailer),
    ):
        scheduler.add_task(
            task_name="Wait between downloads", func=job, run_once=True
        )
        scheduler.start()
        try:
            assert first_download.wait(timeout=10)
            # Give the job time to enter the wait.
            time.sleep(0.2)
        finally:
            started = time.monotonic()
            scheduler.shutdown(timeout=4)
            elapsed = time.monotonic() - started

    assert finished.is_set(), "the shutdown abandoned the job in its wait"
    assert elapsed < 2
    assert len(outcome) == 1 and isinstance(outcome[0], JobCancelledError)
