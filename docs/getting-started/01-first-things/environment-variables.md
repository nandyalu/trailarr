**Environment variables are OPTIONAL.**

!!! info "An environment variable overrides a stored setting"
    {{ version_badge("upd", "0.11.4") }}
    Trailarr saves the settings you change in the WebUI to a `.env` file in your data directory. At startup, a variable that you set for the container (or for the service) overrides the value in that file. Use this to correct a setting that blocks your access to the WebUI, for example `URL_BASE` or `WEBUI_PASSWORD`. Before v0.11.4, the stored value replaced the variable, and your change did nothing.

    If you want to change the setting in the WebUI later, remove the variable first. While the variable is set, the WebUI shows your change, but the variable overrides your change at the next start.

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

!!! warning "Use with caution"
    When auth is disabled, a `session_id` is generated to use with frontend without authentication by calling auth endpoints. These endpoints can be reached from other apps or services to get a `session_id` and use that for authentication. So, use with caution!

!!! note "No logout with auth disabled"
    {{ version_badge("upd", "0.11.0") }}
    When auth is disabled, the web UI hides the logout button — there is no session to log out of. After a period of inactivity, the UI pauses live updates, deletes its session id on the server, and shows a **Session Paused** dialog. Requests that replay the old session id get a `401` response. Click **Resume** to continue with a fresh session.

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

!!! info "You can also set a new password here"
    {{ version_badge("upd", "0.11.4") }}
    A value that is not empty becomes your new password. Trailarr hashes it at startup and stores only the hash — the app never keeps your password as plain text. Remove the variable after the first start. If you keep the variable, Trailarr sets the same password at every start, and you cannot change the password in the WebUI.

To change the password, go to `Settings > About > Password` in web interface. 

!!! info
    If you change your password from the web interface, the password will be hashed and stored internally. There is no way to retrieve the password as only a hashed version is stored, you need to reset it if you forget it.

!!! warning
    Once you change your password, don't forget to remove the `WEBUI_PASSWORD` environment variable from the docker-compose file.


### `FILES_FULL_SCAN`

{{ version_badge("add", "0.9.1") }}

- Default: `false`

When set to `true`, the next **Scan Media Folders** task run will scan every media folder in full, ignoring the folder-change optimisation that normally skips unchanged folders. Useful for correcting stale download records or `media_exists` flags after trailers are added or removed outside of Trailarr.

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

