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

- Default is `False`.

This environment variable is used to disable the authentication for the web interface.
    
```yaml
    environment:
        - WEBUI_DISABLE_AUTH=True # This will disable the web UI authentication
```

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


### `DELETE_TRAILER_CONNECTION`

- Default is `False`.

This environment variable controls the new "Delete Trailers" behaviour in the General settings. When enabled, Trailarr will delete trailer files from disk when the corresponding media item is removed from the connected Radarr/Sonarr instance.

Use this if you want Trailarr to automatically clean up trailer files when media entries are removed in your ARR instances.

```yaml
    environment:
        - DELETE_TRAILER_CONNECTION=False
```

!!! warning
    Enabling this option may remove trailer files from disk when media is removed in Radarr/Sonarr. Make sure you understand the behaviour before enabling it.


### `DELETE_TRAILER_MEDIA`

- Default is `False`.

This environment variable works together with `DELETE_TRAILER_CONNECTION`. When `DELETE_TRAILER_CONNECTION` is `True` and this variable is `True`, Trailarr will only delete trailer files if the media files themselves are also deleted from disk (i.e., only delete trailers when the actual media files are not present on disk).

This provides a safer option to avoid removing trailers while keeping media files intact.

```yaml
    environment:
        - DELETE_TRAILER_MEDIA=False
```

!!! info
    `DELETE_TRAILER_MEDIA` only has effect if `DELETE_TRAILER_CONNECTION` is enabled.


### Example

Here is an example of setting the environment variables:

```yaml
    environment:
        - TZ=America/Los_Angeles
        - PUID=1000
        - PGID=1000
        - APP_DATA_DIR=/data/trailarr
        - DELETE_TRAILER_CONNECTION=True
        - DELETE_TRAILER_MEDIA=False
    volumes:
        - /var/appdata/trailarr:/data/trailarr
```

This sets the environment variables to run the app with following settings:

- Timezone: America/Los_Angeles
- User ID: 1000
- Group ID: 1000
- Application data directory: /data/trailarr
- Volume mapping: /var/appdata/trailarr:/data/trailarr
- Delete trailers on removing media from ARR: enabled (but only delete trailers when media also removed: disabled)
