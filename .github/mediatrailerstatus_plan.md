# Plan: MediaTrailerStatus — Per-Profile Trailer Tracking

## Context

Currently `Media.trailer_exists` (bool) and `Media.status` (MonitorStatus) are single values per media item. With multiple TrailerProfiles, the system needs per-profile, per-season, per-sequence granularity: which profile has a video for which season and sequence index, what is its status, and how was it obtained. This plan introduces a `MediaTrailerStatus` join table as the single source of truth, moves `trailer_exists` and `MonitorStatus` computation to the frontend, and adds season-aware, movie/series-scoped, video-type-aware, and TMDB-sourced profile support.

---

## 1. New Model: `MediaTrailerStatus`

**File:** `backend/core/base/database/models/mediatrailerstatus.py` (new)

Fields:
- `id: int` — primary key
- `media_id: int` — FK → `media.id`, cascade delete
- `profile_id: int | None` — FK → `trailerprofile.id`, SET NULL on delete (NULL = manually placed, unattributed)
- `season: int` — `0` = movie or series-level; `1..N` = season-specific
- `sequence: int` — `1..max_count`; disambiguates multiple results per `(media, profile, season)`
- `status: enum` — `PENDING | DOWNLOADING | DOWNLOADED | FAILED | SKIPPED | UNMONITORED | NOT_AVAILABLE`
- `source: enum` — `APP | MANUAL`
- `linked_download_id: int | None` — FK → `download.id`, SET NULL on delete
- `created_at: datetime`
- `updated_at: datetime`

Unique constraint: `(media_id, profile_id, season, sequence)`.

Read model includes `profile_name` and `video_type` joined from the profile for display purposes.

**Status rules:**
- `UNMONITORED` — set only by the user, never overwritten by the app or filter reapplication
- `NOT_AVAILABLE` — set by the app when TMDB returns no results for a non-trailer `video_type`; rechecked on the weekly TMDB task; never set for `video_type = "trailer"` (YouTube search is the fallback)
- `SKIPPED` — set by the app when `stop_monitoring=True` on a sibling profile that succeeded
- `FAILED` — set after all retries exhausted

---

## 2. Changes to `TrailerProfile`

**File:** `backend/core/base/database/models/trailerprofile.py`

Add to `_TrailerProfileBase`:
- `video_type: VideoType = VideoType.TRAILER` — enum: `Trailer | Teaser | Clip | Behind the Scenes | Bloopers | Featurette | Opening Credits`
- `for_movies: bool = True` — `True` = movies only, `False` = series only
- `download_season_videos: bool = False` — only meaningful when `for_movies=False`; creates per-season rows for all video types
- `max_count: int = 1` — how many top-voted TMDB results to download per `(media, profile, season)`; pre-creates `max_count` sequence rows

### `for_movies` migration auto-detection (applied once on migration; validated on profile creation):
1. If any filter has `is_movie = True` → set `True`
2. Elif any filter has `is_movie = False` → set `False`
3. Elif profile name (lowercased) contains `movie/movies/radarr` → set `True`
4. Elif profile name contains `series/show/sonarr` → set `False`
5. Else → set `True` and `enabled = False` (user must review and re-enable)

Add `for_movies`, `download_season_videos` to `is_bool_field()`. Add `max_count` to `is_int_field()`.

> **Docs:** Update `docs/user-guide/settings/profiles/settings/general.md` — add `Video Type`, `Scope (for_movies)`, `Download Season Videos`, `Max Count` fields with descriptions and valid values. Update `docs/user-guide/settings/profiles/index.md` — add a paragraph explaining that profiles now have a scope (Movies / Series) and video type, and that a profile applies only to matching media.

### Row creation pattern (mirrors season_count logic):
- Movies / series with `download_season_videos=False`: `max_count` rows, `season=0`, `sequence=1..max_count`
- Series with `download_season_videos=True`: `(season_count + 1) × max_count` rows, `season=0..N`, `sequence=1..max_count`

---

## 3. Changes to `Media`

**File:** `backend/core/base/database/models/media.py`

- Remove `trailer_exists` and `status` (MonitorStatus) from the DB model entirely.
- Keep `monitor: bool` as the master kill switch.
- The frontend receives `MediaTrailerStatus` rows alongside each `Media` and computes locally:
  - `trailer_exists = any(s.status == DOWNLOADED and s.profile.video_type == "trailer" for s in statuses)`
  - `MonitorStatus`:
    - Any `DOWNLOADING` → `DOWNLOADING`
    - Any `DOWNLOADED` (none downloading) → `DOWNLOADED`
    - `monitor=True` and any `PENDING` → `MONITORED`
    - Otherwise → `MISSING`
- The download loop queries `MediaTrailerStatus` directly — `Media.status` is never consulted.
- Alembic migration drops `trailer_exists` and `status` columns from the `media` table.

---

## 4. New Setting: TMDB API Key

**File:** `backend/config/settings.py`

- Add `tmdb_api_key: str = ""` to app settings (env var + UI settings page).
- Non-trailer profiles with no API key configured stay `PENDING` and log a clear warning rather than silently failing.
- Profile create/edit UI warns when `video_type != "trailer"` and no API key is set.

