
## Search YouTube

{{ version_badge("add", "0.14.0") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | true    | true or false |

Search YouTube when no known video suits this profile. This is what every profile did before this setting existed: the known videos first (the videos that TMDB lists, the id from Radarr or Sonarr, and videos you added), then a search with the [Search Query](#search-query) when none of them suits the profile.

Turn it off, and the profile takes known videos only. Turning it off also turns `Always Search` off, because `Always Search` needs the search. When none suits it, the profile waits: it does not search, does not fail, and does not back off. Trailarr asks TMDB again every seven days with the `Refresh Video Lists` task, and the [Download Profiles](../../../library/media-details/index.md#download-profiles-section) section of the media details page says that the profile waits for TMDB. This is the setting for a profile that is optional, such as a second trailer in a language that TMDB lists for some titles only.

The profile editor hides `Search Query`, `Always Search`, `Include Words in Title`, `Exclude Words in Title` and `Allowed Uploader IDs` while the search is off. `Minimum Duration`, `Maximum Duration` and `Yt-dlp Extra Options` apply either way.

!!! note "Off by default for the other video types"
    When you set the [Video Type](general.md#video-type) of a profile to something other than `Trailer`, Trailarr turns `Search YouTube` off, because a search finds trailers and nothing in a result says that a video is a featurette. Turn it on again when you want the search, for example for interviews, which TMDB has no type for: aim the `Search Query` and the `Include Words` at the videos you want, and the downloads take the type of the profile. The editor shows a note on such a profile.

!!! tip "An optional trailer in a second language"
    To keep an English trailer for every movie and a Telugu one where TMDB has it, make two profiles with the same filters: `English Trailers` with the [Trailer Language](general.md#trailer-language) `en`, and `Telugu Trailers` with the language `te` and `Search YouTube` off. The Telugu profile downloads when TMDB lists a Telugu trailer and waits otherwise, without failed downloads in the log.

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
| tmdb_id              | TMDB (The Movie Database) ID of the media item. Eg: `603`. `None` for Plex-only items without a TMDB entry.   |
| tvdb_id              | TVDB (The TV Database) ID of the media item. Eg: `71663`. `None` for Plex-only items without a TVDB entry.    |
| txdb_id              | Legacy combined ID — TMDB ID for movies, TVDB ID for series, as a string. Eg: `'603'`. Prefer `tmdb_id` or `tvdb_id`. |
| year                 | Year of the media. Eg: '1999'                                                                                 |

## Minimum Duration

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:------------:|
| Integer | Yes      | 60      | 30 - 1140    |

Select the minimum duration of the trailers to download. Trailers with a duration less than this value will be skipped.

## Maximum Duration

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:------------:|
| Integer | Yes      | 600     | 90 - 1200    |

Select the maximum duration of the trailers to download. Trailers with a duration greater than this value will be skipped.

{{ version_badge("upd", "0.14.0") }} The largest value is `1200` seconds (20 minutes). It was `600` before `v0.14.0`. Bonus features such as featurettes and behind-the-scenes videos often run longer than 10 minutes, so a profile for them can raise this. The default stays `600`, and no existing profile changes. The limit also applies to a video that TMDB lists: Trailarr checks the duration after the download and removes a video that is too long, then tries the next one in the list.

!!! info
    If you want to download trailers with a duration of 2 minutes to 5 minutes, set `Trailer Minimum Duration` to `120` seconds and `Trailer Maximum Duration` to `300` seconds.

!!! warning "60 Seconds Gap Required"
    There should be a gap of at least 60 seconds between `Trailer Minimum Duration` and `Trailer Maximum Duration`. For example, if `Trailer Minimum Duration` is set to `120` seconds, then `Trailer Maximum Duration` should be set to at least `180` seconds.

## Always Search

{{ version_badge("upd", "0.14.0") }}

`Always Search` needs [Search YouTube](#search-youtube) on. It is a mode of the search: search every time, instead of only when no known video suits the profile. Trailarr refuses `Always Search` on a profile with the search off.

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

Enable this setting to always search YouTube for trailers. If disabled, the app will only search YouTube if it cannot find a trailer in Radarr; Sonarr doesn't provide youtube trailer ids.

Most people turn this on to get a trailer that Radarr does not report — a trailer in their own language, usually, because the id Radarr reports is one trailer and it is usually English.

{{ version_badge("upd", "0.13.0") }} From `v0.13.0` the setting ignores **every** known video for the media item — the id from Radarr, a result an earlier search stored, the trailers TMDB lists, and a video you added by hand. Trailarr searches YouTube every time, which is what the setting says.

!!! tip "You may not need it any more"
    Most people turn this on to get a trailer that Radarr does not report — a trailer in their own language, usually, because the id Radarr reports is one trailer and it is usually English. With a [TMDB API key](../../tmdb.md) and a [Trailer Language](general.md#trailer-language), Trailarr downloads a curated trailer in that language instead of guessing from a search, and searches only when TMDB has none. That is the better setup for a language: turn `Always Search` off, and set the language.

    Keep `Always Search` on when you want a search regardless — for example when your [Search Query](#search-query) finds something the curated lists do not have.

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
    - Matches titles containing "movie" AND either "german trailer" OR "deutsch trailer".
    - Same as `movie,german trailer||deutsch trailer`.
    - Example matches:
        - `The Matrix (1999) - movie German Trailer`
        - `The Matrix (1999) - movie Deutsch Trailer - Official`

- `official,teaser` -> `(official) AND (teaser)`
    - Matches titles containing "official" AND "teaser".
    - Example matches:
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
    - Matches titles containing "comment" OR both "fan" AND "review".
    - Same as `comment,fan&&review`.
    - Example matches (ignored for download):
        - `The Matrix (1999) - Comment`
        - `The Matrix (1999) - Fan Review`

- `teaser,clip,featurette` -> `(teaser) OR (clip) OR (featurette)`
    - Matches titles containing "teaser" OR "clip" OR "featurette".
    - Example matches (ignored for download):
        - `The Matrix (1999) - Teaser`
        - `The Matrix (1999) - Clip`
        - `The Matrix (1999) - Featurette`

!!! tip "All Words Must Be Absent"
    If any excluded word is present in the title, the trailer will be skipped.

## Allowed Uploader IDs

| Type    | Required | Default | Valid Values                                   |
|:-------:|:--------:|:-------:|:----------------------------------------------:|
| String  | No       | (empty) | Comma-separated list of uploader handles or channel IDs |

**Purpose**: Restrict trailer downloads to specific YouTube channels. When set, a video is only downloaded if its uploader matches one of the entries in the list.

**How it Works**:

- Leave empty to allow videos from any channel (default behaviour).
- Each entry is matched against the video's **uploader handle** (e.g. `@WarnerBrosPictures`) or **channel ID** (e.g. `UCbmNph6atAoGfqLoCL_duAg`). Either format works.
- Entries are separated by `,` (comma); at least one must match.
- Matching is exact (not a substring search), so `@Warner` will not match `@WarnerBrosPictures`.
- The field takes up to 2000 characters, which is about 75 channel IDs. {{ version_badge("upd", "0.13.1") }}

**Examples**:

- `@WarnerBrosPictures` — only download trailers uploaded by the Warner Bros. Pictures channel.
- `@UniversalPictures, @ParamountPictures` — accept trailers from either Universal or Paramount.
- `UCbmNph6atAoGfqLoCL_duAg` — match by channel ID instead of handle.

!!! tip "Finding a Channel's Uploader ID"
    Open the YouTube channel page and copy the `@handle` from the URL or page header. For the channel ID, check the channel's **About** page or use a tool like [YouTube Channel ID Finder](https://commentpicker.com/youtube-channel-id.php).

!!! note
    This filter only applies to YouTube search results. A video that you add to the [Known videos](../../../library/media-details/index.md#known-videos) of a media item bypasses all search filters including this one.

## Automatic Exclusions

{{ version_badge("upd", "0.10.1") }}

In addition to the filters you configure above, some videos are always excluded from YouTube search results regardless of profile settings:

- **Livestreams and premieres** — live or upcoming videos are never selected as trailers, since they have no bounded duration and would keep downloading until the app's 15-minute timeout kills them, leaving huge partial files behind.
- **Videos with unknown duration** — a real trailer always has a known, bounded duration, so videos where YouTube reports no duration are skipped.
- **YouTube Shorts** — vertical videos are skipped.
- **Reviews** — videos with "review" in the title are skipped.

As a second layer of protection, the download command itself also refuses live and upcoming content — this covers the ids that Radarr reports and the videos that you add by hand, which bypass search filters.

If a download fails or times out for any reason, its partially downloaded files are deleted immediately, and any leftover temporary files from previous runs are cleaned up automatically at every app startup.

## Yt-dlp Extra Options

| Type    | Required | Default | Valid Values                  |
|:-------:|:--------:|:-------:|:-----------------------------:|
| String  | No       | (empty) | Any valid yt-dlp options      |

Enter any additional options you want to pass to `yt-dlp` when downloading the trailer. This can be useful for advanced users who want to customize the download process.

Please refer to the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage-and-options) for a list of all available options.

{{ version_badge("upd", "0.11.1") }}

Extra options are added after the options that Trailarr sets, and `yt-dlp` uses the last value of a repeated option. If you pass an option that Trailarr also sets (for example `-f` / `--format`), your value wins, and Trailarr writes a warning to the logs.

!!! warning "Use with Caution"
    This setting is for advanced users only and should be used with caution. It allows you to pass any valid `yt-dlp` options to the download command. Incorrect options can cause the download to fail.

!!! warning "Custom `-f` removes Trailarr's fallbacks"
    A custom `-f` replaces Trailarr's format selection, which includes fallback formats and a final `best` fallback. A strict format with no fallback (for example `-f "bestvideo[vcodec=h265]+bestaudio"`) fails with `Requested format is not available` — YouTube does not provide `h265` streams. Set the resolution and codecs in the profile instead; Trailarr downloads the best available format and converts it with `ffmpeg`.
