
## Profile Name

| Type   | Required | Valid Values                            |
|:------:|:--------:|:---------------------------------------:|
| String | Yes      | Any string (Max length: 100 characters) |

This is the name of the profile that will be displayed in the UI. Choose a name that clearly identifies the purpose of the profile or a silly name (it doesn't really matter).

## Profile Enabled

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | true    | true or false |


This setting allows you to enable or disable the profile. Only enabled profiles will be used for downloading and processing trailers.

!!! note
    Disabled profiles can still be used for manual trailer downloads from the UI, but they will not be applied automatically during the `Download Missing Trailers` task.

## Priority

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:-------------:|
| Integer | Yes      | 0       | 0 to 999     |

This setting determines the order in which profile is applied when multiple profiles match a media item. Profiles with a higher priority (highest numerical value) will be processed first. 

!!! warning
    If two profiles have the same priority, any one of them can be used, so it is recommended to use unique priorities for each profile.


## Retry Count

{{ version_badge("add", "0.6.10") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Integer | Yes      | 2       | 0 to 9        |


This setting determines how many times Trailarr should retry downloading a trailer if the previous download attempts failed. A failed download can occur due to various reasons such as network issues, YouTube restrictions, or problems with the video itself. By default, Trailarr will retry downloading a trailer 2 times before giving up. 

Setting this value to `0` will disable retries and Trailarr will only attempt to download a trailer once. 

Setting this value to a higher number will allow Trailarr to make multiple attempts to download a trailer, increasing the chances of a successful download in case of temporary issues.

!!! note "Retries vs. backoff"
    {{ version_badge("add", "0.10.0") }} Retries here happen immediately, within the same task run. If all retries fail, the download is attempted again on a later task run with an increasing delay — 1 day after the first failure, then 2 days, then 4, capped at weekly. See [Download Missing Trailers](../../../tasks/index.md#download-missing-trailers).

## Trailer Language

{{ version_badge("add", "0.13.0") }}

| Type    | Required | Default | Valid Values                     |
|:-------:|:--------:|:-------:|:--------------------------------:|
| String  | No       | empty   | empty, or an ISO 639-1 code      |

Which language of trailer this profile downloads. Leave it empty for any language, which is what every profile did before this setting existed.

A language here is a **filter, not a preference**. A profile that asks for `it` downloads an Italian trailer or nothing: Trailarr never downloads a German trailer instead, because a trailer in the wrong language is not what you asked for. When Trailarr knows no trailer in that language, it searches YouTube with the [Search Query](search.md#search-query) of the profile, which you write and can aim at your language.

Trailarr only knows the language of a video when something told it. TMDB records a language for each trailer it lists, and you can [add a video](../../../library/media-details/index.md#known-videos) with a language yourself. The id that Radarr reports carries no language, so a profile that asks for a language does not use it.

!!! tip "One profile per language"
    To keep an Italian trailer and an English one for the same media item, make two profiles, one with `it` and one with `en`. Each downloads its own trailer and keeps track of its own file.

!!! note "This setting needs a TMDB API key"
    The field is disabled until you add a [TMDB API key](../../tmdb.md) in `Settings > General`, and every profile takes any language until then. Only TMDB records which language a trailer is in, so without a key Trailarr cannot tell — and a language it cannot check would match nothing, making every download fall back to a YouTube search.

## Stop Monitoring

{{ version_badge("upd", "0.10.2") }}

This option has been **removed in v0.10.2**. Downloads have been tracked per profile since `v0.10.0`, so it was no longer needed to prevent re-downloads — a profile that already owns a downloaded video never downloads again, and downloading never changes the media item's monitor state.

If you want multiple videos per media item, simply create multiple profiles — each matching profile downloads and keeps track of its own video.

!!! note "Overlapping profiles"
    If several of your profiles match the same media and you previously relied on a `Stop Monitoring` profile's download to suppress the others, each matching profile now downloads its own video. Narrow or split the profile filters if you want only one video per media item. Non-overlapping setups — like the default Movie/Series profiles — are unaffected.