> **Docs:** Update `docs/user-guide/settings/general-settings/index.md` — add `TMDB API Key` under a new **Integrations** heading; explain it is required for non-trailer video types and where to obtain a free key.

---

## 5. Filter Application Logic

**File:** `backend/core/base/database/manager/trailerstatusmanager.py` (new)
**Also touches:** `backend/core/base/database/manager/trailerprofile.py`

### On profile create or filter update:
1. Compute / validate `for_movies`.
2. Query all existing media matching `for_movies` + custom filters.
3. For **matching** media: create rows if they don't already exist (respects `UNMONITORED` — never overwrites).
4. For **non-matching** media (filter changed):
   - Delete rows where `linked_download_id IS NULL`.
   - Keep rows where `linked_download_id IS NOT NULL` (preserve downloaded files).

### On `season_count` increase (Sonarr sync):
- For each profile with `download_season_videos=True` matching this media, append rows for new seasons × `max_count` sequences. Existing rows untouched.

### On `max_count` increase (profile edit):
- Append new sequence rows for all matching media. Existing rows untouched.

### On profile delete:
- Rows with no linked download: cascade deleted.
- Rows with a linked download: `profile_id` set to NULL (preserved as unattributed MANUAL).

---

## 6. Download Loop Redesign

**File:** `backend/core/download/trailers/missing.py`

Query `MediaTrailerStatus` rows where `status = PENDING` and `media.monitor = True`, ordered by `profile.priority ASC`, then `media_id`, then `sequence ASC`.

For each row:
- If `video_type == "trailer"`: check TMDB first (use returned YouTube key directly); fall back to YouTube search if TMDB has no result.
- If `video_type != "trailer"`: TMDB only. If TMDB returns no result, set row `status = NOT_AVAILABLE` and continue — no YouTube search.
- On success: set `status = DOWNLOADED`, `source = APP`, link the `Download` record.
- On failure after retries: set `status = FAILED`.
- If `profile.stop_monitoring=True` and row succeeds: set all other `PENDING` rows for the same `media_id` to `SKIPPED`.

Template variables `{season}` (when `season > 0`), `{sequence}` (when `max_count > 1`), and `{video_type}` added to `VALID_YT_DICT` and `VALID_FILE_DICT`.

---

## 7. New Weekly Task: Refresh TMDB Videos

**File:** `backend/core/tasks/tmdb_refresh.py` (new)

Mirrors the Plex trailer flags refresh task pattern. Runs weekly:
1. For each monitored media item with any `PENDING` or `NOT_AVAILABLE` rows where the profile's `video_type != "trailer"`:
   - Query TMDB videos endpoint for that media's TMDB ID.
   - For each matching profile row in `PENDING` or `NOT_AVAILABLE`: if TMDB now has results, reset to `PENDING` so the download loop picks it up; if still no results, set/keep `NOT_AVAILABLE`.
   - Mark `sequence` rows beyond the actual TMDB result count as `NOT_AVAILABLE`.
2. For `video_type == "trailer"` rows, also check TMDB to cache the YouTube key — avoids a search when the download loop runs.
3. Paginate with a small sleep between requests (good TMDB API citizenship).

> **Docs:** Update `docs/user-guide/tasks/index.md` — add entry for **Refresh TMDB Videos** task: what it does, default schedule (weekly), and that it requires a TMDB API key.

---

## 8. File Scanner Changes

**File:** `backend/core/tasks/files_scan.py` and `backend/core/files_handler.py`

When a video file is detected that is not already in `Download` records:

**Tier 1 — Template match:**
- For each enabled profile applying to this media, reverse the `file_name` template into a pattern (using `video_type`, `season`, `sequence` placeholders).
- If matched: set the row `status = DOWNLOADED`, `source = MANUAL`, create and link a `Download` record.

**Tier 2 — Metadata match (files unmatched by Tier 1):**
- Run `ffprobe` (already done for new files to create `Download` records).
- Use `get_resolution_label(height)` from `backend/core/download/trailers/service.py:25`.
- A file satisfies a profile if:
  - `get_resolution_label(file.height) >= profile.video_resolution` (4K satisfies a 1080p profile)
  - `file.duration` is within `profile.min_duration..profile.max_duration`
  - Codec and audio format are **not** checked for manual files
- Mark **all** satisfied profiles as `DOWNLOADED, source=MANUAL` (prevents duplicate downloads for all matching profiles).
- `UNMONITORED` rows are never overwritten.

**Unattributed files (no profile matched):**
- Create a `MediaTrailerStatus` row with `profile_id=NULL, source=MANUAL, status=DOWNLOADED`.
- Matched profiles' own `PENDING` rows remain — download loop will attempt them (the file doesn't meet their requirements).

**On file disappearance — external deletion (detected by scanner):**
- The `MediaTrailerStatus` row stays `DOWNLOADED` — the slot still knows what was there.
- Create an `Issue` of type `FILE_DELETED` for this `MediaTrailerStatus` row (see §12 Issues System). One issue per row; if it already exists, skip.
- `UNMONITORED` rows: no issue created — user already opted out.
- If the file is found again on a subsequent scan: delete the issue row and leave the status as `DOWNLOADED`.

