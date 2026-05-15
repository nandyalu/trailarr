
## Video Type

{{ version_badge("add", "0.9.5") }}

| Type   | Required | Default | Valid Values                                                                        |
|:------:|:--------:|:-------:|:-----------------------------------------------------------------------------------:|
| String | Yes      | trailer | trailer, teaser, clip, behind the scenes, bloopers, featurette, opening credits     |

Select the type of video to search for and download. Defaults to `trailer`.

!!! note "TMDB API Key required for non-trailer types"
    Searching for video types other than `trailer` requires a TMDB API Key to be set in **Settings > General > Integrations**. Without it, the profile will fall back to searching YouTube directly, which may yield less accurate results.

!!! tip
    Use separate profiles with different video types to download, for example, both a trailer and a featurette for the same media item.

## For Movies

{{ version_badge("add", "0.9.5") }}

| Type    | Required | Default | Valid Values          |
|:-------:|:--------:|:-------:|:---------------------:|
| Boolean | Yes      | true    | true (Movies) or false (Series) |

Set the scope of this profile: **Movies only** (`true`) or **Series only** (`false`). A Movies profile is applied only to movies from Radarr; a Series profile is applied only to series from Sonarr.

!!! warning "One profile per scope"
    A single profile cannot apply to both movies and series. Create separate profiles if you want to download trailers for both.

!!! info "Auto-detected on upgrade"
    When upgrading from a version before 0.9.5, this value is automatically detected for existing profiles based on their filters and name. Profiles where the scope cannot be determined are **disabled** and must be reviewed manually.

## Download Season Videos

{{ version_badge("add", "0.9.5") }}

!!! note ""
    Only available on **Series** profiles (`For Movies = false`).

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

When enabled, Trailarr creates one download tracking entry per season (plus one for the series overall) and searches for a trailer for each season separately. Disabled by default — existing series behaviour (one trailer per series) is unchanged until you opt in.

## Max Count

{{ version_badge("add", "0.9.5") }}

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:------------:|
| Integer | Yes      | 1       | 1 to 10      |

The maximum number of videos to download per media item for this profile. Setting it to `3`, for example, will download up to 3 videos for each matched media item. Each download is tracked as a separate status row with its own sequence number.

!!! tip
    Use this with `Stop Monitoring = false` when you want to collect multiple trailers or extras for the same media without stopping monitoring after the first download.

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

## Stop Monitoring

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

This setting indicates whether Trailarr should stop monitoring the media item after a successful download using this profile. Useful for trailer profiles where you want to download multiple trailers or extras for the same media item.

This setting will save the downloaded video id as the trailer id for the media after a successful download. So, if you are creating a profile to download additional videos (like extras or optional other language trailers), set this to `false`.

!!! example
    If you want to download 2 trailers (English and Spanish) for every media item, you would create trailer profiles like this:
    
    ```
        Profile Name: Spanish Trailer
        Stop Monitoring: false
        Priority: 100
        -------------------------------
        Profile Name: English Trailer
        Stop Monitoring: true
        Priority: 0 (or any lower number than the Spanish Trailer profile)
    ```

    This way, Trailarr will first use the `Spanish Trailer` profile to download the Spanish trailer. Since `Stop Monitoring` is set to `false`, Trailarr will continue to monitor the media item after the download. Next, it will use the `English Trailer` profile to download the English trailer. After this download, since `Stop Monitoring` is set to `true`, Trailarr will stop monitoring the media item.
