
## Video Type

{{ version_badge("add", "0.10.0") }}

| Type   | Required | Default | Valid Values                                                                                |
|:------:|:--------:|:-------:|:-------------------------------------------------------------------------------------------:|
| String | Yes      | trailer | trailer, teaser, clip, behind the scenes, bloopers, featurette, opening credits, other      |

Select the type of video to search for and download. Defaults to `trailer`.

How the app searches based on the selected type:

| Video Type                                                         | How the app finds the video                                                    |
|:-------------------------------------------------------------------|:-------------------------------------------------------------------------------|
| `trailer`                                                          | YouTube search using the **Search Query** template                             |
| `other`                                                            | YouTube search using the **Search Query** template (custom content via yt-dlp) |
| `teaser`, `clip`, `behind the scenes`, `bloopers`, `featurette`, `opening credits` | TMDB API lookup — requires a TMDB API Key                       |

!!! note "TMDB API Key required for specific video types"
    Searching for `teaser`, `clip`, `behind the scenes`, `bloopers`, `featurette`, and `opening credits` requires a TMDB API Key to be set in **Settings > General > Integrations**. Without it, those profiles will mark items as `Not Available` instead of downloading.

    `trailer` and `other` always use YouTube search and do **not** require a TMDB API Key.

!!! tip "Use `other` for fully custom downloads"
    Set **Video Type** to `other` and customise the **Search Query** template to download any content via yt-dlp — music videos, interviews, behind-the-scenes reels that aren't in TMDB, etc. The `{video_type}` placeholder resolves to `other` in this mode, so you can use it in your file name template to keep files organised.

!!! tip
    Use separate profiles with different video types to download, for example, both a trailer and a featurette for the same media item.

## For Movies

{{ version_badge("add", "0.10.0") }}

| Type    | Required | Default | Valid Values          |
|:-------:|:--------:|:-------:|:---------------------:|
| Boolean | Yes      | true    | true (Movies) or false (Series) |

Set the scope of this profile: **Movies only** (`true`) or **Series only** (`false`). A Movies profile is applied only to movies from Radarr; a Series profile is applied only to series from Sonarr.

!!! warning "One profile per scope"
    A single profile cannot apply to both movies and series. Create separate profiles if you want to download trailers for both.

!!! info "Auto-detected on upgrade"
    When upgrading from a version before 0.9.5, this value is automatically detected for existing profiles based on their filters and name. Profiles where the scope cannot be determined are **disabled** and must be reviewed manually.

## Download Season Videos

{{ version_badge("add", "0.10.0") }}

!!! note ""
    Only available on **Series** profiles (`For Movies = false`).

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

When enabled, Trailarr creates one download tracking entry per season (plus one for the series overall) and searches for a trailer for each season separately. Disabled by default — existing series behaviour (one trailer per series) is unchanged until you opt in.

## Max Count

{{ version_badge("add", "0.10.0") }}

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

When enabled, Trailarr will unmonitor the media item **and cancel all other pending downloads** across every profile once this profile successfully downloads a video.

**How the download loop works:** Trailarr only processes rows in `Pending` status. Once a profile's row transitions to `Downloaded`, `Skipped`, or `Not Available`, it is never re-processed. This means the loop naturally stops working on a media item once every profile row is resolved — `Stop Monitoring` is an explicit override on top of that, not a requirement for the loop to stop.

!!! warning "Stop Monitoring cancels all other profiles for that media"
    When a download succeeds and `Stop Monitoring` is `true`, Trailarr marks every other `Pending` row for that media item — across **all** profiles — as `Skipped`. This includes rows for TMDB-based video types (featurette, teaser, etc.) that may not have found a video yet.

    **If you have any TMDB-type profiles alongside a trailer profile, set `Stop Monitoring` to `false` on the trailer profile**, otherwise the featurette / teaser rows will be skipped as soon as the trailer lands, before TMDB has a chance to find those videos.

!!! tip "Use Stop Monitoring only when you want to fully stop after this profile"
    Leave `Stop Monitoring` as `false` (the default) if you want all your profiles to independently run to completion. Set it to `true` only on the *last* profile you want to run — the one where a successful download means you're done with that media item entirely.

!!! example "Multiple language trailers"
    Download a Spanish trailer first, then an English trailer, and stop after the English one:

    ```
        Profile Name: Spanish Trailer
        Stop Monitoring: false
        Priority: 100
        -------------------------------
        Profile Name: English Trailer
        Stop Monitoring: true
        Priority: 0
    ```

    Trailarr processes the higher-priority Spanish profile first. Because `Stop Monitoring` is `false`, the English profile's row remains `Pending` and is picked up next. After the English trailer downloads, `Stop Monitoring` is `true` so the media is unmonitored and any remaining pending rows are skipped.

!!! example "Trailer + featurette (TMDB)"
    Download a trailer via YouTube search and a featurette via TMDB, without either cancelling the other:

    ```
        Profile Name: Movie Trailer
        Video Type: trailer
        Stop Monitoring: false   ← must be false, or featurette row gets skipped
        Priority: 10
        -------------------------------
        Profile Name: Movie Featurette
        Video Type: featurette   ← uses TMDB; video may appear days after release
        Stop Monitoring: false
        Priority: 0
    ```

    Both profiles run independently. If TMDB has no featurette yet, that row stays `Not Available` and will not block or affect the trailer download.