**On file disappearance — app-initiated deletion (two sub-cases, no issue created):**

*Sub-case A: User deletes the `Download` record via the app.*
The FK `linked_download_id → download.id` is `ON DELETE SET NULL`. When the `Download` row is deleted, `linked_download_id` becomes `NULL` but `status` remains `DOWNLOADED`. The download manager's delete path must explicitly call `update_row_status(row_id, PENDING)` — this is intentional, no issue created.

*Sub-case B: User deletes just the file (Download record survives with `file_exists=False`).*
The app's file-delete action must immediately call `update_row_status(row_id, PENDING)` — intentional, no issue created.

**Unattributed rows (`profile_id=NULL`) on external file deletion:**
- Create a `FILE_DELETED` issue as above. The row stays as a record that a manual file existed here.

---

## 9. New Database Manager

**File:** `backend/core/base/database/manager/trailerstatusmanager.py` (new)

Key functions:
- `create_rows_for_profile(profile, media_list)` — batch insert rows per season × sequence
- `delete_undownloaded_rows_for_profile(profile_id, media_ids)` — cleanup on filter change
- `get_pending_rows(limit)` — for download loop (excludes UNMONITORED, NOT_AVAILABLE, SKIPPED, and rows where `profile_id IS NULL`)
- `update_row_status(row_id, status, download_id?)` — single status update
- `get_rows_for_media(media_id)` — for API / frontend
- `on_download_deleted(download_id)` — called by the download manager's delete path (app-initiated); resets matching `DOWNLOADED` rows to `PENDING` (skips `UNMONITORED`); no issue created
- `on_file_deleted(download_id)` — called by the file-delete API path (app-initiated); same reset, no issue created

Remove from `media_manager.py`: `update_trailer_exists()`, `update_no_trailers_exist()`.

---

## 10. API Changes

**File:** `backend/api/v1/` (media and profile routes)

- `GET /media/{id}/trailer-status` — returns list of `MediaTrailerStatusRead` (profile name, video type, season, sequence, status, source, linked download info)
- Profile create/update response includes `{ "rows_created": N, "rows_deleted": M }`
- `PATCH /media/{id}/trailer-status/{status_id}` — allows user to set `UNMONITORED` (or reset to `PENDING`)

---

## 11. Alembic Migration

1. Create `mediatrailerstatus` table with all fields including `sequence`.
2. Add `video_type`, `for_movies`, `download_season_videos`, `max_count` columns to `trailerprofile`.
3. Backfill `for_movies` on all existing profiles using auto-detection logic; disable profiles where it cannot be determined.
4. Set `video_type = "trailer"` and `max_count = 1` on all existing profiles.
5. Backfill `MediaTrailerStatus` rows from existing `Download` records (`status=DOWNLOADED, source=APP, sequence=1`).
6. For media where `trailer_exists=True` but no `Download` record: create row with `profile_id=NULL, source=MANUAL, status=DOWNLOADED, sequence=1`.
7. For all monitored media with no rows: create `PENDING` rows by applying current profile filters.
8. Drop `trailer_exists` and `status` columns from `media` table.

---

## 12. Issues System

### Model

**File:** `backend/core/base/database/models/issue.py` (new)

Fields:
- `id: int` — primary key
- `issue_type: IssueType` — enum (VARCHAR, no migration needed for new types)
- `entity_type: EntityType` — enum: `media_trailer_status | connection | download`
- `entity_id: int` — ID of the affected entity
- `description: str` — human-readable message surfaced in the UI
- `details: str | None` — optional JSON blob for extra context (error text, file path, etc.)
- `created_at: datetime`
- `updated_at: datetime` — updated when the same issue is detected again (tracks recurrence)

Unique constraint: `(issue_type, entity_type, entity_id)` — enforces one active issue per entity per type.

**`IssueType` values (initial scope):**
- `FILE_DELETED` — trailer file disappeared externally; requires user to re-download or skip
- `CONNECTION_FAILED` — Arr/Plex connection refresh failed repeatedly (not a one-off transient error)
- `TOKEN_INVALID` — Arr/Plex API token rejected; requires user to update credentials
- `FOLDER_MISSING` — media folder path is no longer accessible

**What does NOT create an issue:**
- Transient download failures (handled by `FAILED` status + retry logic)
- A single failed Arr/Plex refresh (only after N consecutive failures)
- App-initiated file/download deletions (intentional)

### Database Manager

**File:** `backend/core/base/database/manager/issuemanager.py` (new)

Key functions:
- `create_or_skip(issue_type, entity_type, entity_id, description, details?)` — idempotent: inserts if not exists, updates `updated_at` if already exists; returns the row either way
- `resolve(issue_type, entity_type, entity_id)` — deletes the row; called when the condition clears
- `resolve_all_for_entity(entity_type, entity_id)` — deletes all issues for a given entity (e.g., when a connection is deleted)
- `get_all_open()` — for the issues API endpoint
- `get_for_entity(entity_type, entity_id)` — for detail pages

### Where Issues Are Created and Resolved

