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


## File Settings

### Wait For Media

- Default is `false`

Enable this setting to wait for media to be downloaded before downloading trailers.


## Advanced Settings

These are advanced settings, if you don't know what they do, do not modify them!

### Log Level

- Default is `Info`

Select the logging level for the app. Available options are `Debug`, `Info`, `Warning`, `Error`.

??? info
    If you are having issues and need to troubleshoot or request help, set the log level to `Debug` to get more detailed logs.


### Yt-dlp Cookies Path

- Default is `None`

If you are having issues downloading trailers due to age restrictions, bot detection, etc., you can set the path to a file containing YouTube cookies. This will allow the app to use the cookies to bypass restrictions.

See [Export YouTube Cookies.txt file](../help/common.md#export-youtube-cookiestxt-file) for more info.

!!! tip
    Use the `📁` (folder) icon to open a dialog that shows the container folders and files. Navigate to your `cookies.txt` file and confirm.

!!! warning
    Make sure to save the cookies file in a secure location and map the volume to the container. Set the path to the file in this setting.


## Experimental Settings

These are experimental options, might not work as expected! You can enable them if you want to try. Please report any issues on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"} (recommended) or [Github](https://github.com/nandyalu/trailarr/){:target="_blank"}

### Hardware Acceleration

- Default is `false`

Enable this setting to use hardware acceleration for video conversion. This will speed up the conversion process by using the NVIDIA GPU for encoding and decoding.

!!! note
    This setting is available only if an NVIDIA GPU is detected on the host system. For setup instructions, see [Hardware Acceleration](../install/hardware-acceleration.md).

### Update Yt-dlp

- Default is `false`

Enable this setting to update `yt-dlp` to the latest version on every app start. This will ensure that the app uses the latest features and bug fixes.

### URL Base

- Default is  `(empty)`

Enter the base URL of the app for use with reverse proxies. This will allow the app to generate correct URLs when behind a reverse proxy.