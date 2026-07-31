# Phase 5 — Drop Legacy Columns

**Status:** IMPLEMENTED (Jul 30, 2026, on dev — releases as v0.11.0) · **Release:** v0.11.0 · **Depends on:** Phases 2–4 shipped and
baked (this is the roadmap's only destructive-migration release — keep it MINIMAL; the
richer filter family moved to Phase 6)

## Objective

Remove `Media.trailer_exists`, `Media.status` (and `MonitorStatus`), plus
`TrailerProfile.stop_monitoring` (per Phase 4 decision). Migrate CustomFilter rows that
referenced removed fields. After this release the old failure modes are unrepresentable.

## Design decisions (settled)

1. **Schema migration** (SQLite → alembic `batch_alter_table` rebuilds):
   drop `media.trailer_exists`, `media.status`, `trailerprofile.stop_monitoring`.
   `media.downloaded_at` STAYS (still real data; sorts use it until W1 of Phase 3
   proved the derived variant — reassess at execution; if derived is in use, drop too).
2. **CustomFilter data migration**, in this order inside one alembic data migration:
   - Profile-type filters (`filter_type=TRAILER`) with `filter_by='trailer_exists'`:
     DELETE the filter row (semantics now implicit in satisfaction). If a profile filter
     had `trailer_exists = true` (nonsensical under the new model), delete AND log
     warning with profile name.
   - View-type filters with `filter_by='trailer_exists'` → rewrite to
     `filter_by='has_downloads'` (EQUALS true/false preserved).
   - View filters on `status` → map `downloaded→has_downloads=true`,
     `missing→has_downloads=false`, `monitored→monitor=true`, anything else → delete +
     warn. Log every rewrite/delete with filter name (users can reconstruct).
   - A CustomFilter left with zero filter rows: keep (matches-all) but log.
3. **New virtual filter field `has_downloads`** (bool): evaluated in backend
   `matches_filters` (from `MediaRead.downloads` — any `file_exists=True`) and frontend
   `applyCustomFilter`; added to `BOOL_COLS`-adjacent VIRTUAL list in
   `core/base/database/models/filter.py` validation (it is NOT a SQL column — `_apply_filter`
   in `manager/media/read.py` must translate it to an EXISTS subquery or route those
   filters through Python; decide by where custom view filters are evaluated server-side
   — check `filter_by=<customfilter>` handling first; frontend does most view filtering).
4. **Code removals sweep:** `get_status`, `update_trailer_exists`,
   `update_no_trailers_exist`, remaining status writes in `trailer.py`, files-scan
   trailer_exists mirror, radarr/sonarr parser fields, `helpers.py` MediaUpdate paths,
   API `filter_by` docstrings, frontend `media.ts` fields + any residual template reads,
   filter-field pickers (`edit-filter-dialog`), table/expanded field options
   (`trailer_exists`, `status` entries), stats models.
5. **`MediaRead.status`/`trailer_exists` API compat ends here** — REMOVED from
   responses. Frontend regenerated same release, external consumers warned in notes.

6. **VACUUM after destructive migration:** SQLite table rebuilds don't return disk
   space — run `VACUUM` on `trailarr.db` after this release's migration completes
   (implement as a post-migration step in the startup flow, generalized: VACUUM
   whenever migrations actually ran, per KR's "default into alembic migrations"
   direction). Also add VACUUM to `logs.db` after the daily `delete_old_logs` purge —
   verified July 2026 that log rows are deleted daily but space is never reclaimed
   (see hygiene H10; can ship in any earlier release).

## Execution notes (Jul 30, 2026)

- W4 resolved: Phase 4 did not introduce `exclusive` — `stop_monitoring` was a plain drop.
- `downloaded_at` STAYS (decision 1 reassessment: still real data — used by the
  download service dedup check and date sorts; no derived variant shipped).
- The full-scan startup pass (`full-scan-before-downloads-v0.10`) lost its
  trailer_exists pre-check: an unrecorded pass now always runs one full disk scan
  (fresh installs: no media, no-op; v0.9.x skippers: exactly the protective scan
  they need). `count_untracked_trailer_media`/`report_attribution_health` removed
  with the mirror; `count_tracked_media` (telemetry) replaced them.
- Sync-time disk trailer checks removed with the mirror: TRAILER_DETECTED now
  fires only from the files scan (was also ConnectionRefresh/PlexRefresh).
- VACUUM implemented in alembic env.py `on_version_apply` — runs whenever any
  migration applied (generalizes decision 6; logs.db VACUUM was already done, H10).

