# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Trailarr** is a Docker-based application that automates downloading and managing trailers for Radarr and Sonarr media libraries. Plex is a first-class connection type that works alongside Arr connections. Emby and Jellyfin are also supported.

- **Backend**: Python 3.13 + FastAPI + SQLModel + Alembic + SQLite
- **Frontend**: Angular 22 (standalone components, Signals) + TypeScript strict mode
- **Task Scheduler**: Quiv (async task scheduler, replaced APScheduler)
- **Dependency manager**: `uv` for Python, `npm` for frontend

## Commands

### Setup

```bash
# Backend (from /app/backend) - takes ~60s
uv sync

# Frontend (from /app/frontend) - takes ~90s
npm install
```

### Development Servers

```bash
# FastAPI backend (from /app/backend) - requires database setup first
PYTHONPATH=$(pwd) APP_DATA_DIR=/tmp/trailarr-config uvicorn main:trailarr_api --host 0.0.0.0 --port 7888

# Angular frontend (from /app/frontend) - proxies API to localhost:7888
npm run start   # http://localhost:4200
```

### Database Setup

```bash
# Required before running the backend server
mkdir -p /tmp/trailarr-config/logs /tmp/trailarr-config/web
cd backend
APP_DATA_DIR=/tmp/trailarr-config uv run alembic upgrade head
```

### Verifying Frontend Changes End-to-End

Don't rely on `npm run build` / `npm run test` alone to confirm a frontend change actually works — drive the real app:

```bash
# 1. Build the frontend (outputs to ../frontend-build/)
cd frontend && npm run build

# 2. From repo root, launch the real app (backs up DB, runs migrations, serves API + built
#    frontend together on port 7890 — this is the same path a production install uses,
#    see backend/frontend/router.py)
python3 scripts/launch.py

# 3. Drive http://localhost:7890 with headless Chromium (Playwright) and check console errors
```

`scripts/launch.py` uses the persistent dev config at `config/.env` / `config/trailarr.db` (gitignored; NOT `config-dev/`, which is a copy of a real library — never write to it). That `.env` does not disable auth, so launch with `WEBUI_DISABLE_AUTH=true python3 scripts/launch.py` to skip the login page (the shell env var wins because `load_dotenv(override=False)`), or sign in with admin/trailarr. Stop it with `pkill -f "scripts/launch.py"` and `pkill -f "uvicorn main:trailarr_api"` (it execs into `uv run uvicorn`, so both process names can exist). Prefer this over `ng serve` + `src/proxy.conf.json` for verification — the dev proxy is a different code path (Angular dev server proxying to the backend) than the production static-file serving in `router.py`.

### Testing

```bash
# Backend tests (from /app/backend) - ~680 tests, ~35s
# Note: use `uv run python` — plain `python` is not in PATH
PYTHONPATH=$(pwd) uv run python -m pytest tests/ -v
PYTHONPATH=$(pwd) uv run python -m pytest tests/path/to/test_file.py -v   # single file

# Frontend tests (from /app/frontend) - Vitest, ~2s
npm run test
npm run test:coverage
```

### Build

```bash
# Frontend production build (from /app/frontend) - ~10s, output to ../frontend-build/
npm run build

# Docker image (~15-30 min; may fail in CI due to SSL/PyPI issues)
docker build --tag trailarr:latest .
```

### Docs

```bash
# Build the documentation site (from repo root, outputs to site/)
# NOT `mkdocs build` — mkdocs.yml references mkdocs-material extensions, but the
# `material` package isn't installed in the backend venv. This project actually
# builds with zensical instead.
uv run --project backend zensical build
```

### Database Migrations

```bash
# From /app/backend
uv run alembic revision --autogenerate -m "Description of changes"
uv run alembic upgrade head
```

## Architecture

### Backend (`/app/backend/`)

Layered architecture:

- `main.py` — FastAPI app entry point (`trailarr_api`)
- `api/v1/` — Route handlers (media, tasks, connections, settings, events, logs, websockets, etc.)
- `core/` — Business logic
  - `base/database/models/` — SQLModel ORM models
  - `base/database/manager/` — Database access managers (one per model type)
  - `base/arr_manager/` — Base Radarr/Sonarr integration
  - `base/connection_manager.py` — `BaseConnectionManager` for Arr connections (shared refresh, create/update/delete logic)
  - `radarr/`, `sonarr/` — App-specific logic
  - `plex/` — Plex connection manager, API client, data parser, models
  - `tasks/` — Quiv scheduler setup (`__init__.py`), schedules (`schedules.py`), and task implementations
  - `download/trailers/` — Trailer download orchestration via yt-dlp
  - `files_handler.py` — File management
- `config/settings.py` — Environment-based configuration; settings persisted to `.env` in `APP_DATA_DIR`
- `tests/` — pytest test suite

