# Tasks

The Tasks page shows all background jobs that keep Trailarr running smoothly. You can view scheduled jobs, see their status, and run them manually if needed.

## Scheduled Tasks

- **Arr Data Refresh**: Updates data from Radarr and Sonarr connections. Runs every 60 minutes (configurable in [Settings > General > Monitor Interval](../settings/general-settings/index.md#monitor-interval)).
- **Docker Update Check**: Checks for new Docker image updates. Runs once a day.
- **Scan Disk for Trailers**: Scans your media folders for trailers. Runs every 60 minutes (same as Arr Data Refresh).
- **Download Missing Trailers**: Downloads trailers for media missing them. Runs every 60 minutes (same as Arr Data Refresh).
- **Image Refresh**: Updates artwork and images. Runs every 6 hours.
- **Trailer Cleanup**: Cleans up broken or incomplete trailers. Runs once a day.

You can also see queued/running jobs and their progress in real time.
