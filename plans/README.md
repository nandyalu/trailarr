# Trailarr Roadmap to v1.0.0 — Execution Plans

This directory contains the **per-phase execution plans** for the roadmap published at
`docs/references/roadmap.md`. The roadmap page is the user-facing summary; these files are
the engineering plans. They are written to be executed by someone (or some model) with no
prior context beyond this repository.

## How to execute a phase

1. Read this README fully, then the phase file. Do not start a phase whose
   **Preconditions** are not met.
2. **Design decisions in each plan are settled** — do not relitigate them mid-execution.
   If reality contradicts a decision (an API changed, a file no longer exists), stop and
   surface it rather than improvising.
3. Work in the order given in **Execution steps**. Steps are ordered to keep the app
   releasable at every commit.
4. The **Wargame** section lists scenarios that WILL happen in real libraries. Every one
   must have a deliberate answer in code or tests before the phase exits.
5. Run the full **Verification protocol** — backend tests, frontend tests, AND the
   real-app checks. `npm run build`/pytest alone is never sufficient
   (see CLAUDE.md → "Verifying Frontend Changes End-to-End").
6. Execute the phase's **Docs to update** section (see "Docs rule" below) — docs ship
   in the same release as the behavior change, never afterwards.
7. Update the phase file's **Status** line, the release notes
   (`docs/release-notes/2026.md`), and `docs/references/roadmap.md` if
   dates or content shifted. Regenerate OpenAPI (`uv run python ./export_openapi.py` from
   `backend/`) after any API change. Run `graphify update .` after code changes.

## Docs rule (every phase)

