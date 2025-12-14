# Connections

## Edit Connection Fields

- **Name**: A unique name for your connection (min. 3 characters).
- **Arr Type**: Select either Radarr or Sonarr.
- **Monitor Type**: Choose how trailers are monitored/downloaded (see below).
- **Server URL**: The full URL to your Radarr/Sonarr server (e.g., http://192.168.0.15:7878).
- **External URL**: (Optional) If you access your Radarr/Sonarr instance through a reverse proxy or a different URL than the server URL, specify that here. 
    
    This URL will be used by Trailarr when generating links to media items in the web interface.
    
    For example, `https://arr.mydomain.com/radarr`.

    !!! note ""
        External URL is only used for generating links in Trailarr Web interface. The Server URL is still used for API communication with Radarr/Sonarr.

- **API Key**: The API key from your Radarr/Sonarr server settings.
- **Path Mappings**: Map Radarr/Sonarr internal paths to Trailarr paths for correct file access.

### Monitor Types

#### `Missing`
Monitors and downloads trailers for movies/series without a trailer.

#### `New`
Only Monitors and download trailers for movies/series that gets added after the change.

#### `Sync`
Monitors and downloads trailers for movie/series that are monitored in Radarr/Sonarr.

#### `None`
Turns off monitoring for the connection and does not download any trailers.

!!! tip
    _If you have a huge library and don't want to download trailers for all of them, set the monitor type to `None` when adding a Radarr/Sonarr Connection. Wait for an hour or so to let the app sync all media from that connection, and change it to `New` to download trailers for new media. You can always manually set the monitor type for the movies/series you want to download trailers for._