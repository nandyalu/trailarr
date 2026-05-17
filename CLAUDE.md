# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Trailarr** is a Docker-based application that automates downloading and managing trailers for Radarr and Sonarr media libraries. Plex is a first-class connection type that works alongside Arr connections. Emby and Jellyfin are also supported.

- **Backend**: Python 3.13 + FastAPI + SQLModel + Alembic + SQLite
- **Frontend**: Angular 21 (standalone components, Signals) + TypeScript strict mode
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
mkdir -p /tmp/trailarr-config/web
APP_DATA_DIR=/tmp/trailarr-config uv run alembic upgrade head
PYTHONPATH=$(pwd) APP_DATA_DIR=/tmp/trailarr-config uvicorn main:trailarr_api --host 0.0.0.0 --port 7888

# FastAPI also exposes the frontend (static build) at the root (localhost:7888) when running. Make sure you run `ng build` in frontend dir on changes.

# Angular frontend (from /app/frontend) - proxies API to localhost:7888
npm run start   # http://localhost:4200

```

### Database Setup

```bash
# Required before running the backend server (from /app/backend)
mkdir -p /tmp/trailarr-config/web
APP_DATA_DIR=/tmp/trailarr-config uv run alembic upgrade head
```

### Testing

```bash
# Backend tests (from /app/backend) - ~720 tests, ~6s
# Note: use `uv run python` — plain `python` is not in PATH
# Tests use an in-memory SQLite DB; APP_DATA_DIR is NOT required for tests
PYTHONPATH=$(pwd) uv run python -m pytest tests/ -v
PYTHONPATH=$(pwd) uv run python -m pytest tests/path/to/test_file.py -v   # single file

# Frontend tests (from /app/frontend) - ~13s
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

### Database Migrations

```bash
# From /app/backend
uv run alembic revision --autogenerate -m "Description of changes"
uv run alembic upgrade head
```

## Architecture

### Backend (`/app/backend/`)

Strict layered architecture — each layer only calls the layer below it:

```
api/  →  services/  →  db/repos/  →  db/models/
           ↓
       integrations/   download/   utils/
```

**Top-level files:**
- `main.py` — FastAPI app entry point (`trailarr_api`), lifespan, middleware
- `app_logger.py` — Structured logging setup
- `exceptions.py` — Custom exception types

**`db/` — Pure data layer (no business logic)**
- `engine.py` — SQLite engine, WAL mode, session factory
- `init_db.py` — DB init + Alembic migration on startup
- `models/` — One SQLModel file per domain (`connection.py`, `media.py`, `event.py`, `trailerprofile.py`, `mediatrailerstatus.py`, `issue.py`, `customfilter.py`, `download.py`, `filefolderinfo.py`, `task_config.py`)
- `repos/` — One module per model; pure DB access only, no business logic (`connection.py`, `media.py`, `event.py`, `trailer_profile.py`, `trailer_status.py`, `issue.py`, `custom_filter.py`, `download.py`, `file_info.py`, `task_config.py`, `stats.py`)

**`services/` — Business logic layer**
- `connection_service.py` — validate, rootfolders, CRUD, `refresh_connection` with failure tracking
- `arr_connection_manager.py` — `BaseConnectionManager`; Arr/Plex refresh orchestration (parse → upsert → monitor → clean up)
- `media_service.py` — monitor toggle, batch update, yt-id update
- `event_service.py` — `track_*` helpers; all event tracking is fire-and-forget (exceptions swallowed)
- `files_service.py` — `FilesHandler` filesystem utilities; `delete_trailer_download` service action
- `image_service.py` — poster/fanart refresh orchestration
- `tmdb_service.py` — TMDB video lookup, YouTube key extraction
- `trailer_profile_service.py` — CRUD + `_sync_status_rows` after every write
- `scan_service.py` — media scan orchestration
- `issue_service.py` — upsert/resolve pass-through to repo
- `plex_service.py` — Plex-specific media refresh
- `cleanup_service.py` — trailer file verification and cleanup

**`integrations/` — External API clients**
- `arr/http.py` — `AsyncRequestManager` (base HTTP client for Arr APIs)
- `arr/base.py` — `AsyncBaseArrManager` (shared Radarr/Sonarr methods)
- `arr/radarr.py` — `RadarrManager` + data parser + connection manager
- `arr/sonarr.py` — `SonarrManager` + data parser + connection manager
- `plex/client.py` — Plex HTTP client
- `plex/models.py` — Plex-specific data models
- `plex/parser.py` — `parse_plex_item()`
- `plex/sync.py` — `PlexConnectionManager`

**`download/` — Trailer download pipeline**
- `pipeline.py` — Orchestration: search → download → analyse → move → record
- `search.py` — YouTube search via yt-dlp
- `video.py` — `download_video()` via yt-dlp
- `analysis.py` — `VideoInfo`, `get_media_info()` via ffprobe
- `filename.py` — `get_trailer_filename()` / `get_trailer_path()`
- `conversion.py` — Video conversion via ffmpeg
- `image.py` — `refresh_media_images()` via aiohttp

