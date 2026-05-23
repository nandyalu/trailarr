**Environment variables are OPTIONAL.**

Here are the optional environment variables you can set:

### `APP_DATA_DIR`

- Default is `/config`.

This environment variable is used to set the application data directory. If setting this, make sure to map the volume to the same directory.

Useful if you want to store the application data in a different directory than the default.

For example, if you want to store the application data in `/app_config/abc`, you can set the `APP_DATA_DIR` environment variable like this:

```yaml hl_lines="2 4"
    environment:
        - APP_DATA_DIR=/app_config/abc
    volumes:
        - /var/appdata/trailarr:/app_config/abc
```

!!! warning
    If you are setting the `APP_DATA_DIR` environment variable, make sure to set an absolute path like `/data` or `/config/abc`, and map the volume to the same directory.

!!! danger
    Do not set `APP_DATA_DIR` to `/app` or `/tmp` or any other linux system directory. This could cause the application to not work correctly or data loss.


### `PGID`

- Default is `1000`.

This environment variable is used to set the group ID for the application.

Useful if you have permission issues with the application writing to the volume. You can set the group ID to the group of the volume or a group that has read/write permissions to the volume.

```yaml
    environment:
        - PGID=1000
```


### `PUID`

- Default is `1000`.

This environment variable is used to set the user ID for the application.

Useful if you have permission issues with the application writing to the volume. You can set the user ID to the owner of the volume or a user that has read/write permissions to the volume.

```yaml
    environment:
        - PUID=1000
```


### `TZ`

- Default is `America/New_York`.

This environment variable is used to set the timezone for the application.

For a list of valid timezones, see [tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

```yaml
    environment:
        - TZ=America/New_York
```

### `WEBUI_DISABLE_AUTH`

!!! failure "Removed"
    `WEBUI_DISABLE_AUTH` has been removed. To bypass the login page when Trailarr is behind a reverse proxy, configure your proxy to forward the `X-API-KEY` header instead.
    See [Reverse Proxy → Bypassing the Login Page](../../user-guide/reverse-proxy.md#bypassing-the-login-page) for per-proxy configuration examples.

### `WEBUI_PASSWORD`

- Default is `trailarr` (hashed).

Trailarr Web Interface has a browser login to access the app. Default credentials are:

```bash
Username: admin
Password: trailarr
```

If you forget your password, set this environment variable to `' '` (empty string) to reset the password for the web interface to default.

```yaml
    environment:
        - WEBUI_PASSWORD= # This will reset the password to default
```

!!! tip ""
    App tries to parse the improperly escaped quotes to try and reset the password, but if it's not working, try setting it to a space like `WEBUI_PASSWORD=' '`.

To change the password, go to `Settings > About > Password` in web interface. 

!!! info
    If you change your password from the web interface, the password will be hashed and stored internally. There is no way to retrieve the password as only a hashed version is stored, you need to reset it if you forget it.

!!! warning
    Once you change your password, don't forget to remove the `WEBUI_PASSWORD` environment variable from the docker-compose file.


### `TMDB_API_KEY`

{{ version_badge("add", "0.10.0") }}

- Default: `(empty)`

Your [The Movie Database (TMDB)](https://www.themoviedb.org/){:target="_blank"} v3 API key. Required for downloading non-trailer video types (teasers, clips, featurettes, bloopers, behind the scenes, opening credits) via Trailer Profiles.

Get a free key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api){:target="_blank"}.

```yaml
    environment:
        - TMDB_API_KEY=your_api_key_here
```

This setting can also be configured from the web interface under **Settings > General > Integrations > TMDB API Key**.

### `FILES_FULL_SCAN`

{{ version_badge("add", "0.9.1") }}

- Default: `false`

When set to `true`, the next **Scan Media Folders** task run will scan every media folder in full, ignoring the folder-change optimisation that normally skips unchanged folders. Useful for correcting stale `trailer_exists` or `media_exists` flags after trailers are added or removed outside of Trailarr.

The value is **automatically reset to `false`** once the full scan finishes — you do not need to remove it manually.

```yaml
    environment:
        - FILES_FULL_SCAN=true
```

This setting can also be toggled from the web interface under **Settings > General > Files > Force Full Files Scan**.

### Example

Here is an example of setting the environment variables:

```yaml
    environment:
        - TZ=America/Los_Angeles
        - PUID=1000
        - PGID=1000
        - APP_DATA_DIR=/data/trailarr
    volumes:
        - /var/appdata/trailarr:/data/trailarr
```

This sets the environment variables to run the app with following settings:

- Timezone: America/Los_Angeles
- User ID: 1000
- Group ID: 1000
- Application data directory: /data/trailarr
- Volume mapping: /var/appdata/trailarr:/data/trailarr

