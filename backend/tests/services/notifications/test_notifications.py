"""Tests for notification channels (manager + dispatcher) —
plans/track-apprise-notifications.md wargame scenarios."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import database.manager.notificationchannel as channel_manager
from database.models.notificationchannel import (
    NotificationChannelCreate,
    mask_apprise_url,
)
from services.notifications import dispatcher
from services.notifications.dispatcher import EventNote


@pytest.fixture(autouse=True)
def clean_channels_and_queue():
    for channel in channel_manager.read_all():
        channel_manager.delete(channel.id)
    dispatcher._queue.clear()
    dispatcher._send_times.clear()
    yield
    dispatcher._queue.clear()
    dispatcher._send_times.clear()


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
        """W2: an event storm produces ONE send per channel (Discord
        channels route through the native webhook path)."""
        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        for i in range(500):
            dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, f"yt{i}")

        with patch.object(
            dispatcher, "_post_discord_sync", return_value=True
        ) as send:
            await dispatcher._dispatch_pending()

        assert send.call_count == 1
        body = send.call_args[0][1]["embeds"][0]["description"]
        assert "…and 490 more" in body
        assert len(body.splitlines()) == 11  # 10 lines + overflow summary

    @pytest.mark.asyncio
    async def test_apprise_path_used_for_non_discord(self):
        """W2 for the generic path: non-Discord channels still go
        through Apprise's _send_sync."""
        make_channel(
            name="generic",
            url="json://localhost/notify",
            event_types=["TRAILER_DOWNLOADED"],
        )
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "yt0")
        with patch.object(dispatcher, "_send_sync", return_value=True) as send:
            await dispatcher._dispatch_pending()
        assert send.call_count == 1
        assert "Trailer Downloaded — yt0" in send.call_args[0][2]

    @pytest.mark.asyncio
    async def test_send_failure_never_raises(self):
        """W1: a dead webhook must not break dispatch (or the caller)."""
        make_channel(name="dead", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "x")
        with patch.object(
            dispatcher, "_post_discord_sync", side_effect=RuntimeError("boom")
        ):
            await dispatcher._dispatch_pending()  # must not raise

    @pytest.mark.asyncio
    async def test_unsubscribed_events_send_nothing(self):
        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.enqueue("MEDIA_ADDED", "SYSTEM", None, "")
        with (
            patch.object(dispatcher, "_send_sync", return_value=True) as send,
            patch.object(
                dispatcher, "_post_discord_sync", return_value=True
            ) as post,
        ):
            await dispatcher._dispatch_pending()
        assert send.call_count == 0
        assert post.call_count == 0

    @pytest.mark.asyncio
    async def test_no_channels_no_sends(self):
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "")
        with (
            patch.object(dispatcher, "_send_sync", return_value=True) as send,
            patch.object(
                dispatcher, "_post_discord_sync", return_value=True
            ) as post,
        ):
            await dispatcher._dispatch_pending()
        assert send.call_count == 0
        assert post.call_count == 0

    @pytest.mark.asyncio
    async def test_rate_limit_holds_queue_for_next_batch(self):
        """At MAX_SENDS_PER_MINUTE recent sends, a cycle sends nothing and
        leaves the queue intact so notes merge into the next allowed batch."""
        import time

        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "held")
        now = time.monotonic()
        dispatcher._send_times.extend(
            now - i for i in range(dispatcher.MAX_SENDS_PER_MINUTE)
        )
        with patch.object(
            dispatcher, "_post_discord_sync", return_value=True
        ) as send:
            await dispatcher._dispatch_pending()
        assert send.call_count == 0
        assert len(dispatcher._queue) == 1

        # Once the oldest stamp ages past a minute, the held note goes out
        dispatcher._send_times.clear()
        dispatcher._send_times.extend(
            now - 61 for _ in range(dispatcher.MAX_SENDS_PER_MINUTE)
        )
        with patch.object(
            dispatcher, "_post_discord_sync", return_value=True
        ) as send:
            await dispatcher._dispatch_pending()
        assert send.call_count == 1
        assert len(dispatcher._queue) == 0

    @pytest.mark.asyncio
    async def test_forced_flush_bypasses_rate_limit(self):
        """Shutdown flush must never drop notes to the rate cap."""
        import time

        make_channel(name="downloads", event_types=["TRAILER_DOWNLOADED"])
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", None, "held")
        dispatcher._send_times.extend(
            time.monotonic() for _ in range(dispatcher.MAX_SENDS_PER_MINUTE)
        )
        with patch.object(
            dispatcher, "_post_discord_sync", return_value=True
        ) as send:
            await dispatcher._dispatch_pending(force=True)
        assert send.call_count == 1

    def test_enqueue_never_raises(self):
        """The event-creation hook depends on this being un-crashable."""
        dispatcher.enqueue("ANYTHING", "SYSTEM", None, "")

    def test_format_batch_lines(self):
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", None, "abc123"),
            EventNote("MEDIA_ADDED", "SYSTEM", None, ""),
        ]
        body = dispatcher._format_batch(notes, {})
        assert "Trailer Downloaded — abc123" in body
        assert "Media Added" in body


