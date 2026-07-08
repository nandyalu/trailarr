# Parallel Track — Apprise Notifications

**Status:** not started · **Release:** v0.10.0 (alongside Phase 2) · **Depends on:** nothing
(can be developed any time; independent of the monitor refactor)

## Objective

Users add notification channels (Discord, Telegram, Slack, email — anything
[Apprise](https://github.com/caronc/apprise) supports) and choose which Trailarr events
each channel receives. Canonical use case: a `#trailarr-downloads` Discord channel
subscribed to *Trailer Downloaded*, later a `#trailarr-issues` channel (Phase 11).
Shipping with Phase 2 is deliberate: notifications make the new download engine's
behavior visible during its bake window.

## Design decisions (settled)

1. **Dependency:** `apprise` (pure-python) added to `backend/pyproject.toml` via
   `uv add`. Docker image needs no extra system deps.
2. **Model `NotificationChannel`** (additive migration): `id`, `name` (unique),
   `url` (the Apprise URL — SECRET, see D6), `enabled` (bool, default True),
   `event_types` (JSON list of EventType names; empty = none),
   `include_user_events` (bool, default False — SYSTEM-sourced events only by default,
   so a user clicking around doesn't echo to Discord), `added_at`/`updated_at`.
3. **Dispatch hook:** inside the event manager's `create()`/`create_bulk()` path —
   after DB commit, fire-and-forget an async dispatch (asyncio task) that never raises
   into the caller. A notification failure must NEVER fail or slow event creation.
4. **Flood control (critical):** bulk operations create event storms (Phase 1's
   attribution pass wrote 2,435 events on the maintainer's library; Arr syncs write
   hundreds). Dispatcher aggregates: per channel, buffer events for 30s and send one
   message per batch ("Trailarr: 214 trailers downloaded, 3 skipped — first few: …").
   Hard cap: max 10 notifications per channel per minute; overflow collapses into a
   summary line. Without this, v0.10.0 upgrades would spam every user's Discord.
5. **API** (`api/v1/notifications.py`, new router): CRUD + `POST /{id}/test` (sends a
   test message, returns Apprise's success/failure). Apprise URL is **write-only**:
   read endpoints return a masked form (`discord://…****`), full URL never leaves the
   server after creation. Frontend edit form treats blank URL as "unchanged".
6. **Settings UI:** new "Notifications" page under Settings (route + sidenav entry):
   channel list (name, service icon parsed from URL scheme, enabled toggle), add/edit
   dialog (name, URL, event-type multi-select using `EVENT_TYPE_LABELS`,
   include-user-events toggle), Test button with toast feedback. Follow MD3 conventions
   in CLAUDE.md (cards, popover dropdowns, native dialog).
7. **What is notifiable:** exactly the `EventType` values. No custom templates in this
   release (keep scope); message format is `<emoji> <Event label>: <media title> — <desc>`
   reusing the same description strings the Events page builds.

## Wargame

- **W1. Invalid/dead URL:** Apprise returns False / raises → mark channel's last_error
  (in-memory or column `last_result`), log warning once per batch, keep app healthy.
  Test button surfaces the failure to the user.
- **W2. Event storm** (attribution pass, first Arr sync of a 1,700-title library, files
  scan finding a whole library): batching (D4) verified by seeding 500 events in a loop
  and asserting ≤ a handful of Apprise calls.
- **W3. Secrets hygiene:** Apprise URLs contain tokens. Verify: never logged (grep the
  dispatcher for url interpolation), masked in GET responses, absent from OpenAPI
  examples, excluded from any event payloads.
- **W4. Channel subscribed to nothing:** allowed; sends nothing.
- **W5. App shutdown mid-batch:** pending buffered notifications may be lost —
  acceptable (fire-and-forget by design); ensure no unhandled-task warnings on exit
  (cancel the dispatcher task in lifespan shutdown).
- **W6. Docker + direct installs:** apprise is pure-python; verify `uv sync` in the
  Docker build AND the bare-metal installer scripts pick it up (scripts/install).
- **W7. Migration on old DBs:** table create only; nothing to backfill.
- **W8. Event types grow later** (Phase 11 issues): store names as strings (VARCHAR
  semantics like EventType) so new types need no migration; unknown stored names are
  ignored harmlessly if a type is ever removed.

## Pitfalls

- Event manager helpers swallow exceptions (`track_*` wrap in try/except) — put the
  dispatch hook where it catches ALL creations (`create_event` core), not per-helper.
- `create_skip_event_if_not_exists` dedupes; hook after the "created" branch only.
- Apprise is sync — run `apprise.notify()` via `asyncio.to_thread` to keep the loop free.
- The frontend has no notifications service — generate/extend API client per convention
  (regenerate OpenAPI; service class follows `ProfileService` shape with httpResource).

## Test matrix / verification

- Manager CRUD + masking; dispatcher batching (fake clock), per-minute cap, failure
  isolation (Apprise mock raising), user-event filtering.
- API tests incl. URL never present in GET body.
- Live: scratch env + a real Discord webhook (maintainer-provided, throwaway) — create
  channel via UI, Test button, then trigger a manual trailer download and see the batch
  message arrive. Headless-Chromium pass over the new Settings page (console errors).

## Exit criteria

- 500-event storm produces ≤ 5 messages on a subscribed channel.
- Killing the webhook mid-run causes zero task failures and one warning log.
- Docs: new page under `docs/user-guide/settings/notifications.md` + nav entry; release
  notes entry with 2–3 example Apprise URLs.
