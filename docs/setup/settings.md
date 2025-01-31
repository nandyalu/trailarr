There are several settings that you can use to customize the behavior of Trailarr app. These settings can be set by opening the app in browser [http://localhost:7889/settings](http://localhost:8000/settings){:target="_blank"} and navigatings  to `Settings > Trailer` page.

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

### Trailer Minimum Duration

- Default is `30` seconds

Select the minimum duration of the trailers to download. Trailers with a duration less than this value will be skipped.
Minimum is `30` seconds.

### Trailer Maximum Duration

- Default is `600` seconds

Select the maximum duration of the trailers to download. Trailers with a duration greater than this value will be skipped.
Minimum is `Trailer Minimum Duration + 60` seconds. Maximum is `600` seconds.

!!! info
    If you want to download trailers with a duration of 2 minutes to 5 minutes, set `Trailer Minimum Duration` to `120` seconds and `Trailer Maximum Duration` to `300` seconds.

### Trailer Resolution

- Default is `1080`

Select the resolution of the trailers to download. Available options are `240`, `360`, `480`, `720`, `1080`, `1440`, `2160`.

!!! info
    If set to `1080`, the app will try to download trailers with a resolution of 1080p, if available. If not, it will fallback to the next lower resolution.

### Trailer File Format

- Default is `mkv`

Select the file format of the trailers to download. Available options are `mkv`, `mp4`, `webm`.


Not all file formats support all video and audio codecs. The following tables shows the supported formats:

Video Codecs:

| Format | h264               | h265               | vp8                | vp9                | av1                |
|:------:|:------------------:|:------------------:|:------------------:|:------------------:|:------------------:|
| mkv    | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| mp4    | :white_check_mark: | :white_check_mark: | :x:                | :x:                | :white_check_mark: |
| webm   | :x:                | :x:                | :white_check_mark: | :white_check_mark: | :white_check_mark: |

Audio Codecs:

| Format | aac                | ac3                | eac3               | flac               | opus               |
|:------:|:------------------:|:------------------:|:------------------:|:------------------:|:------------------:|
| mkv    | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| mp4    | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| webm   | :x:                | :x:                | :x:                | :x:                | :white_check_mark: |

!!! note ""
    Please make sure to select a file format that supports the video and audio codecs you want to use.


!!! info
    App will download trailer in the available format and then convert it to the selected format using Ffmpeg.

### Trailer Video Format

- Default is `h264`

Select the video codec of the trailers to download. Available options are `h264`, `h265`, `vp8`, `vp9`, `av1`.

!!! info
    App will download trailer in the available codec and then convert it to the selected codec using Ffmpeg.

!!! warning
    If `av1` is selected, app will try to download trailer in `av1` format. If not available, it will fallback to `vp9`. App will not convert the downloaded trailer to `av1` format.

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

### Trailer Web Optimized

- Default is `true`

Enable this setting to optimize trailers for web streaming. This will allow trailers to start playing faster while streaming over network. Might slightly increase file size.

## Advanced Settings

These are advanced settings, if you don't know what they do, do not modify them!

### Log Level

- Default is `Info`

Select the logging level for the app. Available options are `Debug`, `Info`, `Warning`, `Error`.

??? info
    If you are having issues and need to troubleshoot or request help, set the log level to `Debug` to get more detailed logs.

### Trailer Audio Volume Level

- Default is `100`

Set the audio volume level of the downloaded trailer. Use this option to increase or decrease audio loudness of the trailer.
Set to `100` for no change. Minimum is `1`. Maximum is `200`. 

!!! warning
    Do not modify this setting unless you know what you are doing.

### Exclude Words in Title

- Default is `` (empty)

Enter a comma separated list of words to exclude from the title of the trailers. If the title of the trailer contains any of the words in the list, the trailer will be skipped. For example, `teaser,clip,featurette`.

### Trailer Always Search

- Default is `false`

Enable this setting to always search YouTube for trailers. If disabled, the app will only search YouTube if it cannot find a trailer in Radarr, Sonarr doesn't provide youtube trailer ids.

### Youtube Search Query

- Default is `{title} {year} {is_movie} trailer`

Enter a search query to use when searching for trailers on YouTube. Wrap a supported variable in `{}` like `{title}` and it will be replaced in the actual search query. Supports [Python string formatting options](https://docs.python.org/3/library/string.html#formatstrings).

Available options are:

- `title`: Title of the media. Eg: 'The Matrix'
- `year`: Year of the media. Eg: '1999'
- `is_movie`: 'movie' if the media is a movie, 'series' if the media is a series.
- `language`: Language of the media. Eg: 'English'

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

See [Export YouTube Cookies.txt file](../help/common.md#export-youtube-cookiestxt-file) for more info.

!!! warning
    Make sure to save the cookies file in a secure location and map the volume to the container. Set the path to the file in this setting.


## Experimental Settings

These are experimental options, might not work as expected! You can enable them if you want to try. Please report any issues on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"} (recommended) or [Github](https://github.com/nandyalu/trailarr/){:target="_blank"}

### Trailer Remove Silence

- Default is `false`

Enable this option to let Trailarr analyse the video file and remove it. This helps remove video end credits usually added to show end credits or other video suggestions on YouTube.

Silence is detected using `ffmpeg silencedetect` and if there is any silence (less than 30dB audio) for more than 3 seconds at the end of video file, video will be trimmed till the starting timestamp of the detected silence.

## New Download Method

- Default is `false`

Default `yt-dlp` download and convert method has some limitations and a few bugs. So, a new download method that downloads using `yt-dlp` and converts using `ffmpeg` is added as an experimental option. You can enable this option to try the new method.

!!! note
    This option needs to be enabled if you want to use hardware acceleration for video conversion.

## Hardware Acceleration

- Default is `false`

Enable this setting to use hardware acceleration for video conversion. This will speed up the conversion process by using the NVIDIA GPU for encoding and decoding.

!!! note
    This setting is available only if an NVIDIA GPU is detected on the host system. For setup instructions, see [Hardware Acceleration](../install/hardware-acceleration.md).