**Key patterns:**
- All endpoints and background tasks are async/await
- Database migrations auto-applied on startup via `init_db()`
- WebSocket broadcasting for real-time task/event updates
- `APP_DATA_DIR` env var required for all runtime operations
- `EventType` is stored as VARCHAR (`native_enum=False`) — adding new enum values does **not** require an Alembic migration

**Plex ↔ Arr media linking:**
Plex and Arr connections can track the same physical media. The system merges by `folder_path`:
- Plex sync: before creating, checks `read_by_folder_path()` — if an Arr row exists, updates only `plex_*` fields (fires `PLEX_LINKED`)
- Arr sync: before creating, checks `_read_plex_only_by_folder_path()` — if a Plex-only row (`arr_id=0`) exists at the same path, adopts it with Arr fields (fires `ARR_LINKED`)
- When an item is removed from Arr but still in Plex: demoted back to Plex-only (`connection_id → plex_connection_id`, `arr_id → 0`) instead of deleted (fires `ARR_UNLINKED`)
- `media_manager.create_or_update_bulk()` returns `(MediaRead, created, updated, arr_linked)` — 4-tuple

### Frontend (`/app/frontend/src/app/`)

- `app.routes.ts` — Top-level lazy-loaded routes
- `app.config.ts` — Angular app configuration (standalone, zoneless)
- `services/` — API service wrappers (typed, using auto-generated client)
- `media/` — Media list/detail pages (primary feature UI)
- `tasks/`, `settings/`, `logs/`, `events/` — Feature pages
- `shared/` — Shared UI components
- `models/` — TypeScript interfaces
**Key patterns:**
- Standalone components only (no NgModules)
- Angular Signals for reactivity (zoneless change detection)
- Dev server proxies `/api` to backend on port 7888 (see `src/proxy.conf.json`)

### Frontend Styling Conventions

The app uses a **Material Design 3 (MD3)** token system. Always use the established CSS custom properties — never hardcode colors or shadows.

**Color tokens:**
```scss
var(--color-primary)                    // accent / interactive
var(--color-on-primary)                 // text on primary bg
var(--color-secondary-container)        // active tab/nav bg
var(--color-on-secondary-container)     // text on secondary container
var(--color-surface)                    // base surface
var(--color-surface-container-low)      // subtle background
var(--color-surface-container)          // card / dialog background
var(--color-surface-container-high)     // elevated surface
var(--color-surface-container-highest)  // highest elevation surface
var(--color-on-surface)                 // primary text
var(--color-on-surface-variant)         // secondary text / icons
var(--color-outline)                    // borders, meta labels
var(--color-outline-variant)            // subtle dividers
var(--color-success) / --color-warning / --color-danger / --color-info
var(--shadow-level2)                    // sticky headers
var(--shadow-level3)                    // dialogs / popovers
```

**Sticky floating headers** (used in every page — logs, events, tasks, settings):
```scss
.page-header {
  position: sticky;
  top: calc(76px + 0.5rem);   // 76px = topnav height
  z-index: 99;
  margin: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  background-color: var(--color-surface-container);
  box-shadow: var(--shadow-level2);
}
```

**Card sections** (tasks, settings details, about sections):
```scss
.card {
  border: 1px solid var(--color-outline-variant);
  border-radius: 0.75rem;
  background-color: var(--color-surface-container);
  overflow: hidden;           // clips child border-radius
}
.card-header {
  padding: 0.875rem 1rem;
  background-color: var(--color-surface-container-high);
  border-bottom: 1px solid var(--color-outline-variant);
}
```

**Button shapes:**
- **Action buttons (text + icon):** `border-radius: 0.625rem` (10px squircle) — used for Save, Delete, Duplicate, dialog confirm buttons
- **Icon-only buttons:** `border-radius: 50%` (circle) — used for refresh, close, edit pencil
- **Tab / nav items:** `border-radius: 0.5rem` inside a pill container (`border-radius: 0.75rem`)
- **Never** use `border-radius: 9999px` for buttons — that's the pill container shape only

**Button color patterns:**
```scss
// Primary action
background-color: var(--color-primary);
color: var(--color-on-primary);
&:hover { background-color: color-mix(in srgb, var(--color-primary) 85%, black); }

// Secondary / neutral
background-color: var(--color-surface-container-high);
color: var(--color-on-surface);
&:hover { background-color: var(--color-surface-container-highest); }

// Danger (destructive)
background-color: color-mix(in srgb, var(--color-danger) 12%, transparent);
color: var(--color-danger);
&:hover { background-color: color-mix(in srgb, var(--color-danger) 20%, transparent); }

// Icon button hover (generic)
&:hover { background-color: color-mix(in srgb, var(--color-primary) 12%, transparent); }
```

