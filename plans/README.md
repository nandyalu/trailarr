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
6. Update the phase file's **Status** line, the release notes
   (`docs/release-notes/2026.md`), docs pages, and `docs/references/roadmap.md` if
   dates or content shifted. Regenerate OpenAPI (`uv run python ./export_openapi.py` from
   `backend/`) after any API change. Run `graphify update .` after code changes.

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

## Release ladder (estimates as of July 2026)

| Release | Phase | Content | Target | Bake before next |
|---|---|---|---|---|
| v0.9.9 | 1 | Download↔profile attribution + manual assign + heal | Jul 2026 | ✅ shipped |
| v0.10.0 | 2 | Downloads-driven download engine + Apprise notifications | Aug 2026 | ~4 weeks |
| v0.10.1 | 3+4 | Dynamic status + monitor becomes user intent | Sep 2026 | ~2 weeks |
| v0.11.0 | 5 | Drop trailer_exists/status columns, filter migration | late Sep 2026 | ~2 weeks |
| v0.11.1 | 6 | Downloads/files custom-filter family (views) | Oct 2026 | ~2 weeks |
| v0.12.0 | 7 | Backend reorganization (api/services/database/tasks) | Nov 2026 | ~3 weeks |
| v0.13.0 | 8 | TMDB integration (media-videos candidates table) | Dec 2026 | ~3–4 weeks |
| v0.14.0 | 9 | Video types (trailer/teaser/clip/featurette…) | Jan 2027 | ~3 weeks |
| v0.15.0 | 10 | Movie/Series profiles + season trailers (+ profile presets) | Feb 2027 | ~4 weeks |
| v1.0.0 | 11 | Issues section + delight items + stabilization | Mar–Apr 2027 | — |

**Parallel track — Onboarding & Diagnostics** (`track-onboarding-diagnostics.md`):
Connection Doctor + Health page + cookies UI ride v0.11.x releases; the first-run
guided setup rides v0.13.x (post-reorg); the diagnostics bundle fits any release.
Library-wide **preview mode** ships with Phase 3 (v0.10.1).

Rules of the ladder:

- **Additive migrations only until Phase 5**; Phase 5 is the single destructive-migration
  release; Phase 7 is the single big-churn (zero-behavior-change) release.
- Every phase defaults to current behavior (no key → old search; new columns defaulted;
  new options off) — users never *need* to act to stay working.
- Phases 8–11 plans reference **post-reorg paths** (`services/…`, `database/…`). If the
  reorg slips, translate paths back via the move map in `phase-07-backend-reorg.md`.

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
- `phase-02-downloads-engine.md` — the downloads-driven engine (exhaustive).
- `track-apprise-notifications.md` — parallel track, ships with v0.10.0.
- `track-onboarding-diagnostics.md` — parallel track: Connection Doctor, Health page,
  cookies UI, first-run guided setup, diagnostics bundle (milestones A–D).
- `phase-03-dynamic-status.md`
- `phase-04-monitor-intent.md`
- `phase-05-drop-columns.md`
- `phase-06-view-filters.md`
- `phase-07-backend-reorg.md`
- `phase-08-tmdb.md`
- `phase-09-video-types.md`
- `phase-10-media-types-seasons.md`
- `phase-11-issues-v1.md`
- `hygiene-backlog.md` — small non-blocking cleanups; fold into whichever release fits.
