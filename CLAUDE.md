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

### Testing

```bash
# Backend tests (from /app/backend) - ~333 tests, ~6s
# Note: use `uv run python` — plain `python` is not in PATH
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

## After Every Fix / Feature / Update

After completing any bug fix, feature, or notable change, always ask the user:

1. **Release notes** — "Should this be added to the release notes? If so, which version?" Release notes live in `docs/release-notes/2026.md`. Add entries under the appropriate version heading using the existing format (Bug Fixes / What's New / Other Changes sections with emoji).
2. **Docs update** — "Do any documentation pages need to be updated for this change?" Docs live under `docs/`.
