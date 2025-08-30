
## Search Query

| Type   | Required | Default                               | Valid Values                            |
|:------:|:--------:|:-------------------------------------:|:---------------------------------------:|
| String | Yes      | {title} {year} {is_movie} trailer     | Any string (Max length: 150 characters) |

Enter a search query to use when searching for trailers on YouTube. 

Wrap a supported variable in `{}` like `{title}` and it will be replaced in the actual search query. Supports [Python string formatting options](https://docs.python.org/3/library/string.html#formatstrings).

You can use the following placeholders in the file name:


| Placeholder          | Description                                                                                                   |
|---------------------:|:--------------------------------------------------------------------------------------------------------------|
| clean_title          | Cleaned title of the media. Eg: 'thematrix'                                                                   |
| imdb_id              | IMDB ID of the media. Eg: 'tt0133093'                                                                         |
| is_movie             | 'movie' if the media is a movie, 'series' if the media is a series.                                           |
| language             | Language of the media in Radarr/Sonarr. Eg: 'English'                                                         |
| media_filename       | Filename of the media, Movies only, Series will empty. Eg: 'The.Matrix.1999.1080p.BluRay.x264.DTS-FGT'        |
| studio               | Studio of the media. Eg: 'Village Roadshow Pictures'                                                          |
| title                | Title of the media. Eg: 'The Matrix'                                                                          |
| title_slug           | TMDB ID for Movies and a hash seperated title for Series. Eg: '603' (movie) or 'the-big-bang-theory' (series) |
| txdb_id              | TMDB ID for Movies, TVDB ID for Series. Eg: '603'                                                             |
| year                 | Year of the media. Eg: '1999'                                                                                 |

## Minimum Duration

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:------------:|
| Integer | Yes      | 30      | 30 - 540     |

Select the minimum duration of the trailers to download. Trailers with a duration less than this value will be skipped.

## Maximum Duration

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:------------:|
| Integer | Yes      | 600     | 90 - 600     |

Select the maximum duration of the trailers to download. Trailers with a duration greater than this value will be skipped.

!!! info
    If you want to download trailers with a duration of 2 minutes to 5 minutes, set `Trailer Minimum Duration` to `120` seconds and `Trailer Maximum Duration` to `300` seconds.

!!! warning "60 Seconds Gap Required"
    There should be a gap of at least 60 seconds between `Trailer Minimum Duration` and `Trailer Maximum Duration`. For example, if `Trailer Minimum Duration` is set to `120` seconds, then `Trailer Maximum Duration` should be set to at least `180` seconds.

## Always Search

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

Enable this setting to always search YouTube for trailers. If disabled, the app will only search YouTube if it cannot find a trailer in Radarr, Sonarr doesn't provide youtube trailer ids.

## Include Words in Title

| Type    | Required | Default | Valid Values                  |
|:-------:|:--------:|:-------:|:-----------------------------:|
| String  | No       | (empty) | Comma-separated list of words |

**Purpose**: Specify words that MUST be present in trailer titles. Use `,` for AND logic, `||` for OR logic, and placeholders for dynamic values.

**How it Works**:

- Words separated by `,` (comma): All words must be present. Generates an `AND` condition.
- Words separated by `||` (double pipe): At least one of the words must be present. Generates an `OR` condition.
- Spaces are ignored: All spaces before and after an operator (`,`, `||`) are ignored. Two words separated by a space are considered a single search term.
- You can also use placeholders from [Search Query](#search-query) and they will be replaced.
- Search is case-insensitive. Meaning `German||English,Trailer` is equal to `german||english,trailer`.
- Order: placeholders are replaced first, followed by `,` processing, and then `||` are processed.

**Examples**:

- `movie, german trailer || deutsch trailer` -> `(movie) AND ((german trailer) OR (deutsch trailer))`
    -> Matches titles containing "movie" AND either "german trailer" OR "deutsch trailer".
    -> Same as `movie,german trailer||deutsch trailer`.
    -> Example matches:
        - `The Matrix (1999) - movie German Trailer`
        - `The Matrix (1999) - movie Deutsch Trailer - Official`

- `official,teaser` -> `(official) AND (teaser)`
    -> Matches titles containing "official" AND "teaser".
    -> Example matches:
        - `The Matrix (1999) - Official Teaser`
        - `The Matrix (1999) - Teaser Official`

!!! tip "All Words Must Be Present"
    If any required word is missing from the title, the trailer will be skipped.

## Exclude Words in Title

| Type    | Required | Default | Valid Values                  |
|:-------:|:--------:|:-------:|:-----------------------------:|
| String  | No       | (empty) | Comma-separated list of words |

**Purpose**: Specify words that MUST NOT be present in trailer titles. Use `,` for OR logic, `&&` for AND logic, and placeholders for dynamic values.

**How it Works**:

- Words separated by `,` (comma): At least one of the words must be present. Generates an `OR` condition.
- Words separated by `&&` (double ampersand): All words must be present. Generates an `AND` condition.
- Spaces are ignored: All spaces before and after an operator (`,`, `&&`) are ignored. Two words separated by a space are considered a single search term.
- You can also use placeholders from [Search Query](#search-query) and they will be replaced.
- Search is case-insensitive. Meaning `German&&Review,Comment` is equal to `german&&review,comment`.
- Order: placeholders are replaced first, followed by `,` processing, and then `&&` are processed.

**Examples**:

- `comment, fan && review` -> `(comment) OR ((fan) AND (review))`
    -> Matches titles containing "comment" OR both "fan" AND "review".
    -> Same as `comment,fan&&review`.
    -> Example matches (ignored for download):
        - `The Matrix (1999) - Comment`
        - `The Matrix (1999) - Fan Review`

- `teaser,clip,featurette` -> `(teaser) OR (clip) OR (featurette)`
    -> Matches titles containing "teaser" OR "clip" OR "featurette".
    -> Example matches (ignored for download):
        - `The Matrix (1999) - Teaser`
        - `The Matrix (1999) - Clip`
        - `The Matrix (1999) - Featurette`

!!! tip "All Words Must Be Absent"
    If any excluded word is present in the title, the trailer will be skipped.

## Yt-dlp Extra Options

| Type    | Required | Default | Valid Values                  |
|:-------:|:--------:|:-------:|:-----------------------------:|
| String  | No       | (empty) | Any valid yt-dlp options      |

Enter any additional options you want to pass to `yt-dlp` when downloading the trailer. This can be useful for advanced users who want to customize the download process.

Please refer to the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage-and-options) for a list of all available options.

!!! warning "Use with Caution"
    This setting is for advanced users only and should be used with caution. It allows you to pass any valid `yt-dlp` options to the download command. Incorrect options can cause the download to fail.
