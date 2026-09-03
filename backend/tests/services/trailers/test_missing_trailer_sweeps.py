"""Behavior tests for sweep-based missing-trailer downloads."""

import datetime
import threading
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models.download import DownloadRead
from database.models.downloadattempt import DownloadAttemptRead
from database.models.media import MediaRead
from services.satisfaction import SatisfactionResult
from services.trailers.trailers.missing import (
    _process_single_media_item,
    download_missing_trailers,
)
from exceptions import ItemNotFoundError


def _media(
    media_id: int,
    *,
    monitor: bool = True,
    downloads: list[DownloadRead] | None = None,
) -> MediaRead:
    now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    return MediaRead(
        id=media_id,
        connection_id=1,
        arr_id=media_id,
        is_movie=True,
        title=f"Movie {media_id}",
        clean_title=f"movie {media_id}",
        year=2024,
        language="en",
        studio="Test Studio",
        txdb_id=str(media_id),
        title_slug=f"movie-{media_id}",
        monitor=monitor,
        arr_monitored=True,
        media_exists=True,
        media_filename=f"movie-{media_id}.mkv",
        folder_path=f"/media/movie-{media_id}",
        season_count=0,
        runtime=120,
        added_at=now,
        updated_at=now,
        downloaded_at=None,
        downloads=downloads or [],
    )


def _download(media_id: int, profile_id: int) -> DownloadRead:
    now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    return DownloadRead(
        id=media_id * 100 + profile_id,
        media_id=media_id,
        path=f"/trailers/{media_id}-{profile_id}.mkv",
        file_name=f"{media_id}-{profile_id}.mkv",
        file_hash="hash",
        size=1,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        profile_id=profile_id,
        file_exists=True,
        added_at=now,
        updated_at=now,
    )


def _profile(
    profile_id: int,
    *,
    enabled: bool = True,
    resolution: int = 1080,
) -> MagicMock:
    profile = MagicMock()
    profile.id = profile_id
    profile.enabled = enabled
    profile.priority = profile_id
    profile.video_resolution = resolution
    profile.custom_folder = "{media_folder}"
    profile.customfilter.filter_name = f"Profile {profile_id}"
    profile.customfilter.filters = []
    return profile


def _attempt(media_id: int, profile_id: int) -> DownloadAttemptRead:
    return DownloadAttemptRead(
        id=media_id * 100 + profile_id,
        media_id=media_id,
        profile_id=profile_id,
        attempt_count=1,
        last_attempt_at=datetime.datetime.now(datetime.timezone.utc),
        last_error="failed",
    )


@pytest.fixture
def sweep_harness():
    """Patch external state while keeping the real sweep decisions."""
    state = {
        "library": [],
        "current_media": {},
        "profiles": [],
    }

    def generate_media(monitored_only=False):
        yield from state["library"]

    def read_media(media_id):
        media = state["current_media"].get(media_id)
        if media is None:
            raise ItemNotFoundError("Media", media_id)
        return media

    with ExitStack() as stack:
        settings = stack.enter_context(
            patch("services.trailers.trailers.missing.app_settings")
        )
        stack.enter_context(
            patch(
                "services.trailers.trailers.missing.downloads_ready",
                return_value=True,
            )
        )
        attempts = stack.enter_context(
            patch("services.trailers.trailers.missing.attempt_manager")
        )
        media_generator = stack.enter_context(
            patch(
                "services.trailers.trailers.missing.media_manager.read_all_generator",
                side_effect=generate_media,
            )
        )
        media_read = stack.enter_context(
            patch(
                "services.trailers.trailers.missing.media_manager.read",
                side_effect=read_media,
            )
        )
        profiles = stack.enter_context(
            patch("services.trailers.trailers.missing.trailerprofile")
        )
        process = stack.enter_context(
            patch(
                "services.trailers.trailers.missing._process_single_media_item",
                new_callable=AsyncMock,
                return_value=(1, 0, 1),
            )
        )

        settings.monitor_enabled = True
        settings.downloads_enabled = True
        attempts.prune_for_missing_profiles.return_value = 0
        attempts.read_all.return_value = []
        attempts.read_for_media.return_value = []
        profiles.get_trailerprofiles.side_effect = lambda: list(
            state["profiles"]
        )
        yield SimpleNamespace(
            state=state,
            attempts=attempts,
            media_generator=media_generator,
            media_read=media_read,
            process=process,
        )


def _load(harness, media_items, profiles):
    harness.state["library"] = list(media_items)
    harness.state["current_media"] = {media.id: media for media in media_items}
    harness.state["profiles"] = list(profiles)


