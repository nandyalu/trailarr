# Phase 7 — Backend Reorganization

**Status:** **Stage A COMPLETE** (Aug 28, 2026) on branch `feat/phase7-backend-reorg`,
13 move commits, 1089 tests green at every one, `openapi.json` byte-identical. Stage B
and Stage C not started. · **Release:** v0.12.0, target Oct 2026 (own release, ~3-week
bake)
**Depends on:** Phase 5/6 shipped (post-refactor codebase is smaller; TMDB/video-types
are then *born* into the new structure) · **Blocks:** Phases 8–11 (their plans use new paths)

## Objective

Layered, long-term-maintainable backend: **api** (thin routes) / **services** (all
business logic) / **database** (models + managers + engine, standalone top layer) /
**tasks** (scheduling, state, start/stop only — calls services). **Zero behavior
change** — this release ships no features and no fixes (hygiene-backlog items excepted,
as separate commits). Stage C then rewrites the prose the reorg leaves behind — log
lines, comments, docstrings — into ASD-STE100 Simplified Technical English.

## Non-negotiable invariants

1. `docs/references/api-docs/openapi.json` has **no structural change** before/after:
   no path, operation id, parameter, schema, or status code differs. Regenerate and
   diff; any structural drift = bug. Exactly two text-only diffs are permitted, each in
   its own dedicated commit: the documented 500 responses from Stage B, and the
   rewritten route-handler `description` strings from Stage C.
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
    notifications/            ← core/notifications/ (from v0.10.0 track)
    diagnostics/              ← core/diagnostics/ (from Onboarding track A+B, v0.11.4:
                                connection_doctor, health, cookies, store, models)
    updates/                  ← core/updates/
    binaries.py               ← core/binaries.py (startup binary-path checks)
    profiles.py, filters.py,  ← core/base/utils/{profiles,filters,satisfaction}.py
      satisfaction.py              (path_utils went to utils/, not here — see below)
  database/
    models/                   ← core/base/database/models/
    manager/                  ← core/base/database/manager/
    engine.py, init_db.py     ← core/base/database/utils/
  tasks/                      ← core/tasks/{__init__(scheduler), schedules.py, task_config wiring} ONLY —
                                every task body becomes a thin `await services.x.run(...)`
  utils/                      ← pure, dependency-free helpers both database/ and
    path_utils.py                services/ may import (← core/base/utils/path_utils.py,
    error_classify.py            ← core/download/error_classify.py, which has no imports
                                 at all). DECIDED Aug 28, 2026. utils/ imports nothing
                                 from the other layers; that rule is what keeps it honest.
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
every handler anyway. **openapi.json must still not change structurally** (response
models keep 404 docs; adding documented 500s is one of the two permitted text diffs —
do it for all routers in one dedicated commit so the spec diff is reviewable).

Do not rewrite handler docstrings while extracting — Stage C owns that, and mixing the
two makes the spec diff unreviewable. Move the docstring with the code, unchanged.

### Stage B: the database layer is not standalone (13 call sites)

The objective calls `database/` a "standalone top layer". It is not one today, and
Stage A deliberately does not fix that (moves stay mechanical). Stage B must, or the
layering is a diagram rather than a fact. The 13 imports fall into three kinds, and
they do **not** all get the same treatment:

- **Connection validation reaching into Arr/Plex clients** (`core.plex` ×4,
  `core.radarr` ×2, `core.sonarr` ×2, all in `database/manager/connection/`). The
  connection manager calls `validate_connection()` / `get_rootfolders()` against live
  APIs from inside the database layer. This is the real violation: network I/O behind
  a database read. Extract to `services/connections/`, leaving the manager to persist
  rows only.
- **`services.notifications.dispatcher`** (function-local, in `manager/event/create.py`
  `_notify`). Move the notify call up to the callers so storing an event does not also
  publish it. TODO already in the code.
- **`core.base.utils.path_utils`** (×3) — RESOLVED in Stage A: a top-level `utils/`
  package now holds the pure, dependency-free helpers that both layers may import, so
  these three stopped being violations (13 → 10). `core.download.error_classify` (×1)
  is the same shape and should join `utils/` when `core/download/` moves, unless it
  turns out to carry download-specific dependencies — check before moving it.

Verification for this section: after Stage B, the unanchored audit script reports **0**
imports from `database/` into `core|services|api|tasks`. That number is the exit
criterion — a green suite does not prove the layering holds.

## Stage C: Simplified Technical English sweep (prose only)

