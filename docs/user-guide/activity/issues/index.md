# Issues

{{ version_badge("add", "0.9.5") }}

The **Issues** page lists all actionable problems that Trailarr has detected. Unlike events (which are informational), issues require user attention or action. Issues auto-resolve when the underlying condition clears — you do not need to dismiss them unless you want to hide them temporarily.

## How Issues Differ from Events and Logs

| | Issues | Events | Logs |
|---|---|---|---|
| **Purpose** | Require user action | Informational record | Raw application output |
| **Auto-resolve** | Yes, when condition clears | N/A (permanent record) | N/A |
| **Dismissible** | Yes (may reappear) | No | No |

## Issue Types

### FILE_DELETED

**Trigger:** A trailer file that Trailarr was tracking has disappeared from disk (detected during the **Scan All Media Folders** task).

**What it means:** Someone deleted the file outside of Trailarr, or the storage location became temporarily inaccessible.

**Available actions:**

- **Re-download** — sends the media to the download queue (`/media/{id}/download`).
- **Skip** — sets the corresponding `MediaTrailerStatus` row to `Unmonitored` so the download loop will not re-attempt it.
- **Dismiss** — removes this issue row without taking action. If the file is still missing on the next scan, the issue will reappear.

**Auto-resolves when:** The file is found again on a subsequent **Scan All Media Folders** run.

!!! note
    The `MediaTrailerStatus` row remains `DOWNLOADED` even when the file is missing. This preserves the history of what was there. The issue signals that action may be needed.

---

### CONNECTION_FAILED

**Trigger:** Trailarr has failed to refresh data from a Radarr, Sonarr, or Plex connection repeatedly (default threshold: 3 consecutive failures).

**What it means:** The connection is unreachable or returning unexpected errors. Single transient failures do not create an issue.

**Available actions:**

- **Edit Connection** — navigate to Settings → Connections → Edit for the affected connection to check the URL and credentials.
- **Dismiss** — removes the issue. It will reappear after the next batch of consecutive failures.

**Auto-resolves when:** The next connection refresh succeeds.

---

### TOKEN_INVALID

**Trigger:** An API request to a Radarr, Sonarr, or Plex connection was rejected with an authentication error (HTTP 401 or 403).

**What it means:** The API key or token stored in Trailarr is no longer valid. This can happen after rotating API keys or revoking tokens in Radarr/Sonarr/Plex.

**Available actions:**

- **Edit Connection** — update the API key in Settings → Connections.
- **Dismiss** — removes the issue. It will reappear on the next API call if the token is still invalid.

**Auto-resolves when:** An API call to that connection succeeds (i.e. after the token is updated).

---

### FOLDER_MISSING

**Trigger:** The media folder path for a specific item is not accessible when the download loop tries to download a trailer.

**What it means:** The folder has been moved, renamed, or the mount point is temporarily offline.

**Available actions:**

This issue is informational — Trailarr cannot fix a missing folder path. Check your storage configuration and ensure the folder is accessible from the Trailarr container.

- **Dismiss** — removes the issue. It will reappear on the next download attempt if the folder is still missing.

**Auto-resolves when:** The folder is accessible again on the next download attempt.

---

## Dismissing Issues

Clicking **Dismiss** (the circle × button) deletes the issue row immediately. If the underlying condition persists, the issue will be recreated automatically on the next check. Dismissing is appropriate when you want to silence a known issue temporarily (e.g. a storage drive that is intentionally offline).

## Issue Count Badge

The **Activity** nav item displays a count badge showing the total number of open issues. The badge colour indicates severity:

- **Warning (amber):** Only file-related issues (`FILE_DELETED`, `FOLDER_MISSING`).
- **Danger (red):** At least one urgent issue (`CONNECTION_FAILED` or `TOKEN_INVALID`).
- **Hidden:** No open issues.

The badge updates in real time via WebSocket when issues are created or resolved.
