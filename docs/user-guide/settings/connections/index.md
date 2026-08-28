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

Every connection card shows a **Connection Doctor** chip: `HEALTHY`, `ISSUES FOUND`, or `NOT CHECKED`. The doctor runs automatically after you save a connection. Click the chip to see the report or to run the check again, or use **Check all** to check every connection at once. Trailarr keeps the last report of each connection, so the results are still there after a restart.

### Find your folders while you add a connection

{{ version_badge("add", "0.11.4") }}

The doctor also runs on the **Add / Edit Connection** page, before you save the connection. First test the connection and let Trailarr list the root folders. Then click **Find folders**. Trailarr looks on disk for the folders that your application reports. It fills in the **Trailarr Path** of every mapping that it finds.

Trailarr refuses to save a connection that it cannot reach or read. Without this button, you must know the layout of your mounts in advance. With it, Trailarr finds the layout for you.

Two rules keep it safe:

- A **Trailarr Path you typed is never overwritten**. When the doctor finds a different folder for that row, it offers it as a button next to the field, and you decide.
- Each suggestion shows how strong the evidence is. `2 folders confirm this` means the mapping also resolves other media folders that Trailarr already tracks. `name match only — check it` means that only the folder name matches. Look at the folder contents first.

The doctor runs these checks:

- **API reachability** — Trailarr asks the application for its root folders (Plex: library folders). This check reports a wrong URL or a wrong API key.
- **Path visibility** — each reported folder must exist, and Trailarr must be able to list its contents after it applies your path mappings. Trailarr gives a warning for a folder that it can reach but that is empty. Some network mounts show an empty folder when the mount is not available — see [Network Drives](../../../getting-started/01-first-things/network-drives.md).
- **Mapping suggestions** — when a reported folder is not visible, the doctor finds it for you. It searches the disk for media folders that Trailarr already tracks, by their distinctive names (for example, `Show Name (2015) {tvdb-281662}`). It then derives the path mapping from the place where it finds them. It confirms the mapping against several media folders from different parts of the library. Each suggestion maps one reported root folder (for example, `/media/tv → /media/all/Media/tv`), so there is one mapping for each root folder the application reports. Click **Apply** to add the mapping and to run the check again. When the root folder already has a mapping, the button says **Update mapping** and changes the target of that mapping. It does not add a second mapping. When the check passes, Trailarr also starts a sync of that connection immediately. Trailarr then adds the media to your library before the next scheduled sync. For a new connection with no synced media, the doctor compares the remote path against the visible folders instead. A suggestion that matches only a folder name says so. Look at the folder contents before you apply that suggestion.
- **Write permissions** — the doctor creates a `.trailarr-write-test` file in **every** accessible folder, then deletes it. One writable folder does not make the other folders writable. For example, the doctor reports a read-only TV share next to a writable movies mount. When the test fails, the doctor shows the owner (uid/gid) of the folder and the user that Trailarr runs as. Compare the two values, then set the correct PUID and PGID — see [Environment Variables](../../../getting-started/01-first-things/environment-variables.md).

!!! note "The checks are read-only"
    The write-test file is the only thing the doctor ever creates, and it deletes it right away. Media files are never touched.

!!! note "Reports stay after a restart"
    Trailarr saves the reports to a file in the config folder. After a restart, each chip shows the result of its last check. A connection that was never checked shows `NOT CHECKED`.

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