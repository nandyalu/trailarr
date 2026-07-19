
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

{{ version_badge("upd", "0.10.0") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

!!! warning "Deprecated"
    Downloads are now tracked per profile, so this option is no longer needed to prevent re-downloads — a profile that already owns a downloaded video never downloads again, even if the media item stays monitored. `Stop Monitoring` will be removed in an upcoming release.

Legacy behavior, still honored for now: when a profile with `Stop Monitoring = true` successfully downloads, the media item is treated as **fully satisfied** — no other matching profiles will download for it afterwards. Since `v0.10.0`, the media item's monitor toggle itself is **not** switched off anymore; monitoring always stays as you set it.

If you want multiple videos per media item, simply create multiple profiles and leave `Stop Monitoring = false` on all of them — each profile downloads and keeps its own video.

!!! example
    If you want to download 2 trailers (English and Spanish) for every media item, create two profiles with `Stop Monitoring = false` on both:
    
    ```
        Profile Name: Spanish Trailer
        Stop Monitoring: false
        Priority: 100
        -------------------------------
        Profile Name: English Trailer
        Stop Monitoring: false
        Priority: 0 (or any lower number than the Spanish Trailer profile)
    ```

    Each profile downloads and tracks its own trailer, and the media item stays monitored. If `Stop Monitoring` were `true` on the English profile instead, its successful download would mark the media fully satisfied and prevent any other matching profiles from downloading afterwards.