## Wargame

- **W1. User DB with hand-made filters on status/trailer_exists in combinations** the
  mapping can't express (e.g. `status EQUALS downloading`): delete + warn path; release
  notes list exact transformations. Build the migration test from a fixture DB
  containing every FilterCondition × both fields.
- **W2. Migration interrupted mid-rebuild:** SQLite batch rebuild is transactional per
  table but the data migration spans tables — wrap whole migration in one transaction;
  verify `alembic upgrade head` crash-then-retry on a copy is idempotent-safe (the
  entrypoint backs up the DB pre-migration — confirm scripts/launch.py + docker
  entrypoint both do; that backup IS the rollback).
- **W3. Upgrades skipping releases** (v0.9.8 → v0.11.0 directly): the whole chain
  (attempt table → enum→bool → drops) must run in sequence on one boot. Test exactly
  this jump on a config-dev copy AND on a v0.9.6-era fixture DB (no download rows) —
  Phase 2's upgrade guard must still gate the first download run afterwards.
- **W4. `stop_monitoring` column drop vs Phase 4 decision:** if Phase 4 introduced
  `exclusive`, migrate values (`stop_monitoring AND overlapping-profiles-observed` →
  exclusive=true) before dropping; else plain drop.
- **W5. Frontend localStorage:** saved view-filter selections / sort keys referencing
  removed fields (`TrailarrMoviesSort=trailer_exists` etc.) → fall back to defaults
  gracefully (guard in retrieve logic), don't crash.
- **W6. Events history:** old MONITOR_CHANGED / status-mentioning event rows remain and
  must still render (they're strings — fine; verify Events page on migrated config-dev).

## Pitfalls

- SQLite `batch_alter_table` recreates tables: FKs, indexes, server_defaults must be
  restated — diff `PRAGMA table_info` before/after against models.
- Alembic autogenerate will try to "helpfully" touch unrelated drift — hand-write this
  migration.
- `filter.py` validators hard-code col lists (BOOL_COLS/STR_COLS include the removed
  fields) — update or old saved filters fail validation on READ paths too.
- Search the frontend for `'downloaded'`-style string statuses in templates
  (status-icon, table cells) — Phase 3 moved reads to computed status; verify none
  regressed to raw fields.
- `tests/` fixture builders set `trailer_exists=` widely — the biggest mechanical test
  sweep of the roadmap (~15+ files); do it as its own commit.

## Verification

- Migration matrix: fresh install; v0.9.9→; v0.10.1→; v0.10.2→; v0.9.6-fixture→; config-dev copy→.
  Each: boots, filters render, zero tracebacks, spot-check rewritten filters in UI.
- Full suites; headless pass over home (custom filter dropdown), settings/profiles
  (filters editor shows has_downloads, not trailer_exists), media details.

## Docs to update

- `docs/user-guide/settings/profiles/examples.md` — Examples 1 and 2 build on the
  `Trailer Exists = false` filter (with a v0.10.0 "optional" note): REWRITE them —
  the field no longer exists for profile filters; the examples become filter-less (or
  `Is Movie`-only) with a sentence on satisfaction handling "already has a trailer".
- `docs/user-guide/settings/profiles/filters.md` — remove `trailer_exists`/`status`
  from any field lists; document the new `has_downloads` virtual field (view filters).
- `docs/user-guide/settings/general-settings/index.md` — the one-shot full-scan setting
  description says "for situations where `trailer_exists` or `media_exists` flags are
  stale" — reword to download-records language.
- `docs/troubleshooting/backup-restore.md` — this is the roadmap's only destructive
  migration: add a "no downgrade past v0.11.0" note (pre-migration backup is the
  rollback) and mention the post-migration VACUUM (db file shrinks — not corruption).
- Stale-claim grep across `docs/`: `trailer_exists`, `status` (as a stored field),
  `stop_monitoring`, `Stop Monitoring` — after this phase any remaining mention outside
  release notes is wrong. This includes the Phase 2-era deprecation notes, which now
  become "removed in v0.11.0".
- Release notes: the exact CustomFilter transformation table (W1) so users can
  reconstruct deleted/rewritten filters; API compat end for `status`/`trailer_exists`
  response fields; roadmap tick.

## Exit criteria

`grep -rn "trailer_exists\|MonitorStatus\|stop_monitoring" backend/ frontend/src/`
returns only alembic history + release notes. Same grep over `docs/` returns only
release notes. All migration-matrix paths green.