| Trigger | Issue type | Created when | Resolved when |
|---|---|---|---|
| File scanner detects missing file | `FILE_DELETED` | `file_exists=False` on a tracked Download | File found again on subsequent scan |
| Arr/Plex refresh fails | `CONNECTION_FAILED` | N consecutive refresh failures (configurable, default 3) | Next successful refresh |
| Arr/Plex token rejected (401/403) | `TOKEN_INVALID` | Auth error on any API call | Successful API call after token update |
| Media folder inaccessible | `FOLDER_MISSING` — entity: `media_trailer_status` | Folder check fails during download attempt | Folder accessible again on next attempt |

Connection manager already has retry/failure logic — wire issue creation into the existing failure path after the threshold is exceeded.

### API

- `GET /api/v1/issues/` — returns all open issues (with entity details joined for display)
- `DELETE /api/v1/issues/{id}` — user dismisses an issue without taking action (deletes the row; it may reappear if the condition persists)

Issue-specific actions are handled by existing endpoints (e.g., re-download via `/media/{id}/download`, update connection via `/connections/{id}`).

> **Docs:** Create `docs/user-guide/activity/issues/index.md` — explain what issues are, how they differ from events/logs (issues require user action; auto-resolve when condition clears), list each `IssueType` with its trigger, what the user should do, and available action buttons. Note that dismissing an issue may cause it to reappear if the underlying condition persists.

---

---

# Part 2: Frontend Changes

---

## F1. New & Updated TypeScript Models

**File:** `frontend/src/app/models/media.ts`

- Remove `trailer_exists: boolean` and `status: string` from the `Media` interface.
- Add `trailer_statuses: MediaTrailerStatus[]` to `Media`.
- Add computed helpers alongside `mapMedia()`:
  - `computeTrailerExists(statuses)` — `true` if any row has `status == 'downloaded'` AND `video_type == 'trailer'`
  - `computeMonitorStatus(statuses, monitor)` — returns `'downloading' | 'downloaded' | 'monitored' | 'missing'` using the same logic as §3 of the backend plan
- Update `mapMedia()` to call these helpers and attach `trailer_exists` and `status` as local computed properties on the mapped object (not sent by backend, derived client-side). These preserve the same contract as before — all existing filters, icons, and display logic continue to work unchanged.

**New file:** `frontend/src/app/models/mediatrailerstatus.ts`

```
MediaTrailerStatus {
  id: number
  media_id: number
  profile_id: number | null
  profile_name: string | null   // joined from profile
  video_type: VideoType | null  // joined from profile
  season: number
  sequence: number
  status: TrailerStatusEnum     // 'pending' | 'downloading' | 'downloaded' | 'failed' | 'skipped' | 'unmonitored' | 'not_available'
  source: 'app' | 'manual'
  linked_download_id: number | null
  created_at: string
  updated_at: string
}

VideoType = 'trailer' | 'teaser' | 'clip' | 'behind the scenes' | 'bloopers' | 'featurette' | 'opening credits'
```

**File:** `frontend/src/app/models/trailerprofile.ts`

Add to both `TrailerProfileRead` and `TrailerProfileCreate`:
- `video_type: VideoType`
- `for_movies: boolean`
- `download_season_videos: boolean`
- `max_count: number`

**File:** `frontend/src/app/models/customfilter.ts`

- **No change.** Keep `'trailer_exists'` in `booleanFilterKeys`. The computed `trailer_exists` property on the merged `Media` object preserves the same boolean contract, so all user-configured custom filters continue to work without any migration.

---

## F2. API Service Layer

**File:** `frontend/src/app/services/media.service.ts`

- Add `mediaTrailerStatusResource` — `httpResource<Map<number, MediaTrailerStatus[]>>(() => 'api/v1/media/trailer-statuses-raw')` (new bulk endpoint returning all statuses keyed by `media_id`).
- Update `combinedMedia` computed to merge `trailer_statuses` into each `Media` object alongside downloads, then call `computeTrailerExists()` and `computeMonitorStatus()` to attach computed `trailer_exists` and `status` as local properties.
- Add `setTrailerStatusUnmonitored(statusId: number)` — `PATCH /media/trailer-status/{statusId}` with `{ status: 'unmonitored' }`.
- Add `resetTrailerStatusPending(statusId: number)` — same endpoint with `{ status: 'pending' }`.
- The existing `downloadMediaTrailer()`, `monitorMedia()`, `searchMediaTrailer()` methods are unchanged.

**Backend endpoint needed:** `GET /media/trailer-statuses-raw` — returns all `MediaTrailerStatus` rows for all media (same bulk pattern as `media/downloads_raw`), used by the service to build the `Map<number, MediaTrailerStatus[]>`.

---

## F3. Media List Views — Minimal Changes

The three views (Poster, Expanded, Table) continue to work because `computeMonitorStatus()` produces the same `status` string values the `StatusIconComponent` already handles (`'downloading' | 'downloaded' | 'monitored' | 'missing'`). No template changes needed in the card components themselves.

**File:** `frontend/src/app/media/media-cards/expanded/expanded.component.html`

