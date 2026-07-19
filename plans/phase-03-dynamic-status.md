# Phase 3 — Dynamic Status

**Status:** not started · **Release:** v0.10.1 (with Phase 4) · **Depends on:** Phase 2

## Objective

Status becomes *computed*, never stored-then-trusted: list-level status derives from
downloads + monitor (cheap, no profile matching); detail-level shows the per-profile
matrix (which profiles match, which are satisfied by which download, which pending or
backing off). `DOWNLOADING` moves to runtime state (in-memory + websocket). The DB
columns keep existing until Phase 5 but nothing meaningful reads them.

## Design decisions (settled)

1. **Computed list status** (on `MediaRead`, derived in the Read model or a helper —
   NOT a DB column): `downloaded` (any active download) → `monitored` (monitor, none) →
   `missing` (no monitor, none). Keep the same three user-facing words the UI already
   uses where possible to minimize churn.
2. **`DOWNLOADING` is runtime-only:** an in-memory registry in the download service
   (`{media_id: profile_id}` of in-flight downloads) exposed via an endpoint and pushed
   over the existing websocket; frontend overlays it on computed status. DB writes of
   `MonitorStatus.DOWNLOADING` are removed — this deletes the stuck-status bug class
   (and the startup machinery that repaired it).
3. **Pending-downloads endpoint** — THE reconciliation view, single source of truth
   shared by task and UI: `GET /media/{id}/pending` → per profile: matches (bool),
   satisfied_by (download id | null), pending (bool), attempt info (count, last_error,
   next eligible). Reuses the exact satisfaction helper from Phase 2 — never a parallel
   reimplementation. (A library-wide variant waits for Phase 11's Issues.)
4. **Query rewrites** off the status/trailer_exists columns:
   - `read_recently_downloaded` (`manager/media/read.py` — `status == DOWNLOADED`) →
     join/EXISTS on active downloads ordered by download `added_at`.
   - Home stats (`manager/general.py` — counts `trailer_exists`) → distinct media with
     active downloads.
   - Backend `_apply_filter` built-ins (downloaded/missing/monitored/unmonitored) →
     EXISTS subqueries on downloads.
   - Frontend `apply-filters.ts` built-ins → downloads-based (`media.downloads.some(…)`)
     — note `downloaded`/`missing`/`unmonitored` currently read `trailer_exists` and
     `status`; `downloading` reads `media.status` → switch to the runtime signal.
5. **Media details matrix UI:** new section (or upgrade of the downloads section) on
   media details rendering the pending endpoint — this is the comprehension deliverable
   of the whole refactor ("profile X matched, satisfied by file Y / pending / failing").
6. **Delete the healing machinery:** `fix_trailer_exists_flags` + its chaining in the
   attribution pass, and Phase 2's shadow logging. Files scan keeps maintaining
   `trailer_exists` writes ONLY as a passive mirror (removed entirely in Phase 5).
7. **Library-wide preview ("dry run"):** extend the pending endpoint with an
   all-media variant (`GET /media/pending?summary` → counts + paginated list of
   (media, profile, reason)) reusing the same satisfaction helper, plus an app setting
   `downloads_enabled` (default True for existing installs). When False, the download
   task computes and logs/publishes what it WOULD do but downloads nothing, and the UI
   shows a "Preview mode" banner with the would-download list. The onboarding wizard
   (see `track-onboarding-diagnostics.md` Milestone C) starts fresh installs in
   preview until the user explicitly enables downloads. Addresses the
   mass-download-fear class (#36, #435).

## Wargame

- **W1. Sort by "date downloaded":** table/expanded views sort on `downloaded_at`
  column — derive from `max(download.added_at where file_exists)`; media with none sort
  last. Check `applySelectedSort` and backend sort options.
- **W2. `downloading` view filter with zero in-flight:** returns empty, not error;
  websocket disconnect leaves overlay stale → clear registry state on task end AND
  broadcast a final "none in flight" message.
- **W3. Crash mid-download:** restart → registry empty → nothing stuck. Verify with
  kill -9 during a stubbed download.
- **W4. Performance on 1,700+ items:** computed status must come from the already-loaded
  `downloads` relationship (no N+1). Validate `read_all_generator` timing on config-dev
  copy before/after (±10%).
- **W5. Status badge flicker:** frontend derives status from merged media+downloads
  resources which reload separately — guard against transient "missing" flashes during
  reload (compute only when downloads map is loaded; keep previous value while loading).
- **W6. API consumers:** `MediaRead.status` field remains in responses (compat until
  Phase 5) — populate it from the computed value so external scripts see truthy data.
- **W7. Events page semantics:** MONITOR_CHANGED events keep working; no event changes.
- **W8. Preview at scale:** the all-media pending computation on 1,700+ items must
  stay interactive (<2s) — it reuses already-loaded downloads + profile matching; if
  slow, compute during the (preview) task run and cache. Preview mode must gate ONLY
  actual downloads — scans, syncs, attribution all keep running (they're read/metadata
  operations users need for the preview itself to be accurate).

## Pitfalls

- `MonitorStatus` enum is imported in many modules — this phase removes *writers* of
  DOWNLOADING and *readers* of stored values, not the enum itself.
- `media.py` API `filter_by=downloading` docstring options list must match new behavior.
- Websocket messages: reuse existing `ws_manager.broadcast(reload=…)` conventions;
  the frontend media service already reloads on `downloads` topics.
- OpenAPI client regen after adding the pending endpoint.
- Frontend `status-icon` component (media-cards/status-icon/) reads `media.status`
  strings — update mapping.

## Verification

- Backend + frontend suites; pending endpoint contract tests (satisfied/pending/backoff
  cases reusing Phase 2 fixtures).
- Scratch env: matrix UI renders correct rows for a 2-profile movie (one satisfied, one
  pending); kill mid-download → no stuck DOWNLOADING anywhere; headless-Chromium pass on
  home/movies/details (console errors, no flicker regression on throttled reload).
- config-dev copy: home page stats equal old stats (they measure the same reality).

## Docs to update

- `docs/user-guide/library/index.md` — the status legend / quick-filter list
  ("Missing: Trailer missing (also includes monitored items)" etc.) must describe the
  COMPUTED status trio (downloaded / monitored / missing) and that `Downloading` is a
  live runtime overlay, not a stored state that can get stuck.
- `docs/user-guide/library/media-details/index.md` — new section for the per-profile
  matrix (which profiles match, satisfied-by, pending, backing off) with the page's
  existing video-clip convention; update the Status hover-details section.
- `docs/user-guide/tasks/index.md` — REMOVE the `SIGNAL-DISAGREE` admonition added for
  the v0.10.0 bake window (the shadow logging is deleted this phase); mention preview
  mode gating actual downloads only.
- Preview mode (`downloads_enabled`): document the setting in
  `docs/user-guide/settings/general-settings/index.md` and, if persisted to `.env`,
  in `docs/getting-started/01-first-things/environment-variables.md`. Explain what
  preview shows and that scans/syncs keep running.
- Stale-claim grep: `stuck`, `Downloading` status in `docs/troubleshooting/` —
  stuck-status troubleshooting entries become obsolete this phase; delete or reword.
- Release notes: computed status, matrix screenshot, preview mode; roadmap tick.

## Exit criteria

Stored `status` no longer read anywhere (grep `\.status` in backend/frontend media
paths); stuck-status impossible by construction; matrix visible on details; stats/
filters/sorts equivalent on config-dev; Docs section executed.
