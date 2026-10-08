
## File Format

| Type   | Required | Default | Valid Values          |
|:------:|:--------:|:-------:|:---------------------:|
| String | Yes      | mkv     | mkv, mp4, webm        |

Desired file format of the trailer file. Available options are `mkv`, `mp4`, `webm`.


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


## File Name

| Type   | Required | Default                               | Valid Values                            |
|:------:|:--------:|:-------------------------------------:|:---------------------------------------:|
| String | Yes      | {title} ({year})-{video_type}.{ext}   | Any string (Max length: 150 characters) |

File name format for the trailers. 

Wrap a supported variable in `{}` like `{title}` and it will be replaced in the actual file name. Supports [Python string formatting options](https://docs.python.org/3/library/string.html#formatstrings). 

You can use the following placeholders in the file name:


| Placeholder          | Description                                                                                                   |
|---------------------:|:--------------------------------------------------------------------------------------------------------------|
| clean_title          | Cleaned title of the media. Eg: 'thematrix'                                                                   |
| imdb_id              | IMDB ID of the media. Eg: 'tt0133093'                                                                         |
| is_movie             | 'movie' if the media is a movie, 'series' if the media is a series.                                           |
| language             | Language of the media in Radarr/Sonarr. Eg: 'English'                                                         |
| media_filename       | Filename of the media, Movies only, Series will empty. Eg: 'The.Matrix.1999.1080p.BluRay.x264.DTS-FGT'        |
| studio               | Studio of the media. Eg: 'Village Roadshow Pictures'                                                          |
| title                | Title of the media. Eg: 'The Matrix'                                                                          |
| title_slug           | TMDB ID for Movies and a hash seperated title for Series. Eg: '603' (movie) or 'the-big-bang-theory' (series) |
| tmdb_id              | TMDB (The Movie Database) ID of the media item. Eg: `603`. `None` for Plex-only items without a TMDB entry.   |
| tvdb_id              | TVDB (The TV Database) ID of the media item. Eg: `71663`. `None` for Plex-only items without a TVDB entry.    |
| txdb_id              | Legacy combined ID — TMDB ID for movies, TVDB ID for series, as a string. Eg: `'603'`. Prefer `tmdb_id` or `tvdb_id`. |
| year                 | Year of the media. Eg: '1999'                                                                                 |
| acodec               | Audio codec of the media. Eg: 'aac'                                                                           |
| resolution           | Resolution of the media. Eg: '1080p'                                                                          |
| vcodec               | Video codec of the media. Eg: 'h264'                                                                          |
| youtube_id           | YouTube ID of the trailer. Eg: 'KbWtUJjMj3Y'                                                                  |
| video_type           | {{ version_badge("add", "0.14.0") }} The suffix that Plex and Jellyfin read for the [Video Type](general.md#video-type) of the profile. Eg: 'trailer', 'featurette'. See the table below. |

{{ version_badge("add", "0.14.0") }} A player reads the kind of an extra from the end of its file name, so the `{video_type}` placeholder writes a name that both Plex and Jellyfin read. Neither player knows a teaser or bloopers, and Plex does not know a clip, so Trailarr writes the nearest name that both read. The download still records its real type. One consequence: when the row of such a file is lost, for example after a media item is removed and added again, the next scan reads the file back by its name, so a teaser file becomes a trailer and a bloopers file becomes other.

| Video Type        | `{video_type}` in the file name | Default folder     |
|:-----------------:|:-------------------------------:|:------------------:|
| Trailer           | `trailer`                       | `Trailers`         |
| Teaser            | `trailer`                       | `Trailers`         |
| Clip              | `scene`                         | `Scenes`           |
| Featurette        | `featurette`                    | `Featurettes`      |
| Behind the Scenes | `behindthescenes`               | `Behind The Scenes`|
| Bloopers          | `other`                         | `Other`            |
| Other             | `other`                         | `Other`            |

{{ version_badge("upd", "0.14.0") }} A new profile starts with `{title} ({year})-{video_type}.{ext}` and the folder `{video_type}`. A profile that was created before `v0.14.0` keeps its file name, which ends in `-trailer.{ext}`, and its folder `Trailers`. A `Featurette` profile with that file name writes `-trailer`, and Plex shows the video as a trailer. Change the file name of such a profile to end in `-{video_type}.{ext}` to get the right name.

!!! info
    Filename will be cleaned to remove restricted characters `<>:"/\\|?*\x00-\x1F` to ensure compatibility with filesystems.


## Folder Enabled

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

This setting allows you to enable or disable the folder creation for the trailers. 

- If enabled, a folder will be created for the trailer files in the media folder. 
- If disabled, the trailer files will be saved directly in the media folder.

!!! note
    It is recommended to enable this setting for Series trailers.

## Folder Name

| Type   | Required | Default      | Valid Values                           |
|:------:|:--------:|:-------------|:--------------------------------------:|
| String | No       | {video_type} | Any string (Max length: 50 characters) |

This setting allows you to specify the name of the folder where the trailer files will be saved. If `Folder Enabled` is set to `false`, this setting will be ignored.

{{ version_badge("add", "0.14.0") }} The folder name takes the `{video_type}` placeholder, which Trailarr replaces with the folder that both Plex and Jellyfin read for the [Video Type](general.md#video-type) of the profile: `Trailers`, `Scenes`, `Featurettes`, `Behind The Scenes` or `Other` (see the table under [File Name](#file-name)). An empty folder name takes that folder too. A profile that was created before `v0.14.0` keeps the folder name `Trailers`.


## Custom Save Folder Path

| Type   | Required | Default        | Valid Values                           |
|:------:|:--------:|:--------------:|:--------------------------------------:|
| String | No       | {media_folder} | Any valid file path                    |

This setting allows you to specify a custom save path for the trailer files. Default is `{media_folder}`, which saves the trailers in the same folder as the media item.

You can use the following placeholders in the custom save folder path:

| Placeholder          | Description                                                                                                   |
|---------------------:|:--------------------------------------------------------------------------------------------------------------|
| clean_title          | Cleaned title of the media. Eg: 'thematrix'                                                                   |
| imdb_id              | IMDB ID of the media. Eg: 'tt0133093'                                                                         |
| is_movie             | 'movie' if the media is a movie, 'series' if the media is a series.                                           |
| language             | Language of the media in Radarr/Sonarr. Eg: 'English'                                                         |
| media_filename       | Filename of the media, Movies only, Series will empty. Eg: 'The.Matrix.1999.1080p.BluRay.x264.DTS-FGT'        |
| media_folder         | Folder path of the media item. Eg: '/media/movies/The Matrix (1999)'                                          |
| studio               | Studio of the media. Eg: 'Village Roadshow Pictures'                                                          |
| title                | Title of the media. Eg: 'The Matrix'                                                                          |
| title_slug           | TMDB ID for Movies and a hash seperated title for Series. Eg: '603' (movie) or 'the-big-bang-theory' (series) |
| tmdb_id              | TMDB (The Movie Database) ID of the media item. Eg: `603`. `None` for Plex-only items without a TMDB entry.   |
| tvdb_id              | TVDB (The TV Database) ID of the media item. Eg: `71663`. `None` for Plex-only items without a TVDB entry.    |
| txdb_id              | Legacy combined ID — TMDB ID for movies, TVDB ID for series, as a string. Eg: `'603'`. Prefer `tmdb_id` or `tvdb_id`. |
| year                 | Year of the media. Eg: '1999'                                                                                 |
| acodec               | Audio codec of the media. Eg: 'aac'                                                                           |
| resolution           | Resolution of the media. Eg: '1080p'                                                                          |
| vcodec               | Video codec of the media. Eg: 'h264'                                                                          |
| youtube_id           | YouTube ID of the trailer. Eg: 'KbWtUJjMj3Y'                                                                  |

!!! info
    Filename will be cleaned to remove restricted characters `<>:"/\\|?*\x00-\x1F` to ensure compatibility with filesystems.


## Embed Metadata

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | true    | true or false |

This setting allows you to embed metadata in the trailer files. If enabled, the metadata will be embedded in the trailer files using Ffmpeg.

## Remove Silence

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

Enable this option to let Trailarr analyse the video file to detect silence towards the end of video and remove it. This helps remove video end credits usually added to show end credits or other video suggestions on YouTube.

Silence is detected using `ffmpeg silencedetect` and if there is any silence (less than 30dB audio) for more than 3 seconds at the end of video file, video will be trimmed till the starting timestamp of the detected silence.

