# Tasks

{{ version_badge("upd", "0.8.0") }}

The Tasks page shows all background jobs that keep Trailarr running smoothly. You can view scheduled jobs, see their status, and run them manually if needed.

---

## Default Task Order

When Trailarr starts, each task waits for its configured **first-run delay** before it runs for the first time. The defaults are chosen so that upstream data is ready before downstream tasks consume it:

| # | Task | Default Interval | First-Run Delay |
|:-:|:-----|:----------------:|:---------------:|
| 1 | Arr Data Refresh | 60 min | 30 sec |
| 2 | Docker Update Check | 24 hours | 4 min |
| 3 | Scan All Media Folders | 60 min | 8 min |
| 4 | Refresh Plex Trailer Flags | 7 days | 10 min |
| 5 | Image Refresh | 6 hours | 12 min |
| 6 | Download Missing Trailers | 60 min | 15 min |
| 7 | Refresh TMDB Videos | 7 days | 30 min |
| 8 | Trailer Cleanup | 24 hours | 4 hours |

**Why this order?** Arr Data Refresh runs first (30 s) to populate the database with your media library. Scan All Media Folders follows at 8 min to detect any trailers already on disk. Download Missing Trailers starts at 15 min — after both of those have completed their first run — so it always works with fresh data. Weekly tasks (Plex flags, TMDB videos) stagger their first run across the first half-hour to avoid an API burst at startup.

You can change any task's interval or delay via the **Edit** action. Restart Trailarr after adjusting delays so the new order takes effect.

---

## Task Actions

Scheduled tasks show the following action buttons:

### Run Now

Runs the task immediately without waiting for the next scheduled run.

!!! warning ""
    Once a task is run immediately, it continues its normal schedule from that point forward until the next app restart.

### Pause

Active tasks can be paused so they will not run until resumed.

### Resume

Paused tasks can be resumed to continue their schedule.

### Edit

Every task can be individually configured:

- **Interval** — time between consecutive scheduled runs.
- **Delay** — time before the task's first run on startup. Adjusting delays lets you control the order tasks run relative to one another (see [Default Task Order](#default-task-order) above).

!!! warning ""
    Restart Trailarr after changing delays so the new first-run order takes effect.

---

## Scheduled Tasks

### **Arr Data Refresh**

- Runs every **60 minutes** (first run **30 seconds** after app launch).
- Connects to all Radarr and Sonarr connections to sync media items and their status in Trailarr.
- Applies `Monitor` and `Status` values, and creates trailer status rows for new items.
- If the task is already running, a new instance will not start until the previous one finishes.

### **Docker Update Check**

- Runs every **24 hours** (first run **4 minutes** after app launch).
- Checks if a new Docker image is available for Trailarr and notifies in the UI/logs.
- Does not auto-update; you must update manually.

### **Scan All Media Folders**

{{ version_badge("upd", "0.9.0") }}

- Runs every **60 minutes** (first run **8 minutes** after app launch).
- Scans your media folders for all files and folders, detects trailers, and updates the database with found trailers. Marks download records as deleted if files are missing.
- Useful if you add or delete trailers manually outside of Trailarr.

!!! note "Minimal Files Scan from `v0.9.0`"
    The task checks folder modification times before doing a full recursive scan. If neither the media folder nor any of its immediate subdirectories (e.g., `Trailers/`) have changed since the last scan, the folder is skipped entirely. User-initiated scans always run in full. This significantly reduces scan time for large libraries where most folders are unchanged between runs.

### **Download Missing Trailers**

- Runs every **60 minutes** (first run **15 minutes** after app launch).
- Works through `Pending` trailer status rows in profile priority order, downloading trailers via yt-dlp and ffmpeg.
- Processes one item at a time with a progressive delay between downloads to avoid rate limits.

See the **[Download Pipeline](download-pipeline.md)** page for a full explanation of how Trailarr finds, downloads, and tracks trailers — including the video ID lookup priority, TMDB cache behaviour, retry logic, and the delay table between consecutive downloads.

### **Refresh Plex Trailer Flags**

{{ version_badge("add", "0.9.3") }}

- Runs every **7 days** (first run **10 minutes** after app launch, only if a Plex connection exists).
- For each media item linked to a Plex connection, calls the Plex API to check whether Plex already has a remote (internet-sourced) trailer and stores the result in the database.
- The [Download Missing Trailers](#download-missing-trailers) task reads this cached flag instead of calling Plex on every run, which significantly reduces API calls for large libraries.
- Automatically triggered within 3 minutes whenever a new Plex connection is added, so newly linked media is scanned promptly.
- Only appears in the Tasks page if at least one Plex connection has been added.

!!! note "Only remote trailers are counted"
    Locally stored trailer files (e.g. ones Trailarr itself downloaded) are not counted as Plex trailers. Only internet-sourced trailers provided by Plex are considered.

!!! info "Cached flag behaviour"
    Once a media item has been scanned, the cached `True`/`False` value is used by the download task until the next refresh run. New media items added between runs have no cached value yet and will trigger a live Plex API check on their first download attempt.

### **Refresh TMDB Videos**

{{ version_badge("add", "0.10.0") }}

- Runs every **7 days** (first run **30 minutes** after app launch).
- Requires a **TMDB API Key** configured in [General Settings](../settings/general-settings/index.md#tmdb-api-key). If no key is set the task exits immediately with a warning.
- For each monitored media item that has `PENDING` or `NOT_AVAILABLE` `MediaTrailerStatus` rows on a profile whose **Video Type** is not `trailer`:
    - Calls the TMDB videos endpoint for that media's TMDB/TVDB ID.
    - If TMDB **has** a matching video → resets `NOT_AVAILABLE` rows back to `PENDING` so the download loop picks them up.
    - If TMDB **has no** matching video → sets `PENDING` rows to `NOT_AVAILABLE` so they are skipped until the next weekly check.
- For `trailer`-type rows, also queries TMDB to pre-cache the YouTube key on the status row, reducing API calls during the download task.
- Sleeps briefly between requests to respect TMDB API rate limits.

!!! note "Trailer type always falls back to YouTube search"
    `NOT_AVAILABLE` is never set for rows where the profile `video_type` is `trailer` — YouTube search is always available as a fallback for trailers, so those rows stay `PENDING`.

### **Image Refresh**

- Runs every **6 hours** (first run **12 minutes** after app launch).
- Updates artwork and images for your media library.
- Ensures posters and backgrounds are up to date.

### **Trailer Cleanup**

- Runs every **24 hours** (first run **4 hours** after app launch).
- Cleans up broken, incomplete, or audio-less trailers from your library.
- If a media item is marked as trailer existing but has no downloaded trailers, it will be marked as not having trailers. Does not change monitoring status.
- If a media item has downloaded trailers but the file does not exist, the download record will be marked as file deleted. Does not change monitoring status.

---

## Queued Tasks — Jobs

A scheduled run of a task is called a **Job**. You can see queued and running jobs, plus their real-time progress, in the Queued Jobs section.

!!! tip
    You might occasionally see a log entry like the one below — this is normal. All tasks are configured so that if one is already running, a new instance will not start:

    ```
    WARNING: Tasks: Execution of job "Download Missing Trailers (trigger: interval[1:00:00], next run at: 2025-06-20 11:30:10 CDT)" skipped: maximum number of running instances reached (1)
    ```

### Stop Job

A running task/job shows a `Stop` button. Trailarr has predefined stop points in the task flows so stopping is always safe — it will not force-kill a task mid-operation.

!!! note
    Some tasks like `Trailer Download` can only be cancelled after reaching a certain point in the flow; cancellation may not happen immediately.

### Job Logs

Jobs show a log button for viewing the logs of that task run.

Internally, Trailarr uses the Job's UUID to trace related log entries — clicking the logs button opens the Logs page with that job ID pre-filtered.
