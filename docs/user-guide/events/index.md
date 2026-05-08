# Events

{{ version_badge("add", "0.7.0") }}

Trailarr tracks important events for each media item, giving you visibility into what's happening with your trailers. Events help you understand when and why changes occur to your media library.

!!! info "Where to View Events"
    - **Media Details**: View events for a specific media item in the Events section on the media details page.
    - **Events Page**: View all recent events across your entire library at `/events`.

## Event Sources

{{ version_badge("upd", "0.9.0") }}

Events are triggered by two sources:

| Source | Description |
|--------|-------------|
| **User** | Actions performed manually through the Trailarr UI or API |
| **System** | Automatic actions performed by scheduled tasks |

Each event also includes a **source detail** that provides more context about what triggered the event, such as:

- `API` - Action performed through the web interface
- `ConnectionRefresh` - Triggered during connection sync with Radarr/Sonarr
- `FilesScan` - Triggered during media folder scanning
- `TrailerDownload` - Triggered during trailer download task
- `TrailerSearch` - Triggered by manual trailer search
- `DownloadTrailers` - Triggered by scheduled download task
- `MediaCleanup` - Triggered during cleanup of deleted media
- `PlexRefresh` - Triggered during Plex library sync

---

## Event Types

### Media Added

Logged when a new media item is discovered and added to Trailarr from Radarr or Sonarr.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `ConnectionRefresh` |
| New Value | Connection type (e.g., "Radarr", "Sonarr") |

This event is created when Trailarr syncs with your Radarr/Sonarr connections and discovers a new movie or series that wasn't previously tracked.

---

### Monitor Changed

Logged when the monitor status of a media item changes.

| Field | Value |
|-------|-------|
| Source | User or System |
| Source Detail | `API`, `ConnectionRefresh`, or `TrailerDownload` |
| Old Value | Previous monitor status (`true` or `false`) |
| New Value | New monitor status (`true` or `false`) |

**Triggers:**

- **User**: Toggling the monitor switch in the UI
- **System**: 
    - Connection refresh when monitor status changes in Radarr/Sonarr
    - Trailer download task when it auto-unmonitors after successful download

---

### YouTube ID Changed

Logged when the YouTube trailer ID changes for a media item.

| Field | Value |
|-------|-------|
| Source | User or System |
| Source Detail | `API`, `ConnectionRefresh`, or `TrailerDownload` |
| Old Value | Previous YouTube ID (empty if none) |
| New Value | New YouTube ID (empty if cleared) |

**Triggers:**

- **User**: Manually setting or clearing the YouTube ID in the UI
- **System**: 
    - Connection refresh when a new YouTube ID is detected from Radarr/Sonarr
    - Trailer download task when it finds and sets a trailer ID

---

### Trailer Detected

Logged when an existing trailer file is found on disk that wasn't downloaded by Trailarr.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `ConnectionRefresh` or `FilesScan` |

This event indicates that a trailer was added to your media folder through means other than Trailarr (e.g., manually copied, downloaded by another tool). Trailarr will recognize and track these trailers.

---

### Trailer Downloaded

Logged when a trailer is successfully downloaded for a media item.

| Field | Value |
|-------|-------|
| Source | User or System |
| Source Detail | `TrailerSearch` or `TrailerDownload` |
| New Value | YouTube ID of the downloaded trailer |

**Triggers:**

- **User**: Manually searching and downloading a trailer from the UI
- **System**: Scheduled trailer download task automatically downloading missing trailers

---

### Trailer Deleted

Logged when a trailer file is deleted or removed.

| Field | Value |
|-------|-------|
| Source | User or System |
| Source Detail | `API`, `FilesScan`, or `MediaCleanup` |
| New Value | Reason for deletion |

**Deletion Reasons:**

| Reason | Description |
|--------|-------------|
| `user_request` | User manually deleted the trailer through the UI |
| `file_not_found` | Trailer file was deleted outside of Trailarr and detected during file scan |
| `media_deleted` | Parent media item was deleted, so trailer was cleaned up |

---

### Download Skipped

Logged when Trailarr skips downloading a trailer for a media item.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `DownloadTrailers` |
| New Value | Reason for skipping |

!!! note "Deduplication"
    To avoid cluttering the event log, skip events are only recorded once per media item per reason. If the skip reason changes, a new event will be logged.

**Skip Reasons:**

| Reason | Description |
|--------|-------------|
| `Missing folder path` | Media item doesn't have a folder path set |
| `Folder not found` | Media folder doesn't exist on disk |
| `Already downloaded` | A trailer already exists for this media |
| `Unmonitored` | Media item is not monitored for trailer downloads |

---

### Plex Linked

{{ version_badge("add", "0.9.0") }}

Logged when a media item is successfully matched to an item in a Plex library.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `PlexRefresh` |
| New Value | Name of the Plex connection |
| Old Value | Plex rating key of the matched item |

This event is created when Trailarr syncs with your Plex connection and finds a Plex library entry that corresponds to a Radarr/Sonarr media item. Once linked, Trailarr can check Plex for existing trailers and trigger Plex library scans after downloads.

---

### Plex Unlinked

{{ version_badge("add", "0.9.0") }}

Logged when the Plex link for a media item is removed.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `ConnectionDeleted` |

**Triggers:**

- The Plex connection is deleted from Trailarr.

---

### Plex Scan Triggered

{{ version_badge("add", "0.9.0") }}

Logged when Trailarr requests a Plex library refresh after a successful trailer download.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `TrailerDownload` |

This event is only created when **Notify Plex** is enabled in the Trailer Profile used for the download. It confirms that Trailarr asked Plex to scan the media folder so the new trailer appears in Plex without delay.

---

### Arr Linked

{{ version_badge("add", "0.9.0") }}

Logged when a media item that was previously tracked only by Plex is adopted by a Radarr or Sonarr connection.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `ConnectionRefresh` |
| New Value | Name of the Arr connection (e.g., "Radarr", "My Sonarr") |

This event is created when a Radarr or Sonarr connection sync finds an existing Plex-only media item at the same folder path. Instead of creating a duplicate, Trailarr merges the Arr metadata into the existing item and links both connections to the same record. The Plex link is preserved after the merge.

**Typical scenario**: A Plex connection was set up first, creating items without Radarr/Sonarr backing. When a Radarr or Sonarr connection is added later and synced, any matching items are linked rather than duplicated.

---

### Arr Unlinked

{{ version_badge("add", "0.9.0") }}

Logged when a media item is removed from Radarr or Sonarr but its files remain on disk and it is still tracked by Plex.

| Field | Value |
|-------|-------|
| Source | System |
| Source Detail | `ConnectionRefresh` |
| Old Value | Name of the Arr connection that removed the item |

Instead of deleting the media item from Trailarr, the Arr link is stripped and the item reverts to Plex-only tracking (`connection_id` is reassigned to the Plex connection and `arr_id` is reset to 0). This preserves trailer history and Plex metadata for the item.

**Typical scenario**: A movie or series is unmonitored and removed from Radarr/Sonarr while the media files are kept. Because Plex still has the files in its library, Trailarr keeps the record alive as a Plex-only item rather than deleting it.

---

## Event Retention

Events are stored in the database and retained indefinitely. You can view the complete event history for any media item on its details page.

!!! tip "Troubleshooting with Events"
    Events are valuable for troubleshooting issues. If a trailer isn't downloading or something seems wrong, check the events to see what Trailarr has attempted and why certain actions were skipped.
