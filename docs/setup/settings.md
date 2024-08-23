There are a few settings that you can use to customize the behavior of Trailarr app. These settings can be set by opening the app in browser [http://localhost:7889/settings](http://localhost:8000/settings){:target="_blank"} and navigatings  to `Settings > Trailer` page.

## General Settings

### Debug Mode

- Default is `false`

Enable debug mode to display additional information in the logs. This is useful for troubleshooting issues.

### Monitor Trailers

- Default is `true`

Enable this setting to monitor trailers for connections. When enabled, the app will automatically download trailers for media in Radarr and Sonarr.

!!! note
    Disabling this will disable monitoring of media for all connections.

### Monitor Interval

- Default is `60` minutes. Minimum is `10` minutes`. 

Frequency (in minutes) to check for new media in Radarr/Sonarr.


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