@pytest.mark.asyncio
async def test_multiple_profiles_are_processed_once_each(sweep_harness):
    """One media item receives every unsatisfied matching profile at once.

    The whole media item is handed over in a single call. Calling once per
    profile would repeat the folder and storage validation, and its skip
    events, for every profile."""
    media = _media(1)
    _load(sweep_harness, [media], [_profile(1), _profile(2)])
    handed_over = []

    async def process(media, profiles, *args, **kwargs):
        handed_over.append(
            (media.id, sorted(profile.id for profile in profiles))
        )
        return 1, 0, 1

    sweep_harness.process.side_effect = process

    await download_missing_trailers()

    assert handed_over == [(1, [1, 2])]
    assert sweep_harness.media_generator.call_count == 2


@pytest.mark.asyncio
async def test_profile_enabled_mid_sweep_is_caught_in_same_run(sweep_harness):
    """A new profile reaches later items and an earlier item in sweep two."""
    media_one = _media(1)
    media_two = _media(2)
    profile_one = _profile(1)
    profile_two = _profile(2)
    _load(sweep_harness, [media_one, media_two], [profile_one])
    processed_pairs = []

    async def process(media, profiles, *args, **kwargs):
        processed_pairs.append(
            (media.id, sorted(profile.id for profile in profiles))
        )
        if len(processed_pairs) == 1:
            sweep_harness.state["profiles"].append(profile_two)
        return 1, 0, 1

    sweep_harness.process.side_effect = process

    await download_missing_trailers()

    # Media 2 picks the new profile up at its own re-verify; media 1 was
    # already past, so sweep two catches it via the unconsumed pair.
    assert processed_pairs == [(1, [1]), (2, [1, 2]), (1, [2])]
    assert sweep_harness.media_generator.call_count == 3


@pytest.mark.asyncio
async def test_profile_is_re_read_before_each_awaited_download(sweep_harness):
    """A later media item uses settings edited during an earlier download.

    Profiles are resolved once per media item, immediately before that
    item's download, so an edit made mid-run reaches every item that has
    not started yet."""
    old_profile = _profile(1, resolution=1080)
    new_profile = _profile(1, resolution=2160)
    _load(sweep_harness, [_media(1), _media(2)], [old_profile])
    used_profiles = []

    async def process(media, profiles, *args, **kwargs):
        used_profiles.append((media.id, profiles[0]))
        if media.id == 1:
            sweep_harness.state["profiles"] = [new_profile]
        return 1, 0, 1

    sweep_harness.process.side_effect = process

    await download_missing_trailers()

    assert [media_id for media_id, _ in used_profiles] == [1, 2]
    assert used_profiles[0][1] is old_profile
    assert used_profiles[1][1] is new_profile
    assert used_profiles[1][1].video_resolution == 2160


@pytest.mark.asyncio
async def test_narrowed_profile_filter_drops_later_media(sweep_harness):
    """A profile filter edit applies before a later download starts."""
    media_one = _media(1)
    media_two = _media(2)
    profile = _profile(1)
    profile.allowed_media_ids = {1, 2}
    _load(sweep_harness, [media_one, media_two], [profile])

    def find_matching(media, profiles):
        return [
            item for item in profiles if media.id in item.allowed_media_ids
        ]

    async def process(*args, **kwargs):
        profile.allowed_media_ids = {1}
        return 1, 0, 1

    sweep_harness.process.side_effect = process
    with patch(
        "services.trailers.trailers.missing.find_matching_profiles",
        side_effect=find_matching,
    ):
        await download_missing_trailers()

    assert sweep_harness.process.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("delete_profile", [False, True])
async def test_disabled_or_deleted_profile_stops_later_downloads(
    sweep_harness, delete_profile
):
    """A disabled or deleted profile does not use its stale work list."""
    media_one = _media(1)
    media_two = _media(2)
    profile = _profile(1)
    _load(sweep_harness, [media_one, media_two], [profile])

    async def process(*args, **kwargs):
        if delete_profile:
            sweep_harness.state["profiles"] = []
        else:
            profile.enabled = False
        return 1, 0, 1

    sweep_harness.process.side_effect = process

    await download_missing_trailers()

    assert sweep_harness.process.await_count == 1