Every phase plan carries a **Docs to update** section: the doc pages its changes touch,
with enough context to update them accurately. Execute it as part of the phase, in the
same PR/release — v0.10.0 shipped with docs still describing the pre-Phase-2 engine
(Stop Monitoring as the multi-trailer mechanism, "Trailarr will not download multiple
trailers automatically", no mention of backoff); a follow-up audit had to fix seven
pages. This rule exists so that never happens again.

Standard checklist, in addition to each phase's listed pages:

- **Stale-claim grep, not just new pages:** grep `docs/` for the feature's old terms
  (Phase 2 example: `Stop Monitoring`, `trailer_exists`, `stop monitoring`) — docs rot
  comes from old sentences, not missing ones. FAQ and troubleshooting pages are the
  most frequent offenders.
- **Release notes** (`docs/release-notes/2026.md`) — every user-visible change,
  including the caveats the phase's Wargame section flags for release-noting.
- **`docs/references/roadmap.md`** — phase status/dates.
- **`docs/llms.txt`** — update whenever install steps, CLI commands, ports, config
  paths, or the setup flow change (it inlines those facts for AI assistants; a stale
  llms.txt is worse than none).
- **Version badges:** mark changed sections with
  `{{ version_badge("add"|"upd", "<version>") }}`.
- **Formatting:** docs prose is single-line paragraphs (no hard wrapping — zensical);
  verify with `uv run --project backend zensical build` and spot-check rendered HTML.

## Testbed assets

- `config-dev/` (gitignored) — a copy of the maintainer's real ~1,700-title library
  config/DB. THE wargaming asset: run migrations + tasks against a copy of it before
  declaring any data-touching phase done. Never write to it directly — copy it first.
- Scratch verification pattern: create a temp `APP_DATA_DIR`, run
  `uv run alembic upgrade head` (seeds 2 default profiles), seed rows via the app's own
  managers, boot `uvicorn main:trailarr_api`, drive with headless Chromium (playwright via
  `NODE_PATH=/home/kr/.hermes/hermes-agent/node_modules node <script>.cjs`).
- The startup pass ("Attribute Trailer Downloads") fires at +60s; disk scan at +480s;
  download task at +900s. Time your verification windows accordingly.

## Release ladder (estimates as of August 11, 2026)

| Release | Phase | Content | Target | Bake before next |
|---|---|---|---|---|
| v0.9.9 | 1 | Download↔profile attribution + manual assign + heal | ✅ shipped Jul 2026 | ✅ done |
| v0.10.0 | 2 | Downloads-driven download engine + Apprise notifications | ✅ shipped Jul 19, 2026 | ✅ done |
| v0.10.2 | 3+4 | Dynamic status + monitor becomes user intent | ✅ shipped Jul 30, 2026 | ✅ done |
| v0.11.0 | 5 | Drop trailer_exists/status columns, filter migration | ✅ shipped Aug 9, 2026 | ~2 weeks (baking, to ~Aug 23) |
| v0.11.1 | — | Unplanned fixes (Plex-only removal cleanup, Windows install, yt-dlp/Deno) | ✅ shipped Aug 11, 2026 | — |
| v0.11.2 | — | Unplanned fixes (Plex library-root folder match) | TBD (ready) | — |
| v0.11.3 | 6 | Downloads/files custom-filter family (views) | Sep 2026 | ~2 weeks |
| v0.12.0 | 7 | Backend reorganization (api/services/database/tasks) | Oct 2026 | ~3 weeks |
| v0.13.0 | 8 | TMDB integration (media-videos candidates table) | Nov 2026 | ~3–4 weeks |
| v0.14.0 | 9 | Video types (trailer/teaser/clip/featurette…) | Dec 2026 – Jan 2027 | ~3 weeks |
| v0.15.0 | 10 | Movie/Series profiles + season trailers (+ profile presets) | Feb 2027 | ~4 weeks |
| v1.0.0 | 11 | Issues section + delight items + stabilization | Mar 2027 | — |

**Patch releases do not carry phases.** v0.11.1 and v0.11.2 are fix-only releases that
came out of real-library bug reports, so Phase 6 moved from v0.11.1 to v0.11.3. Expect
this to repeat: when a fix release takes the next patch number, the pending phase moves
down the ladder instead of being folded into the fix release.

**Timeline reassessment (Aug 11, 2026):** Phase 5 shipped ~3 weeks ahead of its Sep 2026
target, so every later phase pulls in by ~1 month against the July estimates. v1.0.0
moves from Mar–Apr 2027 to Mar 2027 — one month of the gain is deliberately held back as
buffer for the December slowdown (Phase 9 spans Dec–Jan) rather than being spent.

**Parallel track — Onboarding & Diagnostics** (`track-onboarding-diagnostics.md`):
Connection Doctor + Health page + cookies UI ride the v0.11.3–v0.12.x releases; the
first-run guided setup rides v0.13.x (post-reorg); the diagnostics bundle fits any
release. Library-wide **preview mode** shipped with Phase 3 (v0.10.2).

Rules of the ladder:

- **Additive migrations only until Phase 5**; Phase 5 is the single destructive-migration
  release; Phase 7 is the single big-churn (zero-behavior-change) release.
- Every phase defaults to current behavior (no key → old search; new columns defaulted;
  new options off) — users never *need* to act to stay working.
- Phases 8–11 plans reference **post-reorg paths** (`services/…`, `database/…`). If the
  reorg slips, translate paths back via the move map in `phase-07-backend-reorg.md`.

## Upgrade-safety rules (version skips are normal, plan for them)

Users routinely jump multiple releases (e.g. v0.9.8 → v0.11.0). Schema is skip-safe by
construction (Alembic runs the whole chain sequentially); these rules keep DATA fixes
skip-safe too:

1. **One-shot fixes are migrations; reconciliation is startup passes.** If a data fix
   should run exactly once, write it as an Alembic data migration. App-code startup
   passes are reserved for idempotent reconciliation that is valid to re-run forever.
2. **A startup pass may only be deleted when** no later code depends on its effect, OR
   its effect is converted to a data migration in the same release that deletes it.
   Record the justification in the deleting phase's plan.
3. **Startup-pass registry (built in Phase 2):** passes register with a name and
   dependency order; completion is recorded in the DB (name, app version, timestamp);
   unrecorded passes run in order at boot BEFORE scheduled tasks; dependent tasks gate
   on their required passes. A version-skipper simply runs every missed pass on first
   boot. The registry doubles as the upgrade audit trail (feeds the diagnostics bundle).
4. **Release-fixture gauntlet:** keep one small fixture DB per released version in
   `backend/tests/fixtures/dbs/` (snapshot after each release, starting with a
   v0.9.6-era and a v0.9.9 fixture); a shared test harness runs
   `alembic upgrade head` + all startup passes from EVERY fixture and asserts core
   invariants. Every phase's verification includes the gauntlet; each release adds its
   fixture.
5. **Downgrade guard:** on boot, if the DB's Alembic revision is unknown to (ahead of)
   the running app, refuse to start with a clear message pointing at the pre-upgrade
   backup — never crash confusingly on a newer schema.

## Cross-phase invariants

1. `PYTHONPATH=backend uv run python -m pytest tests/` green at every commit.
2. `npm run test` + `npm run build` green at every commit that touches frontend.
3. A media item is never downloaded for a profile that already has an active
   (`file_exists=True`) download for it — from Phase 2 onward this is THE core invariant;
   any regression is a release blocker.
4. `monitor` is written by exactly: user actions, media-creation defaults, and (until
   Phase 4 removes them) the legacy sync/download paths. Nothing new may write it.
5. OpenAPI spec (`docs/references/api-docs/openapi.json`) is regenerated whenever
   `api/` changes; for Phase 7 (reorg) the spec must be **byte-identical** before/after.
6. **Automation may only write what automation owns.** Every piece of state has exactly
   one writer class: Arr/Plex syncs write sync-derived facts (ARR-source video rows,
   `arr_monitored`, media metadata), the TMDB refresh writes/prunes TMDB-source rows,
   search writes SEARCH rows, files scan writes disk-derived facts — and **user-owned
   state (the `monitor` flag after Phase 4, USER-source video candidates, manually
   assigned download profiles, dismissals) is never written, relabeled, or deleted by
   any background task**, only reported on (e.g. a failing USER video becomes an Issue,
   not a deletion). When a phase is tempted to have automation "fix" user state for
   convenience, that is a design bug — the pre-roadmap monitor flag is the cautionary
   tale. Applies in reverse too: user actions don't silently rewrite automation-owned
   facts; they express intent through user-owned fields.

## File index

- `phase-01-attribution.md` — DONE (v0.9.9); kept as reference for patterns/conventions.
- `phase-02-downloads-engine.md` — DONE (v0.10.0, Jul 19 2026).
- `track-apprise-notifications.md` — DONE (shipped with v0.10.0).
- `track-onboarding-diagnostics.md` — parallel track: Connection Doctor, Health page,
  cookies UI, first-run guided setup, diagnostics bundle (milestones A–D).
- `phase-03-dynamic-status.md` — DONE (v0.10.2, Jul 30 2026, with Phase 4).
- `phase-04-monitor-intent.md` — DONE (v0.10.2, Jul 30 2026, with Phase 3).
- `phase-05-drop-columns.md` — DONE (v0.11.0, Aug 9 2026); baking ~2 weeks (to ~Aug 23)
  — watch for filter-migration and has_downloads reports before starting Phase 6.
- `phase-06-view-filters.md` — NEXT (v0.11.3); start after the Phase 5 bake window.
- `phase-07-backend-reorg.md`
- `phase-08-tmdb.md`
- `phase-09-video-types.md`
- `phase-10-media-types-seasons.md`
- `phase-11-issues-v1.md`
- `hygiene-backlog.md` — small non-blocking cleanups; fold into whichever release fits.
- `post-v1-backlog.md` — post-v1.0 ideas + deliberate deferrals with revisit triggers
  (Arr webhooks with auto-registration is the headline item).