**`tasks/` — Scheduler entry points only (no business logic)**
- `scheduler.py` — Quiv init + WS event listeners
- `schedules.py` — `TASK_REGISTRY`, `schedule_all_tasks()`
- `api_refresh.py`, `files_scan.py`, `image_refresh.py`, `cleanup.py`, `plex_refresh.py`, `tmdb_refresh.py` — thin wrappers that call services

**`ws/` — WebSocket**
- `manager.py` — `WSConnectionManager` singleton; `broadcast()` for bulk ops

**`api/v1/` — HTTP + WebSocket endpoints**
- `routes.py` — Aggregates all routers
- `deps.py` — `validate_api_key`, session deps
- `ws_endpoint.py` — `/ws/{client_id}` WebSocket endpoint
- `endpoints/` — One file per domain (media, connections, files, events, settings, tasks, trailer_profiles, custom_filters, issues, logs, auth)

**`config/settings.py`** — `_Config` singleton; settings persisted to `.env` in `APP_DATA_DIR`

**`utils/`** — Shared helpers
- `path_utils.py` — Path mapping, subpath checks, trailing-slash normalisation
- `filters.py` — `matches_filters()` for custom filter evaluation
- `media_scanner.py` — `MediaScanner` for filesystem scan
- `docker_check.py` — Docker environment detection

**Key patterns:**
- All endpoints and background tasks are async/await
- DB sessions (`@read_session` / `@write_session`) are applied only in `db/repos/` — never in services or above
- Database migrations auto-applied on startup via `init_db()`
- WebSocket broadcasting for real-time task/event updates
- `APP_DATA_DIR` env var required for all runtime operations (not needed for tests)
- `EventType` is stored as VARCHAR (`native_enum=False`) — adding new enum values does **not** require an Alembic migration
- `TrailerStatusEnum` and `TrailerSourceEnum` (in `db/models/mediatrailerstatus.py`) are also VARCHAR — same rule applies
- `IssueType` and `EntityType` (in `db/models/issue.py`) are also VARCHAR — same rule applies

**Trailer tracking:**
- `Media.trailer_exists` and `Media.status` (MonitorStatus) are **not** in the DB model — the frontend derives them from `MediaTrailerStatus` rows
- `MediaTrailerStatus` is the source of truth: one row per `(media_id, profile_id, season, sequence)`
- `Issue` records actionable problems (missing files, failed connections) — auto-created and auto-resolved by the app
- `downloaded_at IS NOT NULL` on `Media` is used as a proxy for "has trailer" in filters and stats

**Plex ↔ Arr media linking:**
Plex and Arr connections can track the same physical media. The system merges by `folder_path`:
- Plex sync: before creating, checks `read_by_folder_path()` — if an Arr row exists, updates only `plex_*` fields (fires `PLEX_LINKED`)
- Arr sync: before creating, checks `_read_plex_only_by_folder_path()` — if a Plex-only row (`arr_id=0`) exists at the same path, adopts it with Arr fields (fires `ARR_LINKED`)
- When an item is removed from Arr but still in Plex: demoted back to Plex-only (`connection_id → plex_connection_id`, `arr_id → 0`) instead of deleted (fires `ARR_UNLINKED`)
- `media_repo.create_or_update_bulk()` returns `(MediaRead, created, updated, arr_linked)` — 4-tuple

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
- **Create Alembic Migration** — runs `scripts/create_migration.sh`
- **Upgrade Python Dependencies** — `uv sync --upgrade`

## Required Environment Variables

```bash
APP_DATA_DIR=/path/to/config   # Config, database, logs location (REQUIRED for server; not needed for tests)
PYTHONPATH=/path/to/backend    # Required for backend dev/testing
LOG_LEVEL=Info                 # Logging level
TMDB_API_KEY=                  # Optional: TMDB v3 API key for trailer metadata lookups
```

**Quick dev setup (all in one):**
```bash
cd /app/backend
mkdir -p /tmp/trailarr-config/web
APP_DATA_DIR=/tmp/trailarr-config uv run alembic upgrade head
PYTHONPATH=$(pwd) APP_DATA_DIR=/tmp/trailarr-config uvicorn main:trailarr_api --host 0.0.0.0 --port 7888
```

## Key Conventions

- **Python**: PEP-8, type hints everywhere, async/await, specific exception types, log errors where caught
- **Angular**: Standalone components, Signals for reactivity, SCSS for styles, service-based state
- **Database changes**: Always create Alembic migration after SQLModel model changes
- **EventType**: stored as VARCHAR — new enum values require no migration, just add to `EventType` in `db/models/event.py` and add a `track_*` helper in `services/event_service.py`
- **TrailerStatusEnum / TrailerSourceEnum / IssueType / EntityType**: also stored as VARCHAR — same rule, no migration needed for new values
- **Do not add `trailer_exists` or `status` (MonitorStatus) back to `Media`** — intentionally absent; the frontend derives them from `MediaTrailerStatus` rows

## After Every Fix / Feature / Update

After completing any bug fix, feature, or notable change, always ask the user:

1. **Release notes** — "Should this be added to the release notes? If so, which version?" Release notes live in `docs/release-notes/2026.md`. Add entries under the appropriate version heading using the existing format (Bug Fixes / What's New / Other Changes sections with emoji).
2. **Docs update** — "Do any documentation pages need to be updated for this change?" Docs live under `docs/`.
