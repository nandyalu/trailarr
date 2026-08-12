# Phase 7 — Backend Reorganization

**Status:** not started · **Release:** v0.12.0, target Oct 2026 (own release, ~3-week bake)
**Depends on:** Phase 5/6 shipped (post-refactor codebase is smaller; TMDB/video-types
are then *born* into the new structure) · **Blocks:** Phases 8–11 (their plans use new paths)

## Objective

Layered, long-term-maintainable backend: **api** (thin routes) / **services** (all
business logic) / **database** (models + managers + engine, standalone top layer) /
**tasks** (scheduling, state, start/stop only — calls services). **Zero behavior
change** — this release ships no features and no fixes (hygiene-backlog items excepted,
as separate commits).

## Non-negotiable invariants

1. `docs/references/api-docs/openapi.json` is **byte-identical** before/after
   (regenerate and `git diff --exit-code`). Any route/schema drift = bug.
2. Full test suite green after every stage; test changes limited to import paths and
   patch-target strings.
3. DB schema untouched: no migration in this release.
4. Frontend untouched except the agreed light-touch (see bottom).

## Target structure & move map (Stage A: pure moves)

```
backend/
  api/v1/…                    (unchanged location; slimmed in Stage B)
  services/
    media/                    ← core/base/database is NOT this; see database/. Business logic split out in Stage B
    connections/
      base.py                 ← core/base/connection_manager.py
      arr/                    ← core/base/arr_manager/ + core/radarr/ + core/sonarr/
      plex/                   ← core/plex/
    trailers/                 ← core/download/ (trailer.py, trailers/, trailer_search, trailer_file, video_*)
    files/                    ← core/files_handler.py + core/files/ (media_scanner)
    images/                   ← core/download/image.py + core/tasks/image_refresh.py body
    scan/                     ← core/tasks/files_scan.py (logic)
    attribution/              ← core/tasks/download_attribution.py + startup_fixes.py
    notifications/            ← (from v0.10.0 track)
    updates/                  ← core/updates/
    profiles.py, filters.py   ← core/base/utils/{profiles,filters}.py
  database/
    models/                   ← core/base/database/models/
    manager/                  ← core/base/database/manager/
    engine.py, init_db.py     ← core/base/database/utils/
  tasks/                      ← core/tasks/{__init__(scheduler), schedules.py, task_config wiring} ONLY —
                                every task body becomes a thin `await services.x.run(...)`
  config/, exceptions.py, main.py, app_logger.py   (unchanged)
  frontend/                   (static serving — unchanged)
  alembic/                    (unchanged location; see pitfalls)
  tests/                      mirrors the new tree
```

Rules: one commit per moved package; each commit = `git mv` + mechanical import rewrite
+ patch-target rewrite in tests + suite green. Never mix a move with a logic edit.

## Stage B: thin the API layer

`api/v1/*.py` currently hold real logic (e.g. `media.py` ~700 lines: batch updates,
delete-trailer orchestration, filter parsing). For each router: extract logic into the
matching service module; handler keeps only parsing/validation/HTTP-error mapping/
service call/broadcast. Do routers one per commit, largest last
(`media.py`). While extracting, standardize error handling to the pattern established
by `update_download_profile` (ItemNotFoundError→404, unexpected→logged 500 with generic
detail) — this is hygiene-backlog item H1 and IS allowed here since Stage B touches
every handler anyway. **openapi.json must still not change** (response models keep 404
docs; adding documented 500s is the one permitted spec diff — do it for all routers in
one dedicated commit so the spec diff is reviewable).

## Wargame / pitfalls (the whole phase is pitfalls)

- **Alembic:** `alembic/env.py` imports models (`core.base.database…`) — update. Any
  *historical data migration* importing app modules must be found
  (`grep -rn "^from core\|^import core" backend/alembic/versions/`) and rewritten to
  inline table definitions (migrations must never depend on live code paths — fix them
  to be self-contained rather than chasing the new paths).
- **Import rewrite mechanics:** `grep -rln "from core\.\|import core\."` across
  backend+tests; rewrite with sed per move; then `uv run python -c "import main"` and
  pytest as the oracle. Watch for string-based references: `patch("core.tasks…")` in
  tests, `with_logging_context` module labels, task registry names, dynamic imports.
- **ModuleLogger labels** derive from names passed explicitly ("TrailersFilesScan") —
  unchanged. But log lines embed `module:file.py:line` — any doc examples referencing
  them are cosmetic; skip.
- **Runtime path anchors:** `frontend/router.py` computes `parents[2]/frontend-build`
  — moving it would break static serving (it stays). `scripts/launch.py`, Dockerfile
  COPY/WORKDIR, `.vscode/tasks.json` cwd/env, `export_openapi.py`, healthcheck —
  verify each still resolves; they mostly reference `backend/` root which is stable.
- **`PYTHONPATH=backend` import style** stays (no src-layout change — one battle per
  release).
- **conftest.py** temp-dir bootstrapping imports `core.base.database.utils.init_db` →
  `database.init_db`.
- **CLAUDE.md**: the Architecture section MUST be rewritten in the same PR, or every
  future agent session starts with wrong context. Same for `docs/references/contributing.md`
  and graphify (`graphify update .` full re-index; check `graphify-out/wiki`).
- **In-flight PRs/branches** die — coordinate: merge or close everything first; do the
  reorg in one short-lived branch, not over weeks.
- **Circular imports** will surface when database/ becomes standalone: managers
  currently import from `core.base.utils` (filters) for `matches_filters` inside
  read paths? (verify). Rule: `database/` may not import from `services/`; move any
  such logic UP into services (that's Stage B work — if found in Stage A, leave a
  shim + TODO rather than redesigning mid-move).
- **Docker build** (~15–30 min): run once before release even though CI may not.

## Frontend light touch (assess-only + small moves)

- Consolidate `helpers/` + `media/pipes/` into `shared/` (pipes had a duplicate
  `displayTitle` — merge to one, keep the underscore-aware version).
- Write `frontend/src/app/README.md` documenting the feature-folder convention.
- NO route/service restructuring.

## Verification

- Per-commit: full backend suite. Phase end: openapi byte-diff; scratch-env boot +
  full task cycle (attribution → scan → download stubbed) + headless smoke over all
  pages; config-dev copy boot; docker build; `scripts/launch.py` path.
- Grep-proof: `grep -rn "from core\.\|import core\." backend/ | wc -l` == 0 (excluding
  alembic history if left self-contained).

## Docs to update

Zero user-facing behavior change → zero user-guide changes expected. The docs work is
contributor-facing:

- `CLAUDE.md` Architecture section — same PR, non-negotiable (already in pitfalls).
- `docs/references/contributing.md` — any backend path references (`core/…` →
  `services/…`/`database/…`), dev-setup instructions still accurate post-move.
- `docs/references/api-docs/openapi.json` — byte-identical is the invariant; the one
  permitted diff (documented 500s from Stage B) regenerated in its dedicated commit.
- `docs/llms.txt` — no change expected (it documents install/usage, not code layout);
  verify the install commands still hold after script-path checks.
- Stale-claim grep: `docs/` for `core/` code paths (log-line examples referencing
  module paths are cosmetic — skip per pitfalls note).
- Release notes: internal-only statement ("no functional changes; report anything that
  behaves differently"); roadmap tick.

## Exit criteria

Invariants 1–4 hold; CLAUDE.md/docs/graphify updated; release notes describe the reorg
as internal-only ("no functional changes; report anything that behaves differently").
