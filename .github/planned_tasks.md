# Planned Tasks

## Overview

| Priority | Task | Complexity |
|---|---|---|
| 1 | Discord Notifications | Low — isolated, no schema conflicts |
| 2 | NFO Files for Trailers | Low — contained to download flow |
| 3 | Plex Integration | Medium — new connector type + library scan |
| 4 | TMDB + Filesystem Connector | High — decouples app from Arr apps entirely |

---

## 1. Discord Notifications

Send notifications to a user-configured Discord webhook channel when configured events occur.

**Design:**
- Store webhook URL + per-event-type toggle in `app_settings` (`config/settings.py`). Use a JSON blob (cleaner since `EventType` is extensible) rather than individual bool properties.
- Hook point: `core/base/database/manager/event/create.py` — after an event is saved, fire the notification. Or hook into wherever events are created in the download flow.
- New file: `core/notifications/discord.py` — `async def send_discord_notification(event: EventCreate, media: MediaRead) -> None` — POSTs to the webhook URL with a Discord embed payload.
- Existing `EventType` values in `core/base/database/models/event.py` map directly to notification triggers: `TRAILER_DOWNLOADED`, `TRAILER_DELETED`, `MEDIA_ADDED`, etc.

**Frontend:**
- New settings section: webhook URL input + checkboxes per event type.
- Follows existing settings page pattern.

**Risk:** Discord webhook calls must not block or fail in a way that breaks the download flow — wrap in `try/except` and log errors.

---

## 2. NFO Files for Trailers

Create Kodi/Jellyfin/Emby-compatible `.nfo` files alongside downloaded trailers.

**Schema change:**
- Add `create_nfo: bool = False` to `TrailerProfile` (`core/base/database/models/trailerprofile.py`).
- Requires a new Alembic migration.

**Implementation:**
- New utility: `core/files/nfo_writer.py` — takes `MediaRead` + trailer file path, writes `{filename}.nfo` with standard XML (title, year, overview, imdbid, tmdbid, studio, etc.).
- Write point: after the trailer file is saved in the download completion flow (`core/download/trailers/service.py` or `FilesHandler`), if `profile.create_nfo` is True, call the NFO writer.

**Naming convention:** NFO filename must exactly match the trailer filename (minus extension) to be picked up by media servers — e.g., `Movie (2023)-trailer.nfo` alongside `Movie (2023)-trailer.mkv`. This follows the existing `file_name` template in `TrailerProfile`.

**Available metadata on `MediaRead`:** title, year, overview, imdb_id, txdb_id, studio — enough for a complete NFO.

---

## 3. Plex Integration

Add Plex as a connector alongside Radarr/Sonarr. Can work standalone (no Arr apps needed) or alongside them (enriches existing media items). Triggers Plex library scans after trailer download/delete.

**Prior work:** Branch `copilot/fix-87efcdd2-f25b-409c-9e92-81e7ff32f57e` + stashes named `plex` contain early-phase work. Key reusable pieces from the stashes:
- `core/plex/api.py` — `PlexAPI` class (clean async wrapper, keep with fixed imports)
- `core/plex/models.py` — `PlexLibrarySection`, `PlexMediaItem`, `PlexMediaExtra` Pydantic models (keep as-is)
- `core/plex/auth.py` — `start_auth_flow()`, `poll_for_token()`, `get_server_address()` logic → **port to frontend TypeScript**, do not keep as backend endpoints
- Debug JSON files (`debug_media_items_*.json`, `extras.json`, etc.) — **do not commit**

---

### 3A. Backend

#### Schema Changes

**`core/base/database/models/connection.py`:**
- Add `PLEX = "plex"` to `ArrType` enum.
- `url` holds the Plex server address; `api_key` holds the Plex token. No new columns on `Connection`.
- Alembic migration required.