def _fake_media(**overrides):
    base = dict(
        id=7,
        title="Test Movie",
        year=2024,
        youtube_trailer_id="ytabc123",
        poster_path="/images/movies/posters/x.jpg",
        poster_url=None,
        arr_id=0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestEnrichedNotifications:
    """Lines carry year/id/YouTube link; posters attach only when a batch
    is about exactly one media item."""

    def test_lines_include_year_id_and_youtube_link(self):
        with patch.object(
            dispatcher.media_manager, "read", return_value=_fake_media()
        ):
            body = dispatcher._format_batch(
                [EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, "1080p")], {}
            )
        assert "Trailer Downloaded: Test Movie (2024) [#7] — 1080p" in body
        assert "[YouTube](https://www.youtube.com/watch?v=ytabc123)" in body

    def test_no_youtube_link_without_trailer_id(self):
        with patch.object(
            dispatcher.media_manager,
            "read",
            return_value=_fake_media(youtube_trailer_id=None),
        ):
            body = dispatcher._format_batch(
                [EventNote("MEDIA_ADDED", "SYSTEM", 7, "")], {}
            )
        assert "Media Added: Test Movie (2024) [#7]" in body
        assert "YouTube" not in body

    def test_failed_media_lookup_keeps_fallback_label(self):
        with patch.object(
            dispatcher.media_manager,
            "read",
            side_effect=RuntimeError("gone"),
        ):
            body = dispatcher._format_batch(
                [EventNote("MEDIA_ADDED", "SYSTEM", 42, "")], {}
            )
        assert "Media Added: media [42]" in body

    def test_poster_attached_for_single_media_batch(self, tmp_path):
        poster = tmp_path / "poster.jpg"
        poster.write_bytes(b"jpg")
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, ""),
            EventNote("MEDIA_UPDATED", "SYSTEM", 7, ""),
        ]
        with (
            patch.object(
                dispatcher.media_manager, "read", return_value=_fake_media()
            ),
            patch("services.images.image._url_to_fs_path", return_value=poster),
        ):
            assert dispatcher._poster_attachment(notes, {}) == str(poster)

    def test_no_poster_for_multi_media_batch(self):
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, ""),
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", 8, ""),
        ]
        assert dispatcher._poster_attachment(notes, {}) is None

    def test_no_poster_when_file_missing(self, tmp_path):
        notes = [EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, "")]
        with (
            patch.object(
                dispatcher.media_manager, "read", return_value=_fake_media()
            ),
            patch(
                "services.images.image._url_to_fs_path",
                return_value=tmp_path / "nope.jpg",
            ),
        ):
            assert dispatcher._poster_attachment(notes, {}) is None

    @pytest.mark.asyncio
    async def test_apprise_dispatch_passes_poster_to_send(self, tmp_path):
        poster = tmp_path / "poster.jpg"
        poster.write_bytes(b"jpg")
        make_channel(
            name="generic",
            url="json://localhost/notify",
            event_types=["TRAILER_DOWNLOADED"],
        )
        dispatcher.enqueue("TRAILER_DOWNLOADED", "SYSTEM", 7, "1080p")
        with (
            patch.object(
                dispatcher.media_manager, "read", return_value=_fake_media()
            ),
            patch("services.images.image._url_to_fs_path", return_value=poster),
            patch.object(
                dispatcher, "_send_sync", return_value=True
            ) as send,
        ):
            await dispatcher._dispatch_pending()
        assert send.call_count == 1
        assert send.call_args[0][3] == str(poster)


class TestDiscordNative:
    """D10: Discord channels get a native embed — media title header,
    Media/Trailer fields, poster inside the embed, footer + timestamp."""

    # Realistic shapes — Apprise validates the id/token format on the
    # pasted-URL form (short placeholders parse as discord:// but not
    # as https://discord.com/api/webhooks/…).
    _ID = "123456789012345678"
    _TOKEN = "abcDEFghiJKLmnoPQRstuVWXyz-1234567890abcdefghij"

    def test_webhook_url_from_discord_scheme(self):
        assert dispatcher._discord_webhook_url(
            f"discord://{self._ID}/{self._TOKEN}"
        ) == f"https://discord.com/api/webhooks/{self._ID}/{self._TOKEN}"

    def test_webhook_url_from_pasted_discord_url(self):
        url = f"https://discord.com/api/webhooks/{self._ID}/{self._TOKEN}"
        assert dispatcher._discord_webhook_url(url) == url

    def test_webhook_url_none_for_other_services(self):
        assert dispatcher._discord_webhook_url("json://localhost/x") is None

    def test_single_media_payload(self, tmp_path):
        poster_file = tmp_path / "poster.jpg"
        poster_file.write_bytes(b"jpg")
        notes = [EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, "1080p")]
        with (
            patch.object(
                dispatcher.media_manager, "read", return_value=_fake_media()
            ),
            patch(
                "services.images.image._url_to_fs_path",
                return_value=poster_file,
            ),
        ):
            payload, poster = dispatcher._discord_payload(notes, {})
        assert poster == str(poster_file)
        embed = payload["embeds"][0]
        assert embed["title"] == "Test Movie (2024)"
        assert "⬇️ Trailer Downloaded — 1080p" in embed["description"]
        assert embed["image"] == {"url": "attachment://poster.jpg"}
        assert {"name": "Media", "value": "#7", "inline": True} in (
            embed["fields"]
        )
        assert any(
            "youtube.com/watch?v=ytabc123" in f["value"]
            for f in embed["fields"]
        )
        assert embed["footer"]["text"] == "Trailarr"
        assert "timestamp" in embed
        assert embed["color"] == dispatcher._COLOR_GREEN
        assert payload["username"] == "Trailarr"
        # Mobile push previews only show top-level content — without it
        # a poster-attachment message notifies as just "image received"
        assert payload["content"] == (
            "⬇️ Trailer Downloaded: Test Movie (2024)"
        )

    def test_single_media_multi_note_content_lists_event_types(
        self, tmp_path
    ):
        poster_file = tmp_path / "poster.jpg"
        poster_file.write_bytes(b"jpg")
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, ""),
            EventNote("MEDIA_RENAMED", "SYSTEM", 7, ""),
        ]
        with (
            patch.object(
                dispatcher.media_manager, "read", return_value=_fake_media()
            ),
            patch(
                "services.images.image._url_to_fs_path",
                return_value=poster_file,
            ),
        ):
            payload, _ = dispatcher._discord_payload(notes, {})
        assert payload["content"] == (
            "Test Movie (2024): Trailer Downloaded, Media Renamed"
        )

    def test_arr_media_uses_public_poster_url_and_no_content(self):
        """Radarr-style: Arr media has a public TMDB poster URL, so the
        poster goes in the embed by URL (no upload) and no content line is
        needed — mobile push falls back to the embed title/description."""
        media = _fake_media(
            arr_id=101,
            poster_url="https://image.tmdb.org/t/p/original/x.jpg",
        )
        notes = [EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, "1080p")]
        with patch.object(
            dispatcher.media_manager, "read", return_value=media
        ):
            payload, poster = dispatcher._discord_payload(notes, {})
        assert poster is None
        assert payload["embeds"][0]["image"] == {
            "url": "https://image.tmdb.org/t/p/original/x.jpg"
        }
        assert "content" not in payload

    def test_plex_only_media_falls_back_to_poster_upload(self, tmp_path):
        """Plex-only media's poster_url points at the LAN server, which
        Discord can't fetch — upload the cached poster instead and keep
        the content line so mobile push doesn't say 'image received'."""
        poster_file = tmp_path / "poster.jpg"
        poster_file.write_bytes(b"jpg")
        media = _fake_media(
            arr_id=0, poster_url="http://192.168.1.5:32400/thumb/1"
        )
        notes = [EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, "")]
        with (
            patch.object(
                dispatcher.media_manager, "read", return_value=media
            ),
            patch(
                "services.images.image._url_to_fs_path",
                return_value=poster_file,
            ),
        ):
            payload, poster = dispatcher._discord_payload(notes, {})
        assert poster == str(poster_file)
        assert payload["embeds"][0]["image"] == {
            "url": "attachment://poster.jpg"
        }
        assert payload["content"] == (
            "⬇️ Trailer Downloaded: Test Movie (2024)"
        )

    def test_multi_media_payload_stays_compact(self):
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", 7, ""),
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", 8, ""),
        ]
        with patch.object(
            dispatcher.media_manager, "read", return_value=_fake_media()
        ):
            payload, poster = dispatcher._discord_payload(notes, {})
        assert poster is None
        embed = payload["embeds"][0]
        assert embed["title"] == "Trailarr — 2 updates"
        assert "image" not in embed
        assert "fields" not in embed
        assert payload["content"] == (
            "Test Movie — Trailer Downloaded;"
            " Test Movie — Trailer Downloaded"
        )

    def test_multi_media_content_truncates_after_two(self):
        notes = [
            EventNote("TRAILER_DOWNLOADED", "SYSTEM", i, "")
            for i in range(1, 6)
        ]
        with patch.object(
            dispatcher.media_manager, "read", return_value=_fake_media()
        ):
            payload, _ = dispatcher._discord_payload(notes, {})
        assert payload["content"] == (
            "Test Movie — Trailer Downloaded;"
            " Test Movie — Trailer Downloaded; …and 3 more"
        )

    def test_post_uploads_poster_multipart(self, tmp_path):
        poster = tmp_path / "poster.jpg"
        poster.write_bytes(b"jpg")
        resp = MagicMock(status_code=200)
        with patch("requests.post", return_value=resp) as post:
            ok = dispatcher._post_discord_sync(
                "https://discord.com/api/webhooks/id/token",
                {"embeds": []},
                str(poster),
            )
        assert ok
        assert "files" in post.call_args.kwargs
        sent = json.loads(post.call_args.kwargs["data"]["payload_json"])
        assert sent == {"embeds": []}