- Line 48-49: change `trailer_exists ? 'Yes' : 'No'` to show the computed count instead:
  `Trailers: {{ trailerDownloadedCount(media) }}/{{ media.trailer_statuses.length }}` — gives users a richer summary (e.g., "2/3 profiles downloaded").

**File:** `frontend/src/app/media/media-cards/table/table.component.ts`

- Update `getCellValue()` case `'trailer_exists'` to use computed `trailer_exists` (already a property on the merged Media object, so no logic change — just ensuring the computed field name is correct).

**File:** `frontend/src/app/media/utils/apply-filters.ts`

- `'downloaded'` filter: keep using `media.trailer_exists` (now computed, same boolean).
- `'missing'` filter: same.
- `'downloading'` filter: keep `media.status.toLowerCase() === 'downloading'` (now computed string).
- No other changes — the computed values preserve the same contract.

---

## F4. Media Detail Page

**File:** `frontend/src/app/media/media-details/media-details.component.html` & `.ts`

### Changes to existing sections:

- **Trailer exists icon** (line 19-26): unchanged — reads computed `trailer_exists`.
- **Status tooltip** (line 149): change `Downloaded: {{ selectedMedia_.trailer_exists ? 'True' : 'False' }}` to `Trailers: {{ downloadedCount }}/{{ selectedMedia_.trailer_statuses.length }}` for richer info.
- **Status display** (line 143): unchanged — reads computed `status` string.
- **Download button disabled condition** (line 256): unchanged — reads computed `status`.

> **Docs:** Update `docs/user-guide/library/media-details/index.md` — add a **Trailer Profiles** section describing the per-profile status list: what each status means (`Pending`, `Downloading`, `Downloaded`, `Failed`, `Skipped`, `Unmonitored`, `Not Available`), the source chip (App vs Manual), and how to use the Unmonitored / Re-enable actions.

### New section: Trailer Status List

Add a collapsible `Trailer Profiles` section below the existing `Downloads` section. This replaces the need to infer profile state from download records.

**New component:** `frontend/src/app/media/media-details/trailer-status/trailer-status.component.ts` & `.html`

Input: `statuses: MediaTrailerStatus[]`

Displays a list grouped by profile (profile name + video type as header), then rows per season/sequence showing:
- Season label (`Series` / `Season 1` / `Season 2` etc.) and sequence index if `max_count > 1`
- Status badge with colour:
  - `pending` → warning (same amber as missing icon)
  - `downloading` → info (blue, animated)
  - `downloaded` → success (green)
  - `failed` → danger (red)
  - `skipped` → outline (grey)
  - `unmonitored` → outline (grey, strikethrough label)
  - `not_available` → outline (grey, italic)
- Source chip: `App` or `Manual` (subtle, only shown when `downloaded`)
- Action buttons (icon-only, circle):
  - For `pending/failed/skipped`: "Skip" button → sets `UNMONITORED`
  - For `unmonitored`: "Re-enable" button → resets to `PENDING`
  - For `downloaded`: links to the linked `Download` record details

---

## F5. Trailer Profile Settings

**File:** `frontend/src/app/settings/profiles/edit-profile/edit-profile.component.ts` & `.html`

### New fields to add to the profile form:

1. **Video Type** (`video_type`) — `OptionsSettingComponent` dropdown:
   - Options: `['trailer', 'teaser', 'clip', 'behind the scenes', 'bloopers', 'featurette', 'opening credits']`
   - Placed at the top of the form (most impactful setting)

2. **For Movies** (`for_movies`) — `OptionsSettingComponent` with `['true', 'false']` (same pattern as other bool fields):
   - Label: `Scope`; description: `Apply this profile to Movies or Series`
   - Placed near the top alongside Video Type

3. **Download Season Videos** (`download_season_videos`) — `OptionsSettingComponent` with `['true', 'false']`:
   - Only shown when `for_movies === false` (computed `showSeasonOption` signal)
   - Rename from old `download_season_trailers` if it existed

4. **Max Count** (`max_count`) — `TextSettingComponent` (number input, 1–10):
   - Description: `Maximum number of top-voted TMDB results to download per season`

5. **TMDB API key warning banner** — shown inline when `video_type !== 'trailer'` and `tmdbApiKey` setting is empty:
   - `"Non-trailer video types require a TMDB API key. Configure it in General Settings."`
   - Uses `--color-warning` styling

### Computed validation additions (`edit-profile.component.ts`):
- `showSeasonOption = computed(() => this.profile().for_movies === false)`
- `requiresTmdb = computed(() => this.profile().video_type !== 'trailer')`
- `tmdbKeyMissing = computed(() => this.requiresTmdb() && !this.settingsService.settings().tmdb_api_key)`

---

## F6. Settings Page — TMDB API Key

**File:** `frontend/src/app/settings/general/general.component.html` & `.ts`

Add a new **Integrations** card section (after the existing Files card) containing:
- `tmdb_api_key` — `TextSettingComponent` with type `password` (masked input, show/hide toggle):
  - Label: `TMDB API Key`
  - Description: `Required for downloading non-trailer video types (teasers, featurettes, etc.). Get a free key at themoviedb.org.`
  - Calls `updateSetting('tmdb_api_key', value)` on change (same pattern as other settings)

---