@pytest.mark.asyncio
async def test_unmonitored_media_is_dropped_at_reverification(sweep_harness):
    """An item unmonitored after the scan is not downloaded."""
    scanned_media = _media(1)
    _load(sweep_harness, [scanned_media], [_profile(1)])
    sweep_harness.state["current_media"][1] = _media(1, monitor=False)

    await download_missing_trailers()

    sweep_harness.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_deleted_media_is_dropped_at_reverification(sweep_harness):
    """An item deleted after the scan does not fail the sweep."""
    scanned_media = _media(1)
    _load(sweep_harness, [scanned_media], [_profile(1)])
    sweep_harness.state["current_media"].clear()

    await download_missing_trailers()

    sweep_harness.process.assert_not_awaited()
    assert sweep_harness.media_generator.call_count == 2


@pytest.mark.asyncio
async def test_manual_download_satisfies_stale_work_item(sweep_harness):
    """A manual download after the scan prevents a duplicate download."""
    scanned_media = _media(1)
    _load(sweep_harness, [scanned_media], [_profile(1)])
    sweep_harness.state["current_media"][1] = _media(
        1, downloads=[_download(1, 1)]
    )

    await download_missing_trailers()

    sweep_harness.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_media_added_mid_run_is_caught_by_next_sweep(sweep_harness):
    """An Arr-style library addition is processed in the same task run."""
    media_one = _media(1)
    media_two = _media(2)
    _load(sweep_harness, [media_one], [_profile(1)])
    processed_ids = []

    async def process(media, *args, **kwargs):
        processed_ids.append(media.id)
        if media.id == 1:
            sweep_harness.state["library"].append(media_two)
            sweep_harness.state["current_media"][2] = media_two
        return 1, 0, 1

    sweep_harness.process.side_effect = process

    await download_missing_trailers()

    assert processed_ids == [1, 2]
    assert sweep_harness.media_generator.call_count == 3


@pytest.mark.asyncio
async def test_backoff_excludes_pair_with_batched_attempt_lookup(
    sweep_harness,
):
    """A recent failure blocks work without a per-media attempt query."""
    media = _media(1)
    _load(sweep_harness, [media], [_profile(1)])
    sweep_harness.attempts.read_all.return_value = [_attempt(1, 1)]

    await download_missing_trailers()

    sweep_harness.process.assert_not_awaited()
    sweep_harness.attempts.read_for_media.assert_not_called()


@pytest.mark.asyncio
async def test_persistent_scan_reverify_disagreement_drains(
    sweep_harness,
):
    """A pair every scan re-proposes, and every re-check rejects, drains.

    The scan and the re-verify read different rows, so they can disagree
    forever. Termination therefore cannot rest on the disagreement ending:
    it rests on the pair being consumed when the item is visited. Remove
    that consume and this test hangs rather than fails, which is what the
    suite-wide timeout is for."""
    scanned_media = _media(1)
    current_media = _media(1)
    profile = _profile(1)
    _load(sweep_harness, [scanned_media], [profile])
    sweep_harness.state["current_media"][1] = current_media

    def evaluate(media, profiles):
        # Unconditional and stateless: the scan's row is always pending,
        # the re-read row is always satisfied, on every sweep.
        if media is scanned_media:
            return SatisfactionResult(unsatisfied=list(profiles))
        return SatisfactionResult()

    with patch(
        "services.trailers.trailers.missing.evaluate_satisfaction",
        side_effect=evaluate,
    ):
        await download_missing_trailers()

    sweep_harness.process.assert_not_awaited()
    # Sweep one proposes and consumes the pair; sweep two finds it already
    # consumed and returns an empty work list.
    assert sweep_harness.media_generator.call_count == 2


@pytest.mark.asyncio
async def test_stop_event_ends_download_phase_promptly(sweep_harness):
    """A stop request after one item prevents later work-list downloads."""
    stop_event = threading.Event()
    media_one = _media(1)
    media_two = _media(2)
    _load(sweep_harness, [media_one, media_two], [_profile(1)])

    async def process(*args, **kwargs):
        stop_event.set()
        return 1, 0, 1

    sweep_harness.process.side_effect = process

    await download_missing_trailers(_stop_event=stop_event)

    assert sweep_harness.process.await_count == 1


@pytest.mark.asyncio
async def test_no_enabled_profiles_does_not_open_generator(sweep_harness):
    """Profile guards run before a database generator is created."""
    media = _media(1)
    _load(sweep_harness, [media], [_profile(1, enabled=False)])

    await download_missing_trailers()

    sweep_harness.media_generator.assert_not_called()
    sweep_harness.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_library_finishes_without_downloads(sweep_harness):
    """An empty configuration builds one empty sweep and terminates."""
    _load(sweep_harness, [], [_profile(1)])

    await download_missing_trailers()

    sweep_harness.process.assert_not_awaited()
    assert sweep_harness.media_generator.call_count == 1