**`core/base/database/models/media.py` — three new nullable columns:**
- `plex_rating_key: str | None = None` — Plex `ratingKey` for the item; used for per-item scan/extras calls.
- `plex_section_key: str | None = None` — Plex library section key; used for section-level scan.
- `plex_connection_id: int | None` — nullable FK to `Connection.id` (with `ondelete="SET NULL"`). Present on ALL media items (Arr and Plex-only alike) so the library scan trigger always knows which Plex server to call.
- Alembic migration required.

**`connection_id` and `plex_connection_id` rules:**
- Media sourced from Radarr/Sonarr: `connection_id` = Arr connection, `plex_connection_id` = Plex connection (set when Plex sync merges the item).
- Media sourced from Plex only (no Arr match by `folder_path`): `connection_id` = Plex connection, `plex_connection_id` = same Plex connection. `arr_id` = 0.
- When a Plex connection is deleted: `plex_connection_id` → NULL on all merged Arr items (cascade SET NULL); Plex-only items cascade delete (via `connection_id` FK).

#### New Files

- `core/plex/api_manager.py` — rename/adapt `core/plex/api.py` from stash. Fix `from models import` → `from core.plex.models import`. This is the equivalent of `RadarrManager`/`SonarrManager`.
- `core/plex/data_parser.py` — `parse_plex_item(item: PlexMediaItem, connection_id: int) -> MediaCreate`. Maps `PlexMediaItem` fields to `MediaCreate`. `arr_id=0`, `plex_rating_key=item.ratingKey`, `plex_section_key` from the library section, `txdb_id` from `item.tmdb_id`, `imdb_id` from `item.imdb_id`, etc.
- `core/plex/connection_manager.py` — `PlexConnectionManager`. `refresh()` logic:
  1. Call `PlexAPI.get_libraries()` to get all sections.
  2. For each section, call `PlexAPI.get_library_media(section_key)` to get items.
  3. Apply path mappings (same as Arr: translate Plex-side paths to Trailarr-side paths).
  4. For each `PlexMediaItem`, look up existing `Media` by `folder_path`.
     - **Match found:** update `plex_rating_key`, `plex_section_key`, `plex_connection_id` on the existing row. Do not overwrite Arr fields.
     - **No match:** create new `Media` via `parse_plex_item()` with `connection_id` = Plex connection.

#### Existing Files to Modify

- `core/base/database/manager/connection/base.py` — add `PLEX` branch to `validate_connection()` (calls `PlexAPI.validate_token()`) and `get_rootfolders()` (calls `PlexAPI.get_library_folders()` — returns the `Location` paths from all sections, same role as Arr rootfolders).
- `core/tasks/api_refresh.py` — add `PLEX` branch to `api_refresh_by_id()` to instantiate `PlexConnectionManager`.
- `core/download/trailers/` (download completion) — after trailer download/delete, if `media.plex_connection_id` is set, look up that connection, instantiate `PlexAPI`, call `PlexAPI` section or item refresh. Controlled by `notify_plex` on `TrailerProfile` (field already exists).

#### Library Scan Trigger

After a trailer is downloaded or deleted:
1. Check `profile.notify_plex` — if False, skip.
2. Check `media.plex_connection_id` — if None, skip.
3. Load the Plex connection by `plex_connection_id`.
4. Call `PlexAPI(url, token).get_query_json(f"/library/metadata/{media.plex_rating_key}/refresh", type="PUT")` for a targeted item refresh. Fallback: section-level refresh using `plex_section_key`.

---

### 3B. Frontend

#### Connections Page — Add Flow

When user clicks the Add button on the connections page, show a **type picker** with two options:
- **Radarr / Sonarr** → navigates to existing `edit-connection` component (no changes there).
- **Plex** → navigates to new `edit-plex-connection` component.

This avoids complicating the existing `edit-connection` form with Plex-specific OAuth logic.

#### New Component: `edit-plex-connection`

Location: `frontend/src/app/settings/connections/edit-plex-connection/`