## F7. Activity Page — Issues + Events + Logs

Logs and Events are currently separate top-level routes (`/logs`, `/events`). Rather than adding a third cluttered nav item for Issues, consolidate all three into a single **Activity** section with tabs, mirroring the Settings page pattern (`settingsnav` + `routerLinkActive` + `<router-outlet>`).

**New parent component:** `frontend/src/app/activity/activity.component.ts` & `.html`

Tab bar using the same `setnav-btn` + `routerLinkActive="active"` pattern as `settings.component.html`:
```
[ Issues <N> ]  [ Events ]  [ Logs ]
```
The Issues tab label renders as: `Issues <span class="issue-count">{{ issueCount() }}</span>` — same inline span as the nav item; same colour rules; hidden when count is 0. Only the Issues tab gets the count span; Events and Logs tabs have plain labels.

Default tab: **Issues** (wildcard redirect in the routes file).

**Child routes** (`frontend/src/app/activity/routes.ts`):
- `issues` → new `IssuesComponent` — default
- `events` → existing `EventsComponent` relocated from `frontend/src/app/events/`
- `logs` → existing `LogsComponent` relocated from `frontend/src/app/logs/`

**Top-level route changes** (`frontend/src/app/app.routes.ts`):
- Replace `{ path: RouteLogs, ... }` and `{ path: RouteEvents, ... }` with `{ path: RouteActivity, loadChildren: () => import('./activity/routes') }`
- Add redirect stubs so existing bookmarks keep working: `{ path: RouteLogs, redirectTo: '/activity/logs' }`, `{ path: RouteEvents, redirectTo: '/activity/events' }`

**Route constants** (`frontend/src/routing.ts`):
- Add `RouteActivity = 'activity'` and `RouteIssues = 'issues'`
- Keep `RouteLogs` and `RouteEvents` for the redirect stubs

**Nav changes** (`frontend/src/app/app.component.html`):
- Replace the two separate Logs and Events nav items with a single **Activity** nav item pointing to `/activity`
- The label renders as: `Activity <span class="issue-count">{{ issueCount() }}</span>` — the span is inline so the nav item width does not change
- When count > 0: span is visible with a coloured pill style (`--color-danger` background for connection/token issues, `--color-warning` for file issues, white text); when count is 0: `display: none`
- Severity is determined by `issueService.hasUrgentIssues` computed signal (true if any `CONNECTION_FAILED` or `TOKEN_INVALID` rows exist)

**`IssueService`** (`frontend/src/app/services/issue.service.ts`):
- `httpResource` fetching `GET /api/v1/issues/` — initialised as a root-provided singleton so the count is available from any page without waiting for the Activity route to load
- `openCount = computed(() => this.issuesResource.value()?.length ?? 0)`
- `hasUrgentIssues = computed(() => this.issuesResource.value()?.some(i => ['connection_failed', 'token_invalid'].includes(i.issue_type)) ?? false)`
- Refreshes on WebSocket reload signal for the `'issues'` topic (same pattern as `media.service.ts`)
- `dismissIssue(id)` — `DELETE /api/v1/issues/{id}`, then triggers a resource reload

**`IssuesComponent`** (`frontend/src/app/activity/issues/issues.component.ts` & `.html`):
- Fetches `GET /api/v1/issues/` on load and on WebSocket reload signal
- Displays issues grouped by entity type: Connections first (highest urgency), then Trailer Files
- Each issue card shows:
  - Icon + colour: `TOKEN_INVALID` / `CONNECTION_FAILED` → danger; `FILE_DELETED` / `FOLDER_MISSING` → warning
  - Entity name (media title or connection name — joined in API response)
  - Description, **Detected** (`created_at`), **Last seen** (`updated_at`) if different
  - Action buttons (squircle style): `FILE_DELETED` → **Re-download** + **Skip**; `CONNECTION_FAILED` / `TOKEN_INVALID` → **Edit Connection** (→ `/settings/connections/{id}`); `FOLDER_MISSING` → informational only
  - **Dismiss** (icon-only circle button) — `DELETE /api/v1/issues/{id}`; may reappear if condition persists
- Empty state: *"No issues — everything looks good."*

> **Docs:** Create `docs/user-guide/activity/index.md` — Activity section overview; explain the three tabs (Issues, Events, Logs), that Issues defaults, and that the nav badge shows the count of open issues. Move content from `docs/user-guide/events/index.md` → `docs/user-guide/activity/events/index.md` and `docs/user-guide/logs/index.md` → `docs/user-guide/activity/logs/index.md` (update internal links). Update `docs/user-guide/index.md` — replace the separate Events and Logs bullets with a single **Activity** bullet linking to the new section.

---

## F8. Tasks Page — No Code Change Required

The new `Refresh TMDB Videos` weekly task will appear automatically in the tasks list since the component fetches all tasks dynamically. No template changes needed. The task edit dialog (interval/delay) works for any task generically.

---

## Frontend Critical Files

