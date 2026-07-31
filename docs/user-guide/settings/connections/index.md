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

## Plex Connection

{{ version_badge("add", "0.9.0") }}

Plex connections work differently from Radarr/Sonarr connections. See [Plex Connection Fields](./plex.md) for a full field reference and [Plex Connection Setup](../../../getting-started/03-setup/plex-connection.md) for a step-by-step guide.

Key differences:

- **Authentication**: Uses OAuth (sign in with your Plex account) instead of an API key.
- **Library folders instead of path mappings**: Maps Plex library folder paths to Trailarr container paths. The `sync` monitor option is not available.
- **No `sync` monitor type**: Plex connections support `missing`, `new`, and `none`. The `new` option is disabled when first creating a connection.

!!! note ""
    You still need at least one Radarr or Sonarr connection — a Plex connection alone is not sufficient to use Trailarr.