class TestBranding:
    """Outgoing messages are branded as Trailarr (avatar/icon), and Discord
    defaults to markdown embeds so [YouTube](…) links render. No network:
    requests.post is intercepted."""

    def test_discord_payload_has_trailarr_avatar_and_embed(self):
        resp = MagicMock(status_code=200, content=b"", headers={})
        with patch("requests.post", return_value=resp) as post:
            ok = dispatcher._send_sync(
                "discord://fakewebhookid/fakewebhooktoken",
                "Trailarr",
                "Trailer Downloaded — [YouTube](https://youtu.be/x)",
            )
        assert ok
        raw = post.call_args.kwargs.get("data") or post.call_args.args[1]
        payload = json.loads(raw)
        assert payload["avatar_url"].endswith("trailarr-192.png")
        embed = payload["embeds"][0]
        assert embed["author"]["name"] == "Trailarr"
        assert "[YouTube](https://youtu.be/x)" in embed["description"]


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

        with patch.object(
            dispatcher, "_post_discord_sync", return_value=True
        ) as send:
            await dispatcher.stop()  # no `await asyncio.sleep(0)` first

        assert send.call_count == 1
        assert "race-note" in send.call_args[0][1]["embeds"][0]["description"]
        assert list(dispatcher._queue) == []

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self):
        dispatcher.start()
        await dispatcher.stop()
        await dispatcher.stop()  # must not raise

    @pytest.mark.asyncio
    async def test_stop_without_start_is_a_noop(self):
        await dispatcher.stop()  # must not raise