| File | Change |
|---|---|
| `frontend/src/app/models/mediatrailerstatus.ts` | **New** — `MediaTrailerStatus` interface + enums |
| `frontend/src/app/models/issue.ts` | **New** — `Issue` interface + `IssueType` / `EntityType` enums |
| `frontend/src/app/models/media.ts` | Remove `trailer_exists`, `status`; add `trailer_statuses`; add compute helpers |
| `frontend/src/app/models/trailerprofile.ts` | Add `video_type`, `for_movies`, `download_season_videos`, `max_count` |
| `frontend/src/app/models/customfilter.ts` | **No change** — `trailer_exists` stays in boolean keys; computed value preserves same contract |
| `frontend/src/app/services/media.service.ts` | Add `mediaTrailerStatusResource`; update `combinedMedia` to merge + compute |
| `frontend/src/app/services/issue.service.ts` | **New** — `issuesResource` (app-level singleton), `openCount`, `hasUrgentIssues`, `dismissIssue()` |
| `frontend/src/app/media/media-cards/expanded/expanded.component.html` | Show `N/M profiles downloaded` instead of `Yes/No` |
| `frontend/src/app/media/utils/apply-filters.ts` | No logic change — computed fields preserve same contract |
| `frontend/src/app/media/media-details/media-details.component.html` | Update tooltip; add trailer-status section |
| `frontend/src/app/media/media-details/trailer-status/trailer-status.component.ts` | **New** — per-profile status list with UNMONITORED controls |
| `frontend/src/app/activity/activity.component.ts` | **New** — Activity parent with Issues / Events / Logs tabs |
| `frontend/src/app/activity/routes.ts` | **New** — child routes for issues, events, logs |
| `frontend/src/app/activity/issues/issues.component.ts` | **New** — issues tab with per-type action buttons and dismiss |
| `frontend/src/app/settings/profiles/edit-profile/edit-profile.component.ts` | Add `video_type`, `for_movies`, `download_season_videos`, `max_count` fields + TMDB warning |
| `frontend/src/app/settings/general/general.component.html` | Add Integrations section with `tmdb_api_key` |
| `frontend/src/app/app.routes.ts` | Replace Logs/Events routes with Activity; add redirect stubs |
| `frontend/src/app/app.component.html` (nav) | Replace Logs + Events items with single Activity item + badge |
| `frontend/src/routing.ts` | Add `RouteActivity`, `RouteIssues` constants |

---

## Critical Files (Combined)

| File | Change |
|---|---|
| `backend/core/base/database/models/mediatrailerstatus.py` | **New** — model + enums |
| `backend/core/base/database/models/issue.py` | **New** — model + `IssueType` / `EntityType` enums |
| `backend/core/base/database/models/trailerprofile.py` | Add `video_type`, `for_movies`, `download_season_videos`, `max_count` |
| `backend/core/base/database/models/media.py` | Remove `trailer_exists`, `status` |
| `backend/core/base/database/manager/trailerstatusmanager.py` | **New** — all CRUD for join table |
| `backend/core/base/database/manager/issuemanager.py` | **New** — `create_or_skip`, `resolve`, `get_all_open` |
| `backend/core/base/database/manager/trailerprofile.py` | Trigger filter reapplication on save |
| `backend/core/base/database/manager/media.py` | Remove imperative setters |
| `backend/core/download/trailers/missing.py` | Rewrite loop; TMDB-first logic |
| `backend/core/tasks/tmdb_refresh.py` | **New** — weekly TMDB video refresh task |
| `backend/core/tasks/files_scan.py` | Attribute detected files; create/resolve FILE_DELETED issues |
| `backend/core/base/connection_manager.py` | Create/resolve CONNECTION_FAILED and TOKEN_INVALID issues |
| `backend/config/settings.py` | Add `tmdb_api_key` |
| `backend/api/v1/` | New trailer-status, issues endpoints + bulk raw endpoint |
| `backend/alembic/versions/xxxx_mediatrailerstatus.py` | **New** migration |
| `frontend/src/app/models/mediatrailerstatus.ts` | **New** |
| `frontend/src/app/models/issue.ts` | **New** |
| `frontend/src/app/models/media.ts` | Remove fields; add `trailer_statuses`; add compute helpers |
| `frontend/src/app/models/trailerprofile.ts` | Add 4 new fields |
| `frontend/src/app/models/customfilter.ts` | **No change** |
| `frontend/src/app/services/media.service.ts` | Add resource + update computed |
| `frontend/src/app/services/issue.service.ts` | **New** |
| `frontend/src/app/media/media-cards/expanded/expanded.component.html` | Richer trailer count display |
| `frontend/src/app/media/media-details/media-details.component.html` | Update tooltip; add status section |
| `frontend/src/app/media/media-details/trailer-status/trailer-status.component.ts` | **New** |
| `frontend/src/app/activity/activity.component.ts` | **New** — Activity parent with tabs |
| `frontend/src/app/activity/routes.ts` | **New** |
| `frontend/src/app/activity/issues/issues.component.ts` | **New** |
| `frontend/src/app/settings/profiles/edit-profile/edit-profile.component.ts` | Add new profile fields |
| `frontend/src/app/settings/general/general.component.html` | Add TMDB API key setting |
| `frontend/src/app/app.routes.ts` | Replace Logs/Events with Activity + redirect stubs |
| `frontend/src/routing.ts` | Add `RouteActivity`, `RouteIssues` |
| `frontend/src/app/app.component.html` (nav) | Single Activity nav item + issue count badge |

