# Phase 4 — Monitor Becomes User Intent

**Status:** in progress (July 2026, branch `feat/phase-03-dynamic-status` off dev, with Phase 3) · **Release:** v0.10.1 (with Phase 3) · **Depends on:** Phase 2

> **Decision-5 note (July 2026):** v0.10.0 has not shipped yet, so the Phase 2
> shadow logs the `exclusive` option was conditioned on DO NOT EXIST. Implementing
> the stated default path (remove stop_monitoring, no replacement option).
> **Checkpoint before releasing v0.10.1:** review the v0.10.0 bake-window
> SIGNAL-DISAGREE logs (via=stop_monitoring on media with >1 matching profile);
> if real overlapping-profile setups show up, add the `exclusive` per-profile
> bool then.

## Objective

`monitor` is written only by the user (and once at media creation). Arr/Plex syncs stop
touching it. The per-connection `MonitorType` enum becomes a boolean **"Monitor new
media"** used only at creation time. This phase is the flagship application of
cross-phase invariant #6 ("automation may only write what automation owns" —
`plans/README.md`): monitor moves permanently into user-owned state.

## Design decisions (settled)

1. **Migration:** `connection.monitor` enum → bool `monitor_new_media`
   (`MONITOR_NONE → False`, everything else → True). SQLite: batch_alter table rebuild;
   keep a mapping log line per connection.
2. **Sync stops writing monitor:** delete `_check_monitoring` + the monitor half of
   `update_monitor_and_trailer_exists_bulk` in `core/base/connection_manager.py`
   (`_process_media_list` keeps its trailer_exists carry-forward until Phase 5);
   same for the Plex variant (`core/plex/connection_manager.py:121`). Media creation
   sets `monitor = connection.monitor_new_media`.
3. **MONITOR_SYNC replacement = profile filter `arr_monitored = true`.** No automatic
   profile mutation (surprise risk); instead: release notes walk-through + a one-time
   startup log line listing connections that were SYNC ("add an arr_monitored filter to
   your profiles to keep sync-like behavior"). `arr_monitored` keeps being updated by
   syncs (it's a fact, not intent).
4. **User toggle loses guardrails:** `update_monitoring`
   (`manager/media/update.py:181-216`) becomes a plain flag write + event — no
   trailer_exists refusals, no status coupling.
5. **`stop_monitoring` resolution (deferred from Phase 2):** REMOVE the option from the
   UI and stop honoring it; replace its semantics with the Phase 2 satisfaction carve-out
   flipped into an explicit per-profile bool **`exclusive`** ("if this profile downloaded,
   media is fully satisfied") ONLY IF Phase 2's shadow logs showed real usage of
   overlapping-profile setups. Default path: migrate `stop_monitoring=True` (the
   default) → nothing (satisfaction already stops re-downloads);
   `stop_monitoring=False` users are the multi-trailer users — they get exactly what
   they configured. Column dropped in Phase 5. Confirm with maintainer before coding if
   shadow data is ambiguous.
6. **Frontend:** connection create/edit forms swap the Monitor Type dropdown for a
   toggle; `MonitorType` removed from `models/connection.ts`; media-details monitor
   button unchanged (it's now the *only* writer besides creation).

## Wargame

- **W1. SYNC-connection user upgrades:** monitor values FREEZE as-is at upgrade (no
  data migration of media.monitor — intent snapshot is the fairest default). Radarr
  unmonitors a movie later → Trailarr no longer follows. Covered by W3 messaging +
  `arr_monitored` filter path. Verify the filter path actually works end-to-end
  (profile filter on arr_monitored + satisfaction → no download for unmonitored-in-arr).
- **W2. NONE-connection user:** new media arrives unmonitored (monitor_new_media=False)
  — same as before.
- **W3. Bulk edit flows:** the media edit-mode bulk monitor action and
  `update_monitoring_bulk` keep working (they're user intent).
- **W4. Plex-only media:** `_check_monitoring` on Plex path also decided initial
  monitor for newly-found Plex items — replace with the same creation-time bool.
- **W5. Media re-added (deleted from Arr then re-synced):** treated as new → gets
  creation default. Fine; note in code.
- **W6. `arr_monitored` still synced:** confirm the bulk update path that maintains it
  survives the deletion of the monitor half (they're currently the same tuple update —
  split it).
- **W7. Migration downgrade:** bool → enum is lossy; document "no downgrade" and rely
  on the standard pre-migration DB backup.

## Pitfalls

- `MonitorType` is imported by tests, seed migration, plex manager, api models,
  frontend — sweep imports; the old enum stays importable only inside historical
  alembic migrations (they must not import app models — check they don't).
- `_check_monitoring` tests exist in `tests/core/plex/` and connection tests — rewrite
  to creation-default tests.
- API: connection endpoints' schemas change (enum→bool) → OpenAPI regen + frontend
  client; keep accepting the old field name during v0.10.x? No — clean break, called out
  in release notes (API consumers are few; document in notes).
- Events: keep firing MONITOR_CHANGED only from user actions now — assert syncs create
  zero monitor events (nice regression test: full sync on config-dev copy → 0
  MONITOR_CHANGED events).

## Verification

- Backend/frontend suites; migration on config-dev copy (enum distribution → bool
  correctly, log lines list SYNC connections).
- Scratch: full Arr-sync cycle (mocked Arr API responses) → media.monitor untouched for
  existing items, defaulted for new; toggle in UI works; connection form renders toggle.
- config-dev soak: sync twice; diff `SELECT id, monitor FROM media` between runs → empty.

## Docs to update

- `docs/user-guide/settings/connections/index.md` — the **Monitor Types** section is
  the big one: the enum is gone, replaced by the "Monitor new media" toggle (creation
  time only). Note: `docs/troubleshooting/faq.md` ("not downloading for some media")
  deep-links to `#monitor-types` — update both the anchor target and the FAQ answer.
- `docs/getting-started/03-setup/connections.md` — connection setup flow shows the
  Monitor Type choice; swap for the toggle with the new semantics ("sets the initial
  state of new media; Trailarr never changes monitoring afterwards — only you do").
- `docs/user-guide/library/media-details/index.md` + `docs/user-guide/library/index.md`
  — monitor is now purely user intent; syncs never touch it. Extend the Phase 2 note.
- **SYNC-replacement recipe:** document the `arr_monitored = true` profile-filter
  pattern in `docs/user-guide/settings/profiles/filters.md` (and/or `examples.md`) —
  the release notes walk-through should link to this docs anchor, not inline it all.
- `docs/user-guide/settings/profiles/settings/general.md` — if the Stop Monitoring
  option is removed from the UI this phase (decision 5), replace the deprecated section
  with a short "removed in v0.10.1" note pointing at the multi-profile pattern (column
  drop is Phase 5; the `exclusive` option, if introduced, gets its own subsection).
- API breaking change (connection enum→bool): call out in release notes for API
  consumers; regenerate `docs/references/api-docs/`.
- Release notes: SYNC walk-through leads; roadmap tick.

## Exit criteria

Grep-proof: no writer of `media.monitor` outside `update_monitoring(_bulk)` and media
creation. Zero MONITOR_CHANGED events from a full sync. Release notes carry the SYNC
walk-through prominently. Docs section executed (FAQ monitor-types link verified).
