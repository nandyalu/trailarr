
### Video Format

| Type   | Required | Default | Valid Values                     |
|:------:|:--------:|:-------:|:--------------------------------:|
| String | Yes      | vp9     | h264, h265, vp8, vp9, av1, copy  |

Select the video format/codec of the trailers to download.

Trailarr will try to download trailer in the selected codec if available, else it will download in best format available and then convert it to the selected codec using Ffmpeg.

!!! note
    If you select `copy`, Trailarr will not convert the video codec and will download the trailer in the best available format. Use with `File Format` as `mkv` as other formats do not support all video codecs.

!!! warning
    If `av1` is selected, app will try to download trailer in `av1` format. If not available, it will fallback to `vp9`. App will not convert the downloaded trailer to `av1` format.

### Video Resolution

| Type    | Required | Default | Valid Values                      |
|:-------:|:--------:|:-------:|:---------------------------------:|
| Integer | Yes      | 1080    | 0, 480, 720, 1080, 1440, 2160     |

Select the video resolution of the trailers to download.

Trailarr will try to download trailer in the selected resolution if available, else it will download in next best resolution available.

!!! note
    If you select `0` (shown as best in the UI), Trailarr will try to download the best available resolution of the trailer.