# Trailarr Settings

There are several settings that you can use to customize the behavior of Trailarr app. These settings can be set by opening the app in browser [http://localhost:7889/settings](http://localhost:8000/settings){:target="_blank"} and navigating to `Settings > General` page.

## General Settings

### Monitor Trailers

- Default is `true`

Enable this setting to monitor trailers for connections. When enabled, the app will automatically download trailers for media in Radarr and Sonarr.

!!! note
    Disabling this will disable monitoring of media for all connections.

### Monitor Interval

- Default is `60` minutes. Minimum is `10` minutes`. 

Frequency (in minutes) to check for new media in Radarr/Sonarr.

!!! info Restart Required
    Changing this setting will require a restart of the app (container) to take effect.

### App Theme

- Default is `Auto`. Available options are `Light`, `Dark`, and `Auto`.

Select the theme for the app UI.
- Light theme will use light colors for the UI.
- Dark theme will use dark colors for the UI.
- Auto theme will use the system theme of the host system.

!!! tip "Selection will be saved across devices"
    Once you change the theme, Trailarr will remember the selection for next time across your devices.


## File Settings

### Wait For Media

- Default is `false`

Enable this setting to wait for media to be downloaded before downloading trailers.

### Delete Trailer After All Media files Deleted

- Default is `false`

Enable this setting to delete the trailer after all media files are deleted.

## Advanced Settings

These are advanced settings, if you don't know what they do, do not modify them!

### Log Level

- Default is `Info`

Select the logging level for the app logs to display in it's console. Available options are `Debug`, `Info`, `Warning`, `Error`.

!!! info "Console logs only"
    Trailarr logs all logs in it's database (starting from `v0.4.3`), setting this will change what logs are reported by container to Docker.

??? info
    If you are having issues and need to troubleshoot or request help, set the log level to `Debug` to get more detailed logs.


### Yt-dlp Cookies Path

- Default is `None`

If you are having issues downloading trailers due to age restrictions, bot detection, etc., you can set the path to a file containing YouTube cookies. This will allow the app to use the cookies to bypass restrictions.

See [Export YouTube Cookies.txt file](../../../troubleshooting/common-issues.md#export-youtube-cookiestxt-file) for more info.

!!! tip
    Use the `📁` (folder) icon to open a dialog that shows the container folders and files. Navigate to your `cookies.txt` file and confirm.

!!! warning
    Make sure to save the cookies file in a secure location and map the volume to the container. Set the path to the file in this setting.

!!! warning "Do NOT use cookies with New Installations"
    If you are just setting up Trailarr, it is recommended to not use cookies initially for downloading trailers in bulk, as that might lead to your account being flagged for suspicious activity and YouTube placing a ban on your account. Instead, try downloading trailers without cookies first and then setup cookies once the bulk downloads are complete.
    
    Alternatively, you can try setting up a new YouTube account and use cookies from that new account.


## Experimental Settings

These are experimental options, might not work as expected! You can enable them if you want to try. Please report any issues on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"} (recommended) or [Github](https://github.com/nandyalu/trailarr/){:target="_blank"}

### AMD GPU Acceleration

- Default is `true`

Enable this setting to use hardware acceleration for the conversion process by using the AMD GPU for encoding and decoding.

!!! note
    This setting is available only if an AMD GPU is detected on the host system. For setup instructions, see [Hardware Acceleration](../../../getting-started/02-installation/hardware-acceleration.md).

### Intel GPU Acceleration

- Default is `true`

Enable this setting to use hardware acceleration for the conversion process by using the Intel GPU for encoding and decoding.

!!! note
    This setting is available only if an Intel GPU is detected on the host system. For setup instructions, see [Hardware Acceleration](../../../getting-started/02-installation/hardware-acceleration.md).

### NVIDIA GPU Acceleration

- Default is `true`

Enable this setting to use hardware acceleration for the conversion process by using the NVIDIA GPU for encoding and decoding.

!!! note
    This setting is available only if an NVIDIA GPU is detected on the host system. For setup instructions, see [Hardware Acceleration](../../../getting-started/02-installation/hardware-acceleration.md).

### Update Yt-dlp

- Default is `false`

Enable this setting to update `yt-dlp` to the latest version on every app start. This will ensure that the app uses the latest features and bug fixes.

### URL Base

- Default is  `(empty)`

Enter the base URL of the app for use with reverse proxies. This will allow the app to generate correct URLs when behind a reverse proxy.