**OAuth state machine** (ported from `auth.py` stash + `plex-integration.component.ts` stash):

```
idle
  → [Connect with Plex] clicked
pending_pin
  → POST https://plex.tv/api/v2/pins → get { id, code, auth_url }
  → open auth_url in new tab
  → poll https://plex.tv/api/v2/pins/{id} every 2s
pending_auth (user must approve in new tab)
  → on authToken received:
    → GET https://clients.plex.tv/api/v2/resources (local connections only)
    → build list of available servers
server_select (if >1 server; auto-advance if exactly 1)
  → user picks server
authenticated
  → url and api_key (token) set; [Reconnect] option available
```

After `authenticated`, the form shows:
- Name field (editable)
- Monitor Type selector
- Server URL (read-only, from OAuth)
- Plex Token (read-only, from OAuth; masked)
- Path Mappings (populated via `GET /api/v1/connections/rootfolders` → `PlexAPI.get_library_folders()`)
- Test → Save flow using existing `POST /api/v1/connections/test` and `POST /api/v1/connections`

**New service: `plex-oauth.service.ts`** — all direct plex.tv HTTP calls (PIN request, polling, resource discovery). Keeps OAuth logic separate from the component.

#### Model / Enum Changes

- `frontend/src/app/models/connection.ts` — add `Plex = 'plex'` to `ArrType` enum.
- Form validation for `api_key` must be conditional: Plex tokens are ~20 chars alphanumeric (relax the 32-char minimum when `arr_type === ArrType.Plex`).

#### `show-connections` Component

- The existing connections list already renders all connection types generically — no changes needed there beyond the new type label rendering correctly.
- Edit route for a Plex connection (`/settings/connections/plex/{id}`) should load `edit-plex-connection` rather than `edit-connection`. Route guard or the routing config handles this.

---

## 4. TMDB Integration + Filesystem Connector

Decouple the app from Arr apps entirely — scan folders, resolve metadata from TMDB, and work with the rest of the app without any Radarr/Sonarr/Plex connection.

### Sub-task A: TMDB Integration (prerequisite)

- New file: `core/tmdb/api_manager.py` — wraps TMDB v3 REST API.
  - Key endpoints: `/search/movie`, `/search/tv`, `/movie/{id}`, `/tv/{id}`, `/movie/{id}/images`.
  - API key stored in `app_settings` (global, not per-connection).
- The `txdb_id` field on `Media` (`core/base/database/models/media.py`) is the correct slot for TMDB IDs.

### Sub-task B: Filesystem Connector

**Approach:** Add `FILESYSTEM = "filesystem"` to `ArrType` and reuse the existing Connection infrastructure. The `url` field stores the root folder path; `api_key` is unused. No DB schema changes beyond the enum value addition.

This approach is preferred over creating a separate concept because it leverages all existing connection/media/manager/filtering/download infrastructure without modification.

**New files:**
- `core/filesystem/connection_manager.py` — `refresh()` walks the folder path, identifies movie/series folders (by year-in-name pattern etc.), calls TMDB to resolve metadata, upserts `MediaCreate` into DB.
- `core/filesystem/data_parser.py` — converts TMDB API response + local path into `MediaCreate`.

**Existing files to modify:**
- `core/base/database/manager/connection/base.py` — add `FILESYSTEM` branch to `validate_connection()` (checks path exists + TMDB API key is configured) and `get_rootfolders()` (returns configured path).
- `core/tasks/api_refresh.py` — add `FILESYSTEM` branch to instantiate `FilesystemConnectionManager`.

**Edge cases:**
- `arr_id` (FK-like integer from Arr apps) → use TMDB integer ID.
- `arr_monitored` field doesn't apply meaningfully to filesystem connections — treat as always `True`.
- Folder matching heuristics need to handle both flat (`/movies/Title (Year)/`) and nested layouts.
