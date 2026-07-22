# Tasks

{{ version_badge("upd", "0.8.0") }}

The Tasks page shows all background jobs that keep Trailarr running smoothly. You can view scheduled jobs, see their status, and run them manually if needed.

## Task Actions

Scheduled tasks will show the following action buttons:

### Run Now

This runs the task immediately without waiting until the next scheduled run. 

!!! waarning ""
    Once a task is run immediately, it will continue its schedule to run at specified intervals from that time until next app restart.

### Pause

Active Tasks can be paused so that they won't run anymore.

### Resume

Paused Tasks can be resumed to continue with their schedule.

### Edit

Tasks can be edited to change their name, interval and delay.

- Interval: The time between 2 scheduled runs of the task.
- Delay: The time delay before the task is run for the first time on app startup. This can be used to set the task cadence. For example, `Arr Data Refresh` task has default delay of 30 seconds and `Download Missing Trailers` task has default delay of 15 minutes -> so `Arr Data Refresh` always runs before `Download Missing Trailers`.

!!! warning ""
    If you want to change the cadence of task runs by editing delays, restart Trailarr once you set the proper delays.

## Scheduled Tasks

### **Arr Data Refresh**

- Runs every 60 minutes (first run starts 30 seconds after app launch) (configurable in [Settings > General > Monitor Interval](../settings/general-settings/index.md#monitor-interval)).
- Connects to all Radarr and Sonarr connections to sync media items and their status in Trailarr.
- Applies `Monitor` and `Status` values, and scans for trailers for new items.
- Runs as a background job; first run starts 30 seconds after app launch.
- If the task is already running, a new instance will not start until the previous one finishes.

### **Docker Update Check**

- Runs once a day (first run starts 4 minutes after app launch).
- Checks if a new Docker image is available for Trailarr and notifies in the UI/logs.
- Does not auto-update; you must update the container manually.

### **Scan All Media Folders**

{{ version_badge("upd", "0.9.9") }}

- Runs every 60 minutes (same as Arr Data Refresh; first run starts 8 minutes after app launch).
- Scans your media folders for all files and folders, detects trailers, and reconciles what it finds on disk with what Trailarr has recorded in its database.
- This task refreshes the files and folders for all media items in Trailarr.
- Useful if you add, rename, or delete trailers manually or outside of Trailarr.

For each media item, the scan compares the trailer file(s) it finds on disk to what's already recorded, and handles four kinds of changes:

| What changed on disk | What Trailarr does |
|---|---|
| A new trailer file appears | Recorded as a new download. |
| An existing trailer is renamed or moved | Recognized by comparing file content, not just the name/path — the existing download record is updated in place, keeping its history. Logged as a [**Trailer Renamed**](../events/index.md#trailer-renamed) event. |
| An existing trailer's content changes but keeps the same name (e.g. re-encoded outside the app) | Detected via a content-hash mismatch — the file's metadata (size, resolution, codecs, duration) is refreshed automatically. Logged as a [**Trailer Modified**](../events/index.md#trailer-modified) event. |
| An existing trailer is deleted | The download record is marked as missing. Logged as a [**Trailer Deleted**](../events/index.md#trailer-deleted) event. |

!!! note "How trailers are detected"
    {{ version_badge("upd", "0.9.6") }}
    A video file counts as a trailer if either of the following is true:

    - It is inside a recognized trailer folder — `Trailers/`, `Trailer/`, or any custom [Folder Name](../settings/profiles/settings/file.md#folder-name) set in a profile. Folder placement is authoritative: any video file in such a folder is a trailer, with no size or name requirements.
    - It sits next to the media file ("inline") with `trailer` in its file name and no `SxxEyy` episode pattern. Files under 200 MB are accepted directly; larger files are verified with ffprobe and only count if their duration is 10 minutes or less — so a full movie with "trailer" in its name is not mistaken for one.

!!! note "Minimal Files Scan from `v0.9.0`"
    The task now checks folder modification times before doing a full recursive scan. If neither the media folder nor any of its immediate subdirectories (e.g., `Trailers/`) have changed since the last scan, the folder is skipped entirely. User-initiated scans always run in full. This significantly reduces scan time for large libraries where most folders are unchanged between runs.

!!! note "Rename & content-change detection from `v0.9.9`"
    {{ version_badge("add", "0.9.9") }}
    Renaming or editing a trailer file used to look identical to "the old one was deleted and a new one appeared", which lost the file's history. The scan now recognizes these cases (see table above) and updates the existing record in place instead.

!!! note "Network drive protection from `v0.9.9`"
    {{ version_badge("add", "0.9.9") }}
    If your media is stored on a network drive (SMB/NFS) that temporarily disconnects, the scan can no longer tell "the drive is offline" apart from "someone deleted all the trailers" — until now. Before marking any trailers as missing, the scan checks that the underlying storage is actually reachable. If it looks unreachable, that media item is skipped for this run (with an error logged) and retried on the next scheduled run, instead of incorrectly marking its trailers as missing.

### **Download Missing Trailers**

{{ version_badge("upd", "0.10.0") }}

- Runs every 60 minutes (same as Arr Data Refresh; first run starts 15 minutes after app launch).
- For every monitored media item, finds the [Profiles](../settings/profiles/index.md) whose filters match, and downloads a video for each matching profile that does not already **own** one.
- Downloads are tracked per profile: a profile that already has its downloaded video never downloads again, so monitored media is not re-downloaded — you can keep media monitored forever. Existing trailers on disk that Trailarr is not yet tracking are claimed by the highest-priority matching profile instead of being downloaded again.
- Downloading no longer turns monitoring off — the monitor toggle stays exactly as you set it.
- If a trailer file is deleted from disk, the next files scan notices it and the owning profile becomes unsatisfied — the trailer is downloaded again on the following run.
- Uses yt-dlp and ffmpeg for downloading and conversion.

!!! note "Failed downloads back off"
    {{ version_badge("add", "0.10.0") }} When a download attempt genuinely fails (e.g. no matching video can be found), that media + profile combination is not retried on every run. The retry delay doubles after each failure — 1 day, then 2 days, then 4 days — capped at one attempt per week. A successful download resets the backoff, and a manual download from Media Details always bypasses it. Skips (missing media folder, waiting for the media file) do not count as failed attempts.

!!! note "Preview mode"
    {{ version_badge("add", "0.10.1") }} When **Downloads Enabled** is turned off in [Settings → General](../settings/general-settings/index.md#downloads-enabled), this task computes and publishes its full work list but downloads nothing — the media pages show a *Preview mode* banner listing every (media, profile) pair it would download. Scans, syncs and attribution keep running so the preview stays accurate, and manual downloads still work.

- There is a delay between consecutive trailer downloads. The delays are as follows:

    | Download No | Delay     |
    |:-----------:|:---------:|
    | 1 - 9       | 2 mins    |
    | 10 - 49     | 4 mins    |
    | 50 - 99     | 6 mins    |
    | 100 - 199   | 7 mins    |
    | 200 - 499   | 9 mins    |
    | 1000+       | 10 mins   |

    All delays also includes an extra random time between `0 - 60` seconds.

### **Refresh Plex Trailer Flags**

{{ version_badge("add", "0.9.3") }}

- Runs once a week (first run starts 10 minutes after app launch, only if a Plex connection exists).
- For each media item linked to a Plex connection, calls the Plex API to check whether Plex already has a remote (internet-sourced) trailer and stores the result in the database.
- The [Download Missing Trailers](#download-missing-trailers) task reads this cached flag instead of calling Plex on every run, which significantly reduces API calls for large libraries.
- Automatically triggered within 3 minutes whenever a new Plex connection is added, so newly linked media is scanned promptly.
- Only appears in the Tasks page if at least one Plex connection has been added.

!!! note "Only remote trailers are counted"
    Locally stored trailer files (e.g. ones Trailarr itself downloaded) are not counted as Plex trailers. Only internet-sourced trailers provided by Plex are considered.

!!! info "Cached flag behaviour"
    Once a media item has been scanned, the cached `True`/`False` value is used by the download task until the next refresh run. New media items added between runs have no cached value yet and will trigger a live Plex API check on their first download attempt.

### **Image Refresh**

- Runs every 6 hours (first run starts 12 minutes after app launch).
- Updates artwork and images for your media library.
- Ensures posters, and backgrounds are up to date.

### **Trailer Cleanup**

- Runs once a day (first run starts 4 hours after app launch).
- Cleans up broken, incomplete, or audio-less trailers from your library.
- If a media item is marked as trailer existing but has no downloaded trailers, it will be marked as not having trailers. Does not change monitoring status.
- If a media item has downloaded trailers but file does not exist, the download record will be marked as file deleted. Does not change monitoring status.
- Helps keep your storage clean and avoids playback issues.

## Queued Tasks - Jobs

A scheduled run of a task is called Job. You can see queued/running jobs and their progress in real time in the Queued Jobs section.

!!! tip
    You might sometimes see an error in logs like below and it's normal behaviour. All the tasks are setup such that if that task is already running, it won't start a new one!

    ```
    WARNING: Tasks: Execution of job "Download Missing Trailers (trigger: interval[1:00:00], next run at: 2025-06-20 11:30:10 CDT)" skipped: maximum number of running instances reached (1)
    ```

### Stop Job

A running task/job will show a `Stop` button that can be used to stop the task if needed. Trailarr has predefined stop points in the task flows where the tasks will stop - so it's not a forceful cancellation that might result in data loss.

!!! note
    Some tasks like `Trailer Download` can only be cancelled after it reaches a certain point in the flow; so cancellation might not happen immediately.

### Job Logs

Jobs will show a log button that can be used to view the logs of that task run.

Internally, Trailarr uses the Job's id (UUID4) to trace the logs related to that job - so when you click on the logs button it will open logs page and set that job id as filter.