
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

Here are the available boolean filters:

| Filter By        | Description                                                                          |
|-----------------:|:-------------------------------------------------------------------------------------|
| `Is Movie`       | `true` if the media item is a movie, `false` for series.                             |
| `Media Exists`   | `true` if the media (movie/series) is downloaded for the item.                       |
| `Trailer Exists` | `true` if a trailer already exists for the media item.                               |
| `Monitor`        | `true` if the media item is monitored in Trailarr.                                   |
| `ARR Monitored`  | `true` if the media item is monitored in the ARR application (e.g., Radarr, Sonarr). |

### Integer Filters

Here are the available integer filters:

| Filter By        | Description                                                         |
|-----------------:|:--------------------------------------------------------------------|
| `ID`             | ID of the media item in Trailarr.                                   |
| `ARR ID`         | ID of the media item in the ARR application (e.g., Radarr, Sonarr). |
| `Connection ID`  | ID of the connection used for the media item in Trailarr.           |
| `Year`           | Year the media item was released.                                   |
| `Runtime`        | Runtime of the media item in minutes.                               |

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
| `TXDB ID`       | TMDB ID for Movies, TVDB ID for Series. Eg: '603' (movie) 'i-am-groot' (series) |
| `Title Slug`     | Title slug of the media. Eg: 'the-matrix'                                      |
| `Status`         | Status of the media. One of [downloaded, downloading, missing, monitored]      |

### Date Filters

Here are the available date filters:

| Filter By        | Description                                       |
|-----------------:|:--------------------------------------------------|
| `Added At`       | Date the media item was added to Trailarr.        |
| `Updated At`     | Date the media item was last updated in Trailarr. |
| `Downloaded At`  | Date when trailer was downloaded for media item.  |


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


## Filter Values
The value is the value to compare against the property. The available values depend on the type of filter:

- **Boolean Values**: `true` or `false`.
- **Integer Values**: Any integer value.
- **String Values**: Any string value.
- **Date Values**: A date in the format `YYYY-MM-DD` or a number of days (e.g., `7` for the last 7 days).