Apply the `orwell-writing` skill (Orwell's six rules + ASD-STE100) to every **log line,
comment, and docstring** in the reorganized backend. CLAUDE.md already mandates STE100
for new and changed content; Stage C pays off the backlog for the files the reorg has
just touched, while they are open anyway.

Runs **after Stage B**, never before: rewriting prose in a file that is about to move
wastes the work and pollutes the move commits, which must stay mechanical.

Surface (measured Aug 28, 2026, pre-move): 167 files under `core/ api/ config/` —
~418 logger calls, ~1,578 comment lines, ~606 docstrings.

**What changes:** wording only. Short sentences, one idea per sentence, active voice,
present tense, approved/simple vocabulary, no strung-together noun clusters. Docstrings
keep their existing Args/Returns/Raises structure — rewrite the prose inside it, do not
restyle the format.

**What must NOT change:**

- Any code, identifier, signature, or control flow. A Stage C commit that changes a
  non-string token is a bug.
- Log **level**, logger name, `extra=`/context fields, or the `%`/f-string interpolation
  arguments. Reword the message; keep every substituted value and its order.
- Structured/diagnostic strings that something parses or matches: task registry names,
  `with_logging_context` module labels ("TrailersFilesScan"), Connection Doctor check
  ids and their user-facing messages (those are UI copy with their own tests, not log
  prose), exception messages that `api/` maps to HTTP detail strings the frontend keys
  on, and any string in a migration.
- Frontend copy. Stage C is backend-only.

**Log lines asserted in tests** — `tests/core/tasks/test_download_attribution.py`
matches the substrings `"extra trailer file"` and `"no profile filters match this
media"`. Either keep those substrings intact or update the assertion in the same commit;
run the suite per commit and let it be the oracle. Grep for further substring assertions
before starting (`grep -rn "caplog" tests/`) — the set can grow between now and Oct.

**Route-handler docstrings feed openapi.json.** 60 operations carry a `description`
derived from the handler docstring, so this sweep WILL change the spec. Put every
route-handler docstring rewrite in **one dedicated commit**, regenerate the spec in that
same commit, and verify the diff touches only `description` (and `summary`) values —
no paths, operation ids, parameters, schemas, or status codes. This is the second of the
two permitted spec diffs in invariant 1.

**Already done, do not redo:** commit `fe4d5d58` (Aug 28, 2026) applied this treatment
to the files v0.11.4 changed — `core/diagnostics/*`, `api/v1/{connections,health}.py`,
`config/settings.py`, `frontend/{middleware,router}.py`, two managers, and
`core/download/error_classify.py`. Skip those unless the reorg reopens them.

**Order:** one commit per package, same order as Stage A, so the diff for each package
is reviewable as prose. Route-handler docstrings are pulled out of those commits into
the dedicated spec commit above.

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
- **Runtime path anchors — the sharpest edge in this phase.** A `Path(__file__).
  parents[N]` anchor is silently wrong after a move: the module still imports, the app
  still boots, and the feature is just dead. Stage A hit this immediately —
  `version_guard.py` used `parents[4]` (correct at `core/base/database/utils/`) and had
  to become `parents[1]` at `database/`; because the guard also fails open on an empty
  revision set (see hygiene H12), nothing but its unit test would have noticed, and the
  ladder's downgrade protection would have shipped disabled.
  **Full inventory of app-owned anchors (checked Aug 28, 2026 — recheck before each
  move):**
  - `database/version_guard.py` → `parents[1]` — FIXED in the database move.
  - `core/download/cli.py:9` — `sys.path.insert(0, dirname(dirname(abspath(__file__))))`.
    Two levels up from `core/download/` is `core/`. **Recompute when `core/download/`
    becomes `services/trailers/`** — two levels up then lands on `backend/`, which is
    a different (and probably more correct) path. Verify the CLI entry point by
    running it, not by reading it.
  - `export_openapi.py`, `app_logger.py`, `frontend/router.py` — all anchored at the
    `backend/` root and none of them move; no change needed.
  - **Tests have them too**, and a moved test breaks at *collection*, taking the whole
    run down with an error rather than a failure. `tests/services/test_filter_parity.py`
    used `parents[3]` to find `tests/fixtures/filter-cases.json` and needed `parents[1]`
    after moving up two levels. Still-correct ones that must not be "fixed":
    `tests/scripts/test_*.py` use `parents[3]` for the repo root, and
    `tests/test_phase5_filter_migration.py` / `tests/test_upgrade_gauntlet.py` use
    `parents[1]` for `backend/` — all three sit at depths that do not change.
  After every move, grep the moved package **and its tests** for `__file__` and
  re-derive each index by hand. A green test suite does not prove an anchor is right —
  but a collection error usually means you just broke one.
- **Test collection order changes with every move, and the suite is not isolated.**
  Tests share one session-scoped database (`conftest.pytest_configure` → `init_db()`),
  so any test that assumes an autoincrement id breaks when a move reshuffles collection
  order. The database move exposed exactly this: `test_connection.py` hardcoded
  `CONN_ID_1 = 1`, and once it sorted after `tests/core/base/test_connection_manager_
  monitor.py` that module took id 1 first. Fixed by using the id `create()` returns.
  Expect one or two more of these per move; the fix is always "use the id the code gave
  you", never "restore the old ordering". When a move produces failures, run the failing
  file alone first — passing in isolation but failing in the suite is this bug, not the
  move.
- **`scripts/launch.py`, Dockerfile COPY/WORKDIR, `.vscode/tasks.json` cwd/env,
  healthcheck** — verify each still resolves; they mostly reference `backend/` root
  which is stable.
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

## Pre-flight audit (run Aug 28, 2026 — results below)

Measured against `dev` at `fe4d5d58`, before any move. Re-run each line if the phase
does not start within a few weeks of this date.

| Check | Result |
|---|---|
| Baseline test suite | **1089 passed**, 78s. This is the number every Stage A/B/C commit must still show. |
| Alembic history importing app modules | **0 files** — the "rewrite migrations to be self-contained" pitfall is moot. Only `alembic/env.py:8` imports `core` (one line). |
| `database/` → business-logic imports | **13** (3 of them function-local). The first audit said "none" and was simply wrong — see the methodology note below. `database/` is NOT standalone today. Breakdown: `core.plex` ×4, `core.base.utils.path_utils` ×3, `core.radarr` ×2, `core.sonarr` ×2, `core.download.error_classify` ×1, `services.notifications.dispatcher` ×1. Left in place for Stage A per the shim rule; **this is now real Stage B work** (see "Stage B: the database layer is not standalone" below). |
| `from core.`/`import core.` occurrences | **640** total: 405 app code, 235 tests, 1 alembic. This is the mechanical rewrite budget. |
| `from api.`/`import api.` occurrences | 42 |
| String patch targets in tests | **501** `patch("…")` calls — 391 target `core.*`, 102 `api.*`. Highest-churn prefixes: `core.download.trailer.*`, `core.tasks.files_scan.*`, `core.download.video_analysis.*`, `api.v1.files.*`, `api.v1.authentication.*`. These break silently (a wrong patch target still "passes" as a no-op patch) — after each move commit, grep the moved package's old dotted prefix across `tests/` and confirm zero hits, rather than trusting a green suite alone. |
| openapi.json baseline | `sha256 aa8b427ff82e2b443119276ae812a9025e425fe2dc2689211055ab0202ece97a` |
| Route descriptions in spec | 60 operations carry a docstring-derived `description` (drives the Stage C dedicated commit) |

**Methodology — do not audit this phase with plain `grep` in this environment.** The
first pass of the table above was wrong twice over: it reported 263 patch targets (real
number 501) and zero `database/`→business-logic imports (real number 13). Two causes,
both worth knowing:

1. **`grep` here is proxied by rtk**, which does not return the same match set as GNU
   grep. Counts taken through it undercounted by ~half.
2. **Line-anchored patterns (`^from core\.`) miss deferred imports** written inside
   functions, which is precisely where layering violations live.

Take every count for this phase with a small Python script that walks the tree and
matches unanchored (`(?:from|import)\s+core\.`), skipping `__pycache__` and `.venv`.
The numbers in the table above were re-derived that way and are trustworthy; anything
you re-measure later should be too.

**Move-map drift found and fixed:** four things exist that the original map predated —
`core/diagnostics/` (6 files, from Onboarding A+B in v0.11.4), `core/binaries.py`, and
`core/base/utils/{path_utils,satisfaction}.py`. All four are now in the map above. The
map is otherwise accurate.

## Frontend light touch (assess-only + small moves)

- Consolidate `helpers/` + `media/pipes/` into `shared/` (pipes had a duplicate
  `displayTitle` — merge to one, keep the underscore-aware version).
- Write `frontend/src/app/README.md` documenting the feature-folder convention.
- NO route/service restructuring.

## Verification

- Per-commit: full backend suite. Phase end: openapi structural diff (only the two
  permitted text diffs); scratch-env boot + full task cycle (attribution → scan →
  download stubbed) + headless smoke over all pages; config-dev copy boot; docker build;
  `scripts/launch.py` path.
- Grep-proof: `grep -rn "from core\.\|import core\." backend/ | wc -l` == 0 (excluding
  alembic history if left self-contained).
- Stage C proof: `git diff --stat` for each Stage C commit touches only string/comment
  lines — confirm with a token-level check that no non-string token moved
  (e.g. compare `ast.dump` of each changed module before/after with docstrings
  stripped; identical dumps = no code change). Boot the app and read the startup log
  end to end: the sequence must still be followable by a user diagnosing a problem.

## Docs to update

Zero user-facing behavior change → zero user-guide changes expected. The docs work is
contributor-facing:

- `CLAUDE.md` Architecture section — same PR, non-negotiable (already in pitfalls).
  Note the backend subtree is written as bullets relative to `core/` (`base/database/
  models/`), so a grep for `core/` finds only one line — rewrite the whole subtree.
- `.github/instructions/backend.instructions.md` — **18 `core/…` path references**
  (Copilot's architecture brief; the same trap as CLAUDE.md, and not in the original
  plan). Rewrite in the same PR.
- `.github/planned_tasks.md` — scratch planning doc with ~10 `core/…` hook-point paths.
  Lower priority; refresh or delete if it is stale by then.
- `docs/references/contributing.md` — **no `core/` path references** (checked Aug 28,
  2026); only verify the dev-setup commands still work post-move.
- `docs/references/api-docs/openapi.json` — no structural change is the invariant; the
  two permitted text diffs (documented 500s from Stage B, rewritten handler descriptions
  from Stage C) each regenerated in their own dedicated commit.
- `docs/llms.txt` — no change expected (it documents install/usage, not code layout);
  verify the install commands still hold after script-path checks.
- Stale-claim grep: `docs/` for `core/` code paths (log-line examples referencing
  module paths are cosmetic — skip per pitfalls note).
- Release notes: internal-only statement ("no functional changes; report anything that
  behaves differently"); roadmap tick.

## Exit criteria

Invariants 1–4 hold; Stages A, B and C complete; CLAUDE.md/docs/graphify updated;
release notes describe the reorg as internal-only ("no functional changes; log messages
are clearer; report anything that behaves differently").

## Stage A completion record (Aug 28, 2026)

13 move commits on `feat/phase7-backend-reorg`, branched from `dev` at `438fb594`.
Final layout: `api/ services/ database/ tasks/ utils/` — `core/` is gone.

Evidence, not assertions:

- **1089 tests green after every commit** — identical to the pre-reorg baseline. Two
  commits needed a real fix to get there (the `version_guard` anchor, the
  collection-order id assumption); both are described in the pitfalls above.
- **`openapi.json` byte-identical** to the pre-reorg spec (79 paths, 56 schemas,
  `info.version` v0.11.4). This is the strongest proof the moves were pure — the whole
  API surface regenerated to the same bytes from relocated code.
- **Zero `from core` / `import core` anywhere** in `backend/`, including tests and
  alembic.
- **27 migrations apply to a fresh database** (14 tables, head `b30b7b2fd9b4`), then
  VACUUM, with `alembic/env.py` importing `database.init_db`.
- **Real boot, not just tests:** uvicorn started clean with **zero errors** in the log;
  all 7 scheduled tasks registered; `Arr Data Refresh` and `Startup Passes` both ran and
  recorded (`attribute-downloads-v0.9.9`, `full-scan-before-downloads-v0.10`). After
  login, every reorganized layer answered 200: `/connections/`, `/customfilters/`,
  `/events/`, `/settings/`, `/media/all_raw`, `/tasks/`, `/trailerprofiles/`,
  `/connections/doctor`, `/health/checks`. The only warnings were environmental
  (Docker binary paths absent in dev, empty database).
- **`cli_to_api` called after the move** to prove the vendored yt-dlp helper still works.
- **Layering violations 13 → 9.** The four shared-helper cases were resolved by the new
  `utils/` layer; the remaining nine are the connection-validation and notification
  calls that Stage B extracts.

Not done in Stage A, deliberately: task bodies are still in `tasks/` rather than split
into `services/scan/`, `services/attribution/` and `services/images/`. That is an
extraction, not a move, so Stage B owns it. Note the map named
`core/tasks/startup_fixes.py`, which no longer exists — hygiene H7 deleted it; the file
to split is `startup_passes.py`.

Still outstanding before the phase can ship: Stage B, Stage C, the frontend light touch,
`.github/instructions/backend.instructions.md` (18 stale `core/…` paths),
`.github/planned_tasks.md`, a `graphify update .` re-index, the Docker build, and the
`config-dev` copy boot. `CLAUDE.md` is already updated.
