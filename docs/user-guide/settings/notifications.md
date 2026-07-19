# Notifications

Trailarr can send notifications to your favorite services using [Apprise](https://github.com/caronc/apprise) — Discord, Telegram, Slack, email, Pushover, ntfy, Gotify and [100+ others](https://appriseit.com/services/).

Set them up under **Settings → Notifications**.

## Adding a channel

1. Click **Add Channel**.
2. Give it a **name** (e.g. `Discord — downloads`).
3. Paste the **Apprise URL** for your service. Examples:

    | Service | URL format |
    |---|---|
    | Discord | `discord://webhook_id/webhook_token` |
    | Telegram | `tgram://bot_token/chat_id` |
    | Slack | `slack://TokenA/TokenB/TokenC` |
    | Email | `mailto://user:pass@gmail.com` |
    | ntfy | `ntfy://topic` |

    See the [Apprise services list](https://appriseit.com/services/) for every supported service and its URL format.

4. Pick which **events** the channel should receive — for example, subscribe a `#trailarr-downloads` channel to *Trailer Downloaded* only, right alongside your Radarr/Sonarr/Plex notifications.
5. Click **Save**, then use the **Test** button to send a test message and confirm the setup.

### Setting up a Discord webhook

1. In Discord, open the channel's settings (gear icon) → **Integrations** → **Webhooks** → **New Webhook**.
2. Give the webhook a name and pick the channel it posts to, then click **Copy Webhook URL**.
3. Paste that URL directly into Trailarr as the channel URL — the `https://discord.com/api/webhooks/…` form works as-is, or you can rewrite it as `discord://webhook_id/webhook_token`.

## What the messages look like

**Discord** channels get rich embeds, sent by a Trailarr-branded bot: the media title as the header, the event details, **Media**/**Trailer** fields with a ▶ YouTube link to the trailer, the poster inside the embed, and a color-coded strip (green for downloads, red for deletions/failures). When one message covers many media items (e.g. a library sync), it's a compact summary embed instead — no poster pile-up.

**All other services** receive the same information as text: each line carries the event, the media title, year and id, plus a YouTube link when the media has a trailer. On services that support attachments, single-media notifications also include the poster image.

## Good to know

- **Batching:** bulk operations (library syncs, full scans) can produce many events at once — Trailarr groups them into a single summarized message per channel instead of flooding it.
- **User-initiated events** (your own clicks in the UI) are excluded by default; enable *Include user-initiated events* per channel if you want them.
- **Apprise URLs contain credentials** — Trailarr stores them write-only. They are never shown again after saving (the list shows a masked form like `discord://12ab****`), never appear in logs, and are excluded from any diagnostics output. To change a URL, just paste a new one; leaving the field blank when editing keeps the saved one.
- A failing channel never affects Trailarr's operation — a warning is logged and the app carries on. Use **Test** to diagnose.