**Dropdowns** — use the CSS Popover API, never custom JS toggles:
```html
<button popovertarget="myDropdown">Label</button>
<div id="myDropdown" popover="auto" class="popover">
  <div class="dropdown-list" role="listbox">
    <button role="option" [attr.aria-selected]="isSelected" (click)="select(item)">...</button>
  </div>
</div>
```
```scss
.popover {
  border: 1px solid var(--color-outline-variant);
  border-radius: 0.75rem;
  margin: 0.25rem 0 0;
  padding: 0.35rem;
  background-color: var(--color-surface-container-high);
  box-shadow: var(--shadow-level3);
}
```

**Dialogs** — use native `<dialog>` with `showModal()` / `.close()`:
```scss
dialog {
  border: none;
  border-radius: 0.75rem;
  background-color: var(--color-surface-container);
  color: var(--color-on-surface);
  padding: 0;
  box-shadow: var(--shadow-level3);
  &::backdrop {
    background-color: rgb(0 0 0 / 50%);
    backdrop-filter: blur(4px);
  }
}
```

**State persistence** (filters, search, selected options) — always persist to both URL and localStorage:
```typescript
// URL: router.navigate([], { queryParams: { key: value ?? null }, replaceUrl: true })
// localStorage: localStorage.setItem('TrailarrFeatureKey', value)
// Priority: localStorage (low) → URL params (high, read with take(1) in ngOnInit)
// Default values are omitted from URL and localStorage (use null to remove param)
```

**Focus rings** on inputs and selects:
```scss
input:focus, select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 25%, transparent);
}
```

**Mobile breakpoints:** `765px` (bottom nav bar replaces sidenav), `1100px` (icon-only rail replaces full sidenav).

### Docker Build

Multi-stage: Stage 1 builds Angular frontend (Node.js), Stage 2 packages backend with Python/FFmpeg. Uses `nandyalu/python-ffmpeg` base image (Python 3.13 + uv + FFmpeg + yt-dlp).

## VSCode Tasks

Pre-configured in `.vscode/tasks.json`:
- **Frontend build** — `npm run build`
- **Fastapi run** — starts FastAPI dev server
- **Generate OpenAPI Files** — updates OpenAPI spec and generates frontend client
- **Create Alembic Migration** — runs `scripts/create_migration.sh`
- **Upgrade Python Dependencies** — `uv sync --upgrade`

## Required Environment Variables

```bash
APP_DATA_DIR=/path/to/config   # Config, database, logs location (REQUIRED)
PYTHONPATH=/path/to/backend    # Required for backend dev/testing
LOG_LEVEL=Info                 # Logging level
```

## Key Conventions

- **Python**: PEP-8, type hints everywhere, async/await, specific exception types, log errors where caught
- **Angular**: Standalone components, Signals for reactivity, SCSS for styles, service-based state
- **API changes**: Always regenerate OpenAPI client after backend API modifications
- **Database changes**: Always create Alembic migration after SQLModel model changes
- **EventType**: stored as VARCHAR — new enum values require no migration, just add to `EventType` in `models/event.py` and add a `track_*` helper in `manager/event/helpers.py`
- **GitHub**: use the `gh` CLI for all GitHub operations (PRs, issues, releases, API) — it is already authenticated in this environment
- **Raw endpoints are a deliberate design, not a cleanup target**: `/media/all_raw`, `/media/downloads_raw`, `/files/files_raw` return raw dicts from SQL on purpose. Data is validated when WRITTEN to the database, so re-validating and building typed Python objects on every read would only add memory pressure and latency on large libraries. Do not "fix" them into typed responses; new list-scale endpoints may follow the same pattern when hot.
- **Docs prose style**: write each sentence/paragraph as ONE continuous line — never hard-wrap prose across multiple lines in `docs/` markdown. Zensical renders continuous lines correctly, but a paragraph broken into separate lines can break formatting. (Code blocks and lists are fine as usual.)
- **Simplified Technical English**: when writing or updating log lines, docs, and comments, follow [ASD-STE100](https://www.asd-ste100.org/) Simplified Technical English. Short sentences, one instruction/idea per sentence, active voice, approved/simple vocabulary, present tense, no strung-together noun clusters. Applies to new/changed content only — no need to rewrite untouched text just to comply.

## Roadmap Execution Plans

The path to v1.0.0 is an 11-phase roadmap (public summary: `docs/references/roadmap.md`).
**Detailed per-phase execution plans live in `plans/`** — before working on any roadmap
phase (download engine, dynamic status, TMDB, video types, reorg, Issues, notifications…),
read `plans/README.md` and the relevant phase file first. Design decisions recorded there
are settled; follow the phase's wargame scenarios, verification protocol, and exit
criteria. Update the phase file's Status line when work starts/finishes.

## After Every Fix / Feature / Update

After completing any bug fix, feature, or notable change, always ask the user:

1. **Release notes** — "Should this be added to the release notes? If so, which version?" Release notes live in `docs/release-notes/2026.md`. Add entries under the appropriate version heading using the existing format (Bug Fixes / What's New / Other Changes sections with emoji).
2. **Docs update** — "Do any documentation pages need to be updated for this change?" Docs live under `docs/`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
