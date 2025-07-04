
## Audio Format

| Type   | Required | Default | Valid Values                     |
|:------:|:--------:|:-------:|:--------------------------------:|
| String | Yes      | opus    | aac, ac3, eac3, flac, opus, copy |

Select the audio format/codec of the trailers to download.

!!! info ""
    Trailarr will try to download trailer in the selected codec if available, else it will download in available codec and then convert it to the selected codec using Ffmpeg.

!!! note
    If you select `copy`, Trailarr will not convert the audio codec and will download the trailer in the best format available. Use with `File Format` as `mkv` as other formats do not support all audio codecs.


## Audio Volume Level

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Integer | Yes      | 100     | 1 to 200      |

This setting allows you to set the audio volume level of the trailer files. The value is a percentage of the original volume, where 100 is the original volume, 200 is double the volume, and 50 is half the volume.

!!! note
    If `Audio Format` is set to `copy`, Trailarr will try to change audio volume using downloaded audio format, might fallback to `opus`.

