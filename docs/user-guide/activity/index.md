# Activity

{{ version_badge("add", "0.9.5") }}

The **Activity** section consolidates three pages — **Issues**, **Events**, and **Logs** — into a single tab-based view. Navigate to each tab using the tab bar at the top of the page.

## Tabs

### Issues

The default tab. Shows all open issues that require your attention: missing trailer files, failed connections, invalid API tokens, and inaccessible media folders. Issues are auto-resolved when the underlying condition clears (e.g. a re-downloaded file resolves a `FILE_DELETED` issue).

The nav badge next to **Activity** shows the count of open issues. When an urgent issue (connection failure or invalid token) is present, the badge turns red.

See **[Issues](./issues/index.md)** for a full description of each issue type and the available actions.

### Events

Shows all recent events across your entire library: trailer downloads, deletions, monitor changes, Plex link/unlink events, and more. Events are informational — they record what happened and why, but do not require user action.

See **[Events](./events/index.md)** for a full description of each event type.

### Logs

Shows the Trailarr application logs. Useful for monitoring background task activity and troubleshooting problems.

See **[Logs](./logs/index.md)** for filtering and download options.

---

## Navigation

- Old direct URLs `/events` and `/logs` redirect automatically to `/activity/events` and `/activity/logs`.
- The **Activity** nav item is always visible; the issue count badge appears when there are open issues.