@pytest.mark.asyncio
async def test_download_failure_records_backoff_attempt():
    """A real download failure is recorded for later-run backoff."""
    media = _media(1)
    profile = _profile(1)
    profile.retry_count = 0
    recorded_attempt = _attempt(1, 1)

    with (
        patch(
            "services.trailers.trailers.missing._is_valid_media",
            return_value=True,
        ),
        patch(
            "services.trailers.trailers.missing.trailer_downloader"
            ".download_trailer",
            new_callable=AsyncMock,
            side_effect=RuntimeError("download failed"),
        ),
        patch(
            "services.trailers.trailers.missing.attempt_manager.record_failure",
            return_value=recorded_attempt,
        ) as record_failure,
        patch(
            "services.trailers.trailers.missing.utils.sleep_between_downloads",
            new_callable=AsyncMock,
        ),
    ):
        result = await _process_single_media_item(media, [profile])

    # A real failure reached the network, so it counts as an attempt and
    # advances the delay ladder.
    assert result == (0, 1, 1)
    record_failure.assert_called_once_with(1, 1, "download failed")


@pytest.mark.asyncio
async def test_validation_skip_does_not_record_backoff_attempt():
    """A storage validation skip is not treated as a failed download."""
    media = _media(1)
    profile = _profile(1)

    with (
        patch(
            "services.trailers.trailers.missing._is_valid_media",
            return_value=False,
        ),
        patch(
            "services.trailers.trailers.missing.attempt_manager.record_failure"
        ) as record_failure,
        patch(
            "services.trailers.trailers.missing.trailer_downloader"
            ".download_trailer",
            new_callable=AsyncMock,
        ) as download_trailer,
    ):
        result = await _process_single_media_item(media, [profile])

    # No network call, so no attempt — a library on an offline mount must
    # not push the delay ladder up.
    assert result == (0, 1, 0)
    record_failure.assert_not_called()
    download_trailer.assert_not_awaited()


@pytest.mark.asyncio
async def test_declined_download_is_not_counted_as_an_attempt():
    """A download that declines to run makes no attempt.

    `download_trailer` returns False without a network request when Plex
    already holds the trailer, or when the stop event is set. Neither may
    report a download or advance the delay ladder."""
    media = _media(1)
    profile = _profile(1)
    profile.retry_count = 0

    with (
        patch(
            "services.trailers.trailers.missing._is_valid_media",
            return_value=True,
        ),
        patch(
            "services.trailers.trailers.missing.trailer_downloader"
            ".download_trailer",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "services.trailers.trailers.missing.attempt_manager.record_failure"
        ) as record_failure,
        patch(
            "services.trailers.trailers.missing.utils.sleep_between_downloads",
            new_callable=AsyncMock,
        ) as sleep_between,
    ):
        result = await _process_single_media_item(media, [profile])

    assert result == (0, 0, 0)
    record_failure.assert_not_called()
    sleep_between.assert_not_awaited()


@pytest.mark.asyncio
async def test_validation_skip_is_reported_once_for_the_media_item():
    """An unreachable folder skips the media item, not each profile.

    Events are permanent history in this project, so a library on a
    disconnected mount must not write one skip row per matching profile."""
    media = _media(1)
    profiles = [_profile(1), _profile(2), _profile(3)]

    with (
        patch(
            "services.trailers.trailers.missing._is_valid_media",
            return_value=False,
        ) as is_valid_media,
        patch(
            "services.trailers.trailers.missing.trailer_downloader"
            ".download_trailer",
            new_callable=AsyncMock,
        ) as download_trailer,
    ):
        result = await _process_single_media_item(media, profiles)

    assert result == (0, 1, 0)
    is_valid_media.assert_called_once()
    download_trailer.assert_not_awaited()


@pytest.mark.asyncio
async def test_validation_skip_is_not_reproposed_by_the_next_sweep(
    sweep_harness,
):
    """W11: a skip that records no attempt row still drains the loop.

    Backoff cannot exclude the pair, because a validation skip writes no
    attempt row. Only the consumed-pair set stops the next sweep from
    proposing the same work again."""
    _load(sweep_harness, [_media(1)], [_profile(1)])
    sweep_harness.process.return_value = (0, 1, 0)

    await download_missing_trailers()

    assert sweep_harness.process.await_count == 1
    sweep_harness.attempts.record_failure.assert_not_called()
    assert sweep_harness.media_generator.call_count == 2
