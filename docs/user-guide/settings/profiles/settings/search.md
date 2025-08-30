
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

Enter a comma separated list of words that should be included in the title when searching for trailers. This can be useful for finding specific versions or edits of trailers.

- Words separated by `,` (comma) needs to be present in the video title. Generates an `AND` condition.
- Atleast one of the words separated by `||` needs to be present in the video title. Generates an `OR` condition.
- You can also use placeholders from [Search Query](#search-query) and they will be replaced.
- All spaces before and after an operator (`,`, `||`) are ignored.
- Two words separated by a space are considered a single search term.
- Search is case-insensitive. Meaning `German||English,Trailer` is equal to `german||english,trailer`.

Ex: `movie, german trailer || deutsh trailer` is equal to `movie,german trailer||deutsh trailer`.
This will become `(movie) AND ((german trailer) OR (deutsh trailer))` and matches the below video titles:

- `The Matrix movie GERMAN Trailer`
- `The matrix deutsh trailer movie`
- `The matrix 1999 German trailer  movie`



!!! warning "All Words Must Be Present"
    A video is considered a match only if all the words in the list are present in the title of the trailer. If any word is missing, the trailer will be skipped. For example, `official,teaser` will be matched if title is `The Matrix (1999) - Official Trailer`.

## Exclude Words in Title

| Type    | Required | Default | Valid Values                  |
|:-------:|:--------:|:-------:|:-----------------------------:|
| String  | No       | (empty) | Comma-separated list of words |

Enter a comma separated list of words to exclude from the title of the trailers. If the title of the trailer contains any of the words in the list, the trailer will be skipped. For example, `teaser,clip,featurette`.

- Atleast one of the words separated by `,` (comma) needs to be present in the video title. Generates an `OR` condition.
- All words separated by `&&` needs to be present in the video title. Generates an `AND` condition.
- You can also use placeholders from [Search Query](#search-query) and they will be replaced.
- All spaces before and after an operator (`,`, `&&`) are ignored.
- Two words separated by a space are considered a single search term.
- Search is case-insensitive. Meaning `German&&Review,Comment` is equal to `german&&review,comment`.

Ex: `comment, fan && review` is equal to `comment,fan&&review`.
This will become `(comment) OR ((fan) AND (review))` and matches the below video titles for ignoring:

- `The Matrix movie GERMAN comment`
- `The Matrix movie GERMAN fanmade trailer`
- `The matrix movie deutsh trailer - fan review`
- `The matrix 1999 German trailer  comment | review`


!!! warning "All Words Must Be Absent"
    Unlike `Include Words in Title`, if any of the words in this list are present in the title of the trailer, it will be skipped.

## Yt-dlp Extra Options

| Type    | Required | Default | Valid Values                  |
|:-------:|:--------:|:-------:|:-----------------------------:|
| String  | No       | (empty) | Any valid yt-dlp options      |

Enter any additional options you want to pass to `yt-dlp` when downloading the trailer. This can be useful for advanced users who want to customize the download process.

Please refer to the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage-and-options) for a list of all available options.

!!! warning "Use with Caution"
    This setting is for advanced users only and should be used with caution. It allows you to pass any valid `yt-dlp` options to the download command. Incorrect options can cause the download to fail.
