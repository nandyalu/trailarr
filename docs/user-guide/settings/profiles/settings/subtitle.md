
## Subtitles Enabled

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | true    | true or false |

Enable this setting to download subtitles for trailers, if available.

## Auto-Generated Subtitles

{{ version_badge("add", "0.11.1") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

Enable this setting to also accept YouTube auto-generated (AI) subtitles.

When enabled, Trailarr prefers the uploader's subtitles for a language and uses the auto-generated ones only when the video has no uploader subtitles.

!!! note ""
    Before `v0.11.1`, Trailarr downloaded only auto-generated subtitles. Auto-generated subtitles are often low quality, so they are now off by default ([#644](https://github.com/nandyalu/trailarr/issues/644)).

## Subtitles Format

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| String  | Yes      | srt     | srt, vtt      |

Select the format of the subtitles to download. Available options are `srt`, `vtt`.

!!! note ""
    Mp4 does not support `srt`, so `mov_text` will be used instead. 

!!! info
    App will download subtitles in the available format and then convert it to the selected format using Ffmpeg.

## Subtitles Language

| Type    | Required | Default | Valid Values                     |
|:-------:|:--------:|:-------:|:--------------------------------:|
| String  | Yes      | en      | valid ISO 639-1 language code(s) |

Select the language of the subtitles to download. 

A valid ISO 639-1 language code is required. See [ISO 639-1 language codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes){:target="_blank"} for more information.

!!! info
    Multiple languages can be set with a comma separated list. For example, `en,es,fr`.

!!! info
    You can also set it to `all` to download all available subtitles.