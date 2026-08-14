Filters are the conditions that determine when a profile should be applied to a media item.

Each Filter consists of 3 things:

- **Filter By**: The property of the media item to filter on.
- **Condition**: The condition to apply to the property.
- **Value**: The value to compare against.

You can add multiple filters to a profile, and all filters must match for the profile to be applied to a media item.

## Filter By

There are 4 main categories of filters you can use:

- **Boolean**
- **Integer**
- **String**
- **Date**

See below for the available filters in each category.

### Boolean Filters

{{ version_badge("upd", "0.11.3") }}

Here are the available boolean filters:

| Filter By        | Description                                                                          |
|-----------------:|:-------------------------------------------------------------------------------------|
| `Is Movie`       | `true` if the media item is a movie, `false` for series.                             |
| `Media Exists`   | `true` if the media (movie/series) is downloaded for the item.                       |
| `Monitor`        | `true` if the media item is monitored in Trailarr.                                   |
| `ARR Monitored`  | `true` if the media item is monitored in the ARR application (e.g., Radarr, Sonarr). |

`Has Downloads` is now part of the [Download Filters](#download-filters-view-filters-only) family, which is available in view filters only.

!!! note "`Trailer Exists` and `Status` filters removed in v0.11.0"
    {{ version_badge("upd", "0.11.0") }}
    Trailarr tracks downloads per profile since `v0.10.0`. A profile that already owns a downloaded video never downloads again, so profiles no longer need a filter to prevent re-downloads. Trailarr migrated existing filters automatically. View filters on `Trailer Exists` became `Has Downloads`, view filters like `Status = downloaded` became `Has Downloads = true`, and profile filters on these fields were removed. See the [v0.11.0 release notes](../../../release-notes/2026.md) for the full migration table.

### Integer Filters

Here are the available integer filters:

| Filter By        | Description                                                                       |
|-----------------:|:----------------------------------------------------------------------------------|
| `ID`             | ID of the media item in Trailarr.                                                 |
| `ARR ID`         | ID of the media item in the ARR application (e.g., Radarr, Sonarr).               |
| `Connection ID`  | ID of the connection used for the media item in Trailarr.                         |
| `Year`           | Year the media item was released.                                                 |
| `Runtime`        | Runtime of the media item in minutes.                                             |
| `Season Count`   | Number of seasons for the series. Sonarr series use the count Sonarr reports. Plex-only series count the seasons present in the Plex library (Specials excluded). Movies have `0`. |
| `TMDB ID`        | The Movie Database (TMDB) ID of the media item. Populated for movies from Radarr and for any media item where Plex or Sonarr provides a TMDB ID. `null` for Plex-only items without a TMDB entry. Eg: `603` |
| `TVDB ID`        | The TV Database (TVDB) ID of the media item. Populated for series from Sonarr and for any media item where Plex or Radarr provides a TVDB ID. `null` for Plex-only items without a TVDB entry. Eg: `71663` |

### String Filters

Here are the available string filters:

| Filter By           | Description                                                                 |
|--------------------:|:----------------------------------------------------------------------------|
| `Title`          | Title of the media. Eg: 'The Matrix'                                           |
| `Clean Title`    | Cleaned title of the media. Eg: 'thematrix'                                    |
| `Language`       | Language of the media in Radarr/Sonarr. Eg: 'English'                          |
| `Studio`         | Studio of the media. Eg: 'Village Roadshow Pictures'                           | 
| `Media Filename` | Filename of the media. Eg: 'the.matrix.1999.1080p.mkv'                         |
| `YouTube Trailer ID` | YouTube trailer ID of the media. Eg: 'dQw4w9WgXcQ'                         |
| `Folder Path`    | Folder path of the media. Eg: '/movies/the.matrix'                             |
| `IMDB ID`        | IMDB ID of the media. Eg: 'tt0133093'                                          |
| `TXDB ID`        | Legacy combined ID field — TMDB ID for movies, TVDB ID for series, stored as a string. Eg: `'603'` (movie), `'71663'` (series). Prefer `TMDB ID` or `TVDB ID` integer filters instead — they are type-safe, support proper numeric comparisons, and correctly handle Plex-only items with no external ID. |
| `Title Slug`     | Title slug of the media. Eg: 'the-matrix'                                      |

### Date Filters

Here are the available date filters:

| Filter By        | Description                                       |
|-----------------:|:--------------------------------------------------|
| `Added At`       | Date the media item was added to Trailarr.        |
| `Updated At`     | Date the media item was last updated in Trailarr. |
| `Downloaded At`  | Date when trailer was downloaded for media item.  |


### File Filters 

{{ version_badge("add", "0.6.5") }}

Here are the available file filters:

| Filter By        | Description                                           |
|-----------------:|:------------------------------------------------------|
| `Has File`      | Indicates whether the media item has specified file.   |
| `Has Folder`    | Indicates whether the media item has specified folder. |


!!! note
    File filters look for files/folders relative to the media item's root folder (anywhere in the media item's folder structure). For example, to check if a movie has a subtitle file, you would use the `Has File` filter with something like `Ends With` condition and the value as `.srt`.


### Download Filters (view filters only) {: #download-filters-view-filters-only }

{{ version_badge("add", "0.11.3") }}

Download filters read the download records of each media item. They are grouped under **Downloads** in the filter editor. Here are the available download filters:

| Filter By                       | Type    | Description                                                                 |
|--------------------------------:|:-------:|:-----------------------------------------------------------------------------|
| `Has Downloads`                 | Boolean | `true` if the media item has at least one downloaded video on disk.          |
| `Download Count`                | Integer | Number of downloaded videos on disk for the media item.                      |
| `Download Profile`              | Profile | Matches when a download is owned by the selected profile. The editor shows profile names; a profile that was deleted shows as `Deleted [id]`. |
| `Download Resolution`           | Integer | Resolution of a downloaded video. Eg: `1080`, `2160`.                        |
| `Download Added At`             | Date    | Date a downloaded video was added.                                           |
| `Download File Missing`         | Boolean | `true` if a download record exists but its file was deleted from disk.       |
| `Has Unknown Profile Download`  | Boolean | `true` if a downloaded video on disk has no owning profile.                  |

!!! info "A media item matches when ANY download matches"
    Each download filter checks every download of the media item. The media item matches when at least one download matches the condition. For example, `Download Resolution LESS THAN 1080` matches a media item that has a 720p trailer, even when it also has a 4K one. Only downloads whose files exist on disk are checked — except `Download File Missing`, which exists to find the deleted ones.

!!! warning "Not available in Trailer Profile filters"
    Download filters work in view filters only. Trailer Profiles reject them: the download engine already skips media that have a download for the profile, so a profile does not need a download filter — and a profile that filtered on its own downloads would stop matching a media item the moment its trailer downloaded. This also applies to `Has Downloads`, which profile filters accepted before `v0.11.3`. If a profile save is rejected, remove the download filter from the profile and create a view filter with it instead.


## Conditions

The conditions determine how the value is compared against the property. The available conditions depend on the type of filter:

### Boolean Conditions

| Condition        | Description                                  |
|-----------------:|:---------------------------------------------|
| `EQUALS`         | The property must equal the specified value. |

### Integer Conditions

| Condition            | Description                                                        |
|---------------------:|:-------------------------------------------------------------------|
| `EQUALS`             | The property must equal the specified value.                       |
| `NOT EQUALS`         | The property must not equal the specified value.                   |
| `GREATER THAN`       | The property must be greater than the specified value.             |
| `GREATER THAN EQUAL` | The property must be greater than or equal to the specified value. |
| `LESS THAN`          | The property must be less than the specified value.                |
| `LESS THAN EQUAL`    | The property must be less than or equal to the specified value.    |

### String Conditions

| Condition         | Description                                            |
|------------------:|:-------------------------------------------------------|
| `EQUALS`          | The property must equal the specified value.           |
| `NOT EQUALS`      | The property must not equal the specified value.       |
| `CONTAINS`        | The property must contain the specified value.         |
| `NOT CONTAINS`    | The property must not contain the specified value.     |
| `STARTS WITH`     | The property must start with the specified value.      |
| `NOT STARTS WITH` | The property must not start with the specified value.  |
| `ENDS WITH`       | The property must end with the specified value.        |
| `NOT ENDS WITH`   | The property must not end with the specified value.    |
| `IS EMPTY`        | The property must be empty.                            |
| `IS NOT EMPTY`    | The property must not be empty.                        |

### Date Conditions

| Condition         | Description                                                     |
|------------------:|:----------------------------------------------------------------|
| `EQUALS`          | The property must equal the specified date.                     |
| `NOT EQUALS`      | The property must not equal the specified date.                 |
| `IS AFTER`        | The property must be after the specified date.                  |
| `IS BEFORE`       | The property must be before the specified date.                 |
| `IN THE LAST`     | The property must be within the last specified time period.     |
| `NOT IN THE LAST` | The property must not be within the last specified time period. |


### File Conditions

{{ version_badge("add", "0.6.5") }}

| Condition         | Description                                            |
|------------------:|:-------------------------------------------------------|
| `EQUALS`          | The property must equal the specified value.           |
| `NOT EQUALS`      | The property must not equal the specified value.       |
| `CONTAINS`        | The property must contain the specified value.         |
| `NOT CONTAINS`    | The property must not contain the specified value.     |
| `STARTS WITH`     | The property must start with the specified value.      |
| `NOT STARTS WITH` | The property must not start with the specified value.  |
| `ENDS WITH`       | The property must end with the specified value.        |
| `NOT ENDS WITH`   | The property must not end with the specified value.    |


## Filter Values
The value is the value to compare against the property. The available values depend on the type of filter:

- **Boolean Values**: `true` or `false`.
- **Integer Values**: Any integer value.
- **String Values**: Any string value.
- **Date Values**: A date in the format `YYYY-MM-DD` or a number of days (e.g., `7` for the last 7 days).

## Sync-like behavior with `arr_monitored` {: #sync-like-behavior-with-arr-monitored }

{{ version_badge("add", "0.10.2") }}

Before `v0.10.2`, the connection **Monitor Type** `Sync` made Trailarr follow the monitored state from Radarr/Sonarr. Monitoring is now yours alone — syncs never change it — but Trailarr still updates the `ARR Monitored` **fact** on every sync, so you can get the same effect with a profile filter:

| Filter By       | Condition | Filter Value |
|:---------------:|:---------:|:------------:|
| `ARR Monitored` | `Equals`  | `true`       |

Add this filter to your download profiles and they will only apply to media currently monitored in your Arr apps: unmonitor a movie in Radarr and Trailarr stops downloading for it on the next sync — without ever touching your Trailarr monitor flags. Remove the filter to decouple from Arr again.