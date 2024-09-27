There are a few settings that you can use to customize the behavior of Trailarr app. These settings can be set by opening the app in browser [http://localhost:7889/settings](http://localhost:8000/settings){:target="_blank"} and navigatings  to `Settings > Trailer` page.

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

### Trailer Folder Movie

- Default is `false`

Enable this setting to save trailers in a `Trailers` folder inside the movie folder.

### Trailer Folder Series

- Default is `true`

Enable this setting to save trailers in a `Trailers` folder inside the series folder.


## Trailer Settings

### Trailer Resolution

- Default is `1080`

Select the resolution of the trailers to download. Available options are `240`, `360`, `480`, `720`, `1080`, `1440`, `2160`.

!!! info
    If set to `1080`, the app will try to download trailers with a resolution of 1080p, if available. If not, it will fallback to the next lower resolution.

### Trailer File Format

- Default is `mkv`

Select the file format of the trailers to download. Available options are `mkv`, `mp4`, `webm`.

!!! info
    App will download trailer in the available format and then convert it to the selected format using Ffmpeg.

### Trailer Video Format

- Default is `h264`

Select the video codec of the trailers to download. Available options are `h264`, `h265`, `vp8`, `vp9`, `av1`.

!!! info
    App will download trailer in the available codec and then convert it to the selected codec using Ffmpeg.

### Trailer Audio Format

- Default is `aac`

Select the audio codec of the trailers to download. Available options are `aac`, `ac3`, `eac3`, `flac`, `opus`.

!!! info
    App will download trailer in the available codec and then convert it to the selected codec using Ffmpeg.

### Trailer Subtitles Enabled

- Default is `true`

Enable this setting to download subtitles for trailers, if available.

### Trailer Subtitles Format

- Default is `srt`

Select the format of the subtitles to download. Available options are `srt`, `vtt`, `pgs`.

!!! info
    App will download subtitles in the available format and then convert it to the selected format using Ffmpeg.

### Trailer Subtitles Language

- Default is `en`

Select the language of the subtitles to download. A valid ISO 639-1 language code is required. See [ISO 639-1 language codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes){:target="_blank"} for more information.

!!! info
    Multiple languages can be set with a comma separated list. For example, `en,es,fr`.

## Other Settings

### Trailer Embed Metadata

- Default is `true`

Enable this setting to embed metadata in the trailers.

### Trailer Remove SponsorBlocks

- Default is `true`

Enable this setting to remove sponsor blocks from the trailers, if available. Sponsor blocks are sections of the trailer that contain promotional content like intros, outros, ads, etc.

### Trailer Web Optimized

- Default is `true`

Enable this setting to optimize trailers for web streaming. This will allow trailers to start playing faster while streaming over network. Might slightly increase file size.

## Advanced Settings

### Log Level

- Default is `Info`

Select the logging level for the app. Available options are `Debug`, `Info`, `Warning`, `Error`.

??? info
    If you are having issues and need to troubleshoot or request help, set the log level to `Debug` to get more detailed logs.

### Trailer File Name

- Default is `{title} - Trailer-trailer.{ext}`

Select the file name format for the trailers. Wrap a supported variable in `{}` like `{title}` and it will be replaced in the actual file name. Supports [Python string formatting options](https://docs.python.org/3/library/string.html#formatstrings). 

Available options are:

- `title`: Title of the media. Eg: 'The Matrix'
- `year`: Year of the media. Eg: '1999'
- `resolution`: Resolution of the trailer. Eg: '1080p'
- `vcodec`: Video codec of the trailer. Eg: 'h264'
- `acodec`: Audio codec of the trailer. Eg: 'aac'

### Yt-dlp Cookies Path

- Default is `None`

If you are having issues downloading trailers due to age restrictions, bot detection, etc., you can set the path to a file containing YouTube cookies. This will allow the app to use the cookies to bypass restrictions.

See yt-dlp [documentation](https://github.com/yt-dlp/yt-dlp){:target="_blank"} for more information on how to get the cookies file.

!!! warning
    Make sure to save the cookies file in a secure location and map the volume to the container. Set the path to the file in this setting.
