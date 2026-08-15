# Connections

## Edit Connection Fields

- **Name**: A unique name for your connection (min. 3 characters).
- **Arr Type**: Select either Radarr or Sonarr.
- **Monitor New Media**: Whether media added by this connection start monitored (see below).
- **Server URL**: The full URL to your Radarr/Sonarr server (e.g., http://192.168.0.15:7878).
- **External URL**: (Optional) If you access your Radarr/Sonarr instance through a reverse proxy or a different URL than the server URL, specify that here. 
    
    This URL will be used by Trailarr when generating links to media items in the web interface.
    
    For example, `https://arr.mydomain.com/radarr`.

    !!! note ""
        External URL is only used for generating links in Trailarr Web interface. The Server URL is still used for API communication with Radarr/Sonarr.

- **API Key**: The API key from your Radarr/Sonarr server settings.
- **Path Mappings**: Map Radarr/Sonarr internal paths to Trailarr paths for correct file access.

### Monitor New Media {: #monitor-types }

{{ version_badge("upd", "0.10.2") }}

This Yes/No toggle decides the **starting monitor state** for media added by this connection: `Yes` → new media start monitored (a trailer will be downloaded for them), `No` → new media start unmonitored. It applies only once, when a media item is first added — after that, monitoring belongs entirely to you: change it per item (or in bulk) from the library pages, and nothing changes it back. Connection syncs and downloads never touch it.

!!! note "Upgrading from Monitor Types"
    Before `v0.10.2` this was a four-value **Monitor Type** dropdown (`Missing` / `New` / `Sync` / `None`). Existing connections migrate automatically: `None` becomes `No`, everything else becomes `Yes` — and your media keep their current monitor values. If you used **Sync**, Trailarr no longer follows monitoring changes from Radarr/Sonarr; to keep sync-like behavior, add a profile filter on `arr_monitored` instead — see [Sync-like behavior with `arr_monitored`](../profiles/filters.md#sync-like-behavior-with-arr-monitored). The upgrade logs list your affected connections.

!!! tip
    _If you have a huge library and don't want to download trailers for all of it, set **Monitor New Media** to `No` when adding the connection. Wait for the first sync to finish, then flip it to `Yes` — only media added from then on start monitored. You can always monitor individual movies/series by hand from the library._

---

## Connection Doctor

{{ version_badge("add", "0.11.4") }}

Every connection card shows a **Connection Doctor** chip: `HEALTHY`, `ISSUES FOUND`, or `NOT CHECKED`. The doctor runs automatically after you save a connection. Click the chip to see the report or to run the check again.

The doctor runs these checks:

- **API reachability** — Trailarr asks the application for its root folders (Plex: library folders). A wrong URL or API key shows up here.
- **Path visibility** — each reported folder must exist and list from inside Trailarr, after your path mappings are applied. A folder that is reachable but empty is flagged as a warning: some network mounts present an empty folder when they are down — see [Network Drives](../../../getting-started/01-first-things/network-drives.md).
- **Mapping suggestions** — when a reported folder is not visible, the doctor does the work of finding it: it searches the disk for media folders it already tracks, by their distinctive names (for example, `Show Name (2015) {tvdb-281662}`), and derives the exact path mapping from where it finds them — verified against several media folders spread across the library. Click **Apply** to add the mapping and re-run the check. For a fresh connection with no synced media yet, it falls back to comparing the remote path against the visible folders; a suggestion confirmed by only a folder-name match says so — check the folder contents before you apply it.
- **Write permissions** — the doctor creates and deletes a `.trailarr-write-test` file in one accessible folder. On failure it reports the folder's owner (uid/gid) against the user Trailarr runs as, which is the PUID/PGID fix — see [Environment Variables](../../../getting-started/01-first-things/environment-variables.md).

!!! note "The checks are read-only"
    The write-test file is the only thing the doctor ever creates, and it deletes it right away. Media files are never touched.

!!! note "Reports do not survive a restart"
    Reports are kept in memory. After a restart, the chips show `NOT CHECKED` until you save a connection or click the chip and run the check.

---

## Plex Connection

{{ version_badge("add", "0.9.0") }}

Plex connections work differently from Radarr/Sonarr connections. See [Plex Connection Fields](./plex.md) for a full field reference and [Plex Connection Setup](../../../getting-started/03-setup/plex-connection.md) for a step-by-step guide.

Key differences:

- **Authentication**: Uses OAuth (sign in with your Plex account) instead of an API key.
- **Library folders instead of path mappings**: Maps Plex library folder paths to Trailarr container paths. The `sync` monitor option is not available.
- **No `sync` monitor type**: Plex connections support `missing`, `new`, and `none`. The `new` option is disabled when first creating a connection.

!!! note ""
    You still need at least one Radarr or Sonarr connection — a Plex connection alone is not sufficient to use Trailarr.