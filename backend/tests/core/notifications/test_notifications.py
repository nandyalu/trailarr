"""Tests for notification channels (manager + dispatcher) —
plans/track-apprise-notifications.md wargame scenarios."""

from unittest.mock import patch

import pytest

import core.base.database.manager.notificationchannel as channel_manager
from core.base.database.models.notificationchannel import (
    NotificationChannelCreate,
    mask_apprise_url,
)
from core.notifications import dispatcher
from core.notifications.dispatcher import EventNote


@pytest.fixture(autouse=True)
def clean_channels_and_queue():
    for channel in channel_manager.read_all():
        channel_manager.delete(channel.id)
    dispatcher._queue.clear()
    yield
    dispatcher._queue.clear()


def make_channel(
    name: str = "Discord",
    url: str = "discord://tokenA/tokenB",
    event_types: list[str] | None = None,
    include_user_events: bool = False,
    enabled: bool = True,
):
    return channel_manager.create(
        NotificationChannelCreate(
            name=name,
            url=url,
            enabled=enabled,
            event_types=(
                event_types
                if event_types is not None
                else ["TRAILER_DOWNLOADED"]
            ),
            include_user_events=include_user_events,
        )
    )


class TestChannelManager:

    def test_create_masks_url_in_reads(self):
        channel = make_channel()
        assert channel.url_masked == "discord://toke****"
        assert "tokenB" not in str(channel.model_dump())
        listed = channel_manager.read_all()[0]
        assert "tokenB" not in str(listed.model_dump())

    def test_create_without_url_rejected(self):
        with pytest.raises(ValueError):
            make_channel(url="")

    def test_update_blank_url_keeps_stored_one(self):
        channel = make_channel()
        updated = channel_manager.update(
            channel.id,
            NotificationChannelCreate(
                name="Discord renamed", url="", event_types=["MEDIA_ADDED"]
            ),
        )
        assert updated.name == "Discord renamed"
        assert channel_manager.get_url(channel.id) == "discord://tokenA/tokenB"

    def test_update_with_url_replaces(self):
        channel = make_channel()
        channel_manager.update(
            channel.id,
            NotificationChannelCreate(
                name="Discord", url="tgram://new/token"
            ),
        )
        assert channel_manager.get_url(channel.id) == "tgram://new/token"

    def test_subscribed_channels_filters(self):
        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        make_channel(
            name="everything",
            event_types=["TRAILER_DOWNLOADED", "MEDIA_ADDED"],
            include_user_events=True,
        )
        make_channel(name="disabled", enabled=False)

        system_dl = channel_manager.subscribed_channels(
            "TRAILER_DOWNLOADED", is_user_event=False
        )
        assert {name for name, _ in _names(system_dl)} == {
            "downloads",
            "everything",
        }
        # User-sourced events only reach channels that opted in
        user_dl = channel_manager.subscribed_channels(
            "TRAILER_DOWNLOADED", is_user_event=True
        )
        assert {name for name, _ in _names(user_dl)} == {"everything"}
        # Unsubscribed type reaches nobody
        assert (
            channel_manager.subscribed_channels(
                "TRAILER_DELETED", is_user_event=False
            )
            == []
        )


def _names(pairs):
    """Map (channel_id, url) → (name, url) for readable asserts."""
    by_id = {c.id: c.name for c in channel_manager.read_all()}
    return [(by_id[cid], url) for cid, url in pairs]


class TestMaskUrl:

    def test_masks_token_tail(self):
        assert mask_apprise_url("discord://abcdef/ghij") == "discord://abcd****"

    def test_handles_schemeless(self):
        assert mask_apprise_url("garbage") == "****"


class TestDispatcher:

    @pytest.mark.asyncio
    async def test_batch_sends_one_message_per_channel(self):
        """W2: an event storm produces ONE Apprise send per channel."""
        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        for i in range(500):
            dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, f"yt{i}")

        with patch.object(dispatcher, "_send_sync", return_value=True) as send:
            await dispatcher._dispatch_pending()

        assert send.call_count == 1
        body = send.call_args[0][2]
        assert "…and 490 more" in body
        assert len(body.splitlines()) == 11  # 10 lines + overflow summary

    @pytest.mark.asyncio
    async def test_send_failure_never_raises(self):
        """W1: a dead webhook must not break dispatch (or the caller)."""
        make_channel(name="dead", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "x")
        with patch.object(
            dispatcher, "_send_sync", side_effect=RuntimeError("boom")
        ):
            await dispatcher._dispatch_pending()  # must not raise

    @pytest.mark.asyncio
    async def test_unsubscribed_events_send_nothing(self):
        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.enqueue("MEDIA_ADDED", "SYSTEM", None, "")
        with patch.object(dispatcher, "_send_sync", return_value=True) as send:
            await dispatcher._dispatch_pending()
        assert send.call_count == 0

    @pytest.mark.asyncio
    async def test_no_channels_no_sends(self):
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "")
        with patch.object(dispatcher, "_send_sync", return_value=True) as send:
            await dispatcher._dispatch_pending()
        assert send.call_count == 0

    def test_enqueue_never_raises(self):
        """The event-creation hook depends on this being un-crashable."""
        dispatcher.enqueue("ANYTHING", "SYSTEM", None, "")

    def test_format_batch_lines(self):
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", None, "abc123"),
            EventNote("MEDIA_ADDED", "SYSTEM", None, ""),
        ]
        body = dispatcher._format_batch(notes)
        assert "Trailer Downloaded — abc123" in body
        assert "Media Added" in body


class TestDispatcherLifecycle:
    """Copilot review (PR #619): stop() must flush pending notes even if the
    stop event races ahead of the loop's first iteration."""

    def teardown_method(self):
        # Belt-and-braces: never leak a running task into the next test
        dispatcher._dispatch_task = None
        dispatcher._stop_event = None

    @pytest.mark.asyncio
    async def test_start_uses_running_loop(self):
        dispatcher.start()
        assert dispatcher._dispatch_task is not None
        await dispatcher.stop()
        assert dispatcher._dispatch_task is None

    @pytest.mark.asyncio
    async def test_stop_before_first_iteration_still_flushes(self):
        """The exact race Copilot flagged: stop() called before the
        scheduled task has run its first loop iteration must not drop
        queued notes."""
        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.start()
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "race-note")

        with patch.object(dispatcher, "_send_sync", return_value=True) as send:
            await dispatcher.stop()  # no `await asyncio.sleep(0)` first

        assert send.call_count == 1
        assert "race-note" in send.call_args[0][2]
        assert list(dispatcher._queue) == []

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self):
        dispatcher.start()
        await dispatcher.stop()
        await dispatcher.stop()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_without_start_is_a_noop(self):
        await dispatcher.stop()  # must not raise