---

## Documentation Updates

### New files

| File | Content |
|---|---|
| `docs/user-guide/activity/index.md` | Activity section overview — three tabs, Issues as default, nav badge explained |
| `docs/user-guide/activity/issues/index.md` | Issues page — what issues are, each `IssueType` (trigger, user action, available buttons), dismiss behaviour, auto-resolve |
| `docs/user-guide/activity/events/index.md` | Moved from `docs/user-guide/events/index.md`; update internal links |
| `docs/user-guide/activity/logs/index.md` | Moved from `docs/user-guide/logs/index.md`; update internal links |

### Updated files

| File | What to update |
|---|---|
| `docs/user-guide/index.md` | Replace separate Events and Logs bullets with a single **[Activity](./activity/index.md)** bullet; list Issues, Events, Logs as sub-bullets |
| `docs/user-guide/settings/profiles/index.md` | Add paragraph: profiles now have a **Scope** (Movies / Series) and **Video Type**; a profile only applies to matching media; migration auto-detection note for existing profiles |
| `docs/user-guide/settings/profiles/settings/general.md` | Add entries for `Video Type` (enum values + what each means), `Scope / for_movies` (Movies vs Series), `Download Season Videos` (series only, creates per-season rows), `Max Count` (number of TMDB results to download) |
| `docs/user-guide/settings/general-settings/index.md` | Add **Integrations** heading with `TMDB API Key` entry — required for non-trailer video types, where to get a free key, what happens if unset |
| `docs/user-guide/library/media-details/index.md` | Add **Trailer Profiles** section — per-profile status list, status definitions, source chip (App / Manual), Unmonitored / Re-enable actions |
| `docs/user-guide/tasks/index.md` | Add **Refresh TMDB Videos** task — purpose, default schedule (weekly), TMDB API key requirement |
| `docs/troubleshooting/common-issues.md` | Update any troubleshooting steps that previously said "check the Events page" or "check the Logs page" to reference the Activity page instead; add a section on Issues — what they mean and that they auto-resolve |

### Link updates required
- All internal links to `/events` or `/logs` in docs must be updated to `/activity/events` and `/activity/logs`
- The getting-started guide (`docs/getting-started/`) may reference Events or Logs — check and update

---

## Verification

1. Run existing test suite: `PYTHONPATH=$(pwd) uv run python -m pytest tests/ -v`
2. Run frontend tests: `cd frontend && npm run test`
3. Create a Movies profile (`for_movies=True, video_type=Trailer`) and a Series profile (`for_movies=False, download_season_videos=True, max_count=2`); verify correct row counts created and correct `trailer_statuses` returned by API.
4. Verify `trailer_exists` computes `true` on frontend only when a `video_type='trailer'` row has `status='downloaded'`; a downloaded featurette alone must not set it.
5. Verify `MonitorStatus` icon in all three list views (Poster, Expanded, Table) matches the computed status.
6. Edit a profile's filters; verify newly matching media get rows, and undownloaded rows for non-matching media are deleted.
7. Set `video_type=Featurette` on a profile with no TMDB API key; verify inline warning appears in profile edit form and rows stay `PENDING` with a warning log.
8. Configure TMDB API key; run weekly TMDB task; verify `NOT_AVAILABLE` rows are set where TMDB has no results, and `PENDING` rows reset where results appear.
9. Manually place a trailer file; run file scan; verify Tier 1 template match attributes it to the correct profile row, and `trailer_exists` computes `True` on the frontend.
10. Place a file with a non-standard name; verify Tier 2 metadata match marks all satisfied profiles as `DOWNLOADED`.
11. Set a row to `UNMONITORED` via the new Trailer Status section in media detail; verify filter reapplication and file scanner never overwrite it.
12. Trigger a download; verify `stop_monitoring=True` marks sibling `PENDING` rows as `SKIPPED`.
13. Set `media.monitor=False`; verify the download loop and TMDB task both skip that media entirely.
14. Delete a trailer file externally (outside the app); run file scan; verify a `FILE_DELETED` issue is created, `MediaTrailerStatus` row stays `DOWNLOADED`, and the Issues page shows the issue with Re-download and Skip action buttons.
15. Restore the deleted file; run file scan; verify the `FILE_DELETED` issue row is deleted and the status remains `DOWNLOADED`.
16. Delete the file via the app UI; verify no issue is created and the row resets to `PENDING` immediately.
17. Simulate a connection auth failure (invalid token); verify a `TOKEN_INVALID` issue is created after the first failure; restore valid credentials; verify the issue is deleted after the next successful refresh.
18. Simulate N consecutive Arr/Plex refresh failures; verify a `CONNECTION_FAILED` issue is created only after the threshold; verify it is deleted after the next successful refresh.
19. Verify the nav badge shows the correct unresolved issue count and updates in real-time via WebSocket.
20. Verify docs: `/activity`, `/activity/issues`, `/activity/events`, `/activity/logs` all render correctly; old `/events` and `/logs` URLs redirect properly. Confirm no broken internal links in the docs.
