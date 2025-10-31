
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
