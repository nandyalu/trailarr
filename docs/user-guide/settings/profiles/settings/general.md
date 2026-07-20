
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

## Stop Monitoring

{{ version_badge("upd", "0.10.1") }}

This option has been **removed in v0.10.1**. Downloads have been tracked per profile since `v0.10.0`, so it was no longer needed to prevent re-downloads — a profile that already owns a downloaded video never downloads again, and downloading never changes the media item's monitor state.

If you want multiple videos per media item, simply create multiple profiles — each matching profile downloads and keeps track of its own video.

!!! note "Overlapping profiles"
    If several of your profiles match the same media and you previously relied on a `Stop Monitoring` profile's download to suppress the others, each matching profile now downloads its own video. Narrow or split the profile filters if you want only one video per media item. Non-overlapping setups — like the default Movie/Series profiles — are unaffected.
