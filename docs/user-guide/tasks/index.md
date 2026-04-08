# Tasks

The Tasks page shows all background jobs that keep Trailarr running smoothly. You can view scheduled jobs, see their status, and run them manually if needed.

## Task Actions

Scheduled tasks will show the following action buttons:

### Run Now

This runs the task immediately without waiting until the next scheduled run. Once a task is immediately runned, it will continue it's schedule to run at specified intervals from that time until next app restart.

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

<!-- md:version:upd 0.6.5 -->

- Runs every 60 minutes (same as Arr Data Refresh; first run starts 8 minutes after app launch).
- Scans your media folders for all files and folders, detects trailers, and updates the database with found trailers and marks download records as deleted if files are missing.
- This task refreshes the files and folders for all media items in Trailarr.
- Useful if you add/delete trailers manually or outside of Trailarr.

### **Download Missing Trailers**

- Runs every 60 minutes (same as Arr Data Refresh; first run starts 15 minutes after app launch).
- Downloads trailers for media that are missing them, based on your profiles and filters.
- Uses yt-dlp and ffmpeg for downloading and conversion.
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