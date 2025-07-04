
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
| String | Yes      | {title} ({year})-trailer.{ext}        | Any string (Max length: 150 characters) |

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
| txdb_id              | TMDB ID for Movies, TVDB ID for Series. Eg: '603'                                                             |
| year                 | Year of the media. Eg: '1999'                                                                                 |
| acodec               | Audio codec of the media. Eg: 'aac'                                                                           |
| resolution           | Resolution of the media. Eg: '1080p'                                                                          |
| vcodec               | Video codec of the media. Eg: 'h264'                                                                          |
| youtube_id           | YouTube ID of the trailer. Eg: 'KbWtUJjMj3Y'                                                                  |

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
| String | No       | Trailers     | Any string (Max length: 50 characters) |

This setting allows you to specify the name of the folder where the trailer files will be saved. If `Folder Enabled` is set to `false`, this setting will be ignored.


## Embed Metadata

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | true    | true or false |

This setting allows you to embed metadata in the trailer files. If enabled, the metadata will be embedded in the trailer files using Ffmpeg.

## Remove Silence

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

Enable this option to let Trailarr analyse the video file and remove it. This helps remove video end credits usually added to show end credits or other video suggestions on YouTube.

Silence is detected using `ffmpeg silencedetect` and if there is any silence (less than 30dB audio) for more than 3 seconds at the end of video file, video will be trimmed till the starting timestamp of the detected silence.

