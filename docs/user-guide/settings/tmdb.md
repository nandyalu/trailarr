# TMDB

{{ version_badge("add", "0.13.0") }}

TMDB ([The Movie Database](https://www.themoviedb.org){:target="_blank"}) keeps a list of the videos that belong to a movie or a series, and the studios keep it up to date. With a TMDB API key, Trailarr reads that list and downloads a trailer from it, instead of searching YouTube and taking the best match.

Trailarr works without a key. Nothing changes for you until you add one.

## What changes with a key

| Without a key | With a key |
|---|---|
| Trailarr uses the id that Radarr or Sonarr reports. | Trailarr uses the trailers that TMDB lists, and keeps the id from Radarr or Sonarr as a fallback. |
| Without an id, Trailarr searches YouTube for the title and the year. | Trailarr searches YouTube only when TMDB and the Arr have nothing. |
| A wrong result of a search is downloaded. | A trailer that the studio published is downloaded. |

## Get a key

1. Make an account at [themoviedb.org](https://www.themoviedb.org/signup){:target="_blank"}. It is free.
2. Open [Settings > API](https://www.themoviedb.org/settings/api){:target="_blank"} in your TMDB account.
3. Ask for a key for personal use. TMDB gives you an **API Key** of 32 characters, and an **API Read Access Token**, which is much longer. Trailarr takes either one.
4. Copy the value.

## Add the key to Trailarr

1. Open `Settings > General`.
2. Paste the value into **TMDB API Key**.
3. Save the field.

Trailarr asks TMDB whether the key works before it stores it. A key that TMDB refuses is not stored, and the page tells you so. A key that Trailarr cannot check, because it cannot reach TMDB, is stored: the network is the problem, not the key.

After it is stored, the field shows only the last four characters, such as `****99eb`. That is enough to see which key is set. Leave the field as it is to keep the key.

## What Trailarr does with it

Trailarr asks TMDB which videos belong to a media item before it downloads a trailer for it. It keeps the trailers, and it puts an official trailer before one that is not official. The videos show on the media details page under [Known videos](../library/media-details/index.md#known-videos).

An answer from TMDB stays fresh for seven days. A curated list changes rarely, and asking about every item on every run would send thousands of requests.

!!! info "Trailarr may not take the first trailer TMDB lists"
    TMDB marks some short videos as trailers. The first trailer it lists for The Matrix, for example, is a 33-second anniversary spot, which is shorter than the `Min Duration` of a profile. Trailarr tries it, sees that it is too short, and moves to the next one in the list. This is normal, and the log line says which video it took.

!!! info "Which trailer of several"
    A profile has a [Trailer Language](profiles/settings/general.md#trailer-language). Trailarr prefers a trailer in that language, then one with no language, then English, then any other. It is a preference and not a filter: a trailer in another language is better than no trailer.

## A media item with no TMDB id

Trailarr asks TMDB about an item only when the item has a TMDB id. Radarr reports one for almost every movie. Sonarr reports one for most series, but not all: a series that Sonarr knows only by its TVDB id has none.

Such an item is not broken. Trailarr uses the id from Sonarr, or searches YouTube, exactly as it did before you added a key.

To give an item a TMDB id, fix the link in Sonarr:

1. Open the series in Sonarr.
2. Check that it is matched to the correct series. A series with the wrong match, or with no TMDB entry, reports no TMDB id.
3. Refresh the series in Sonarr, then run **Arr Data Refresh** in Trailarr from the [Tasks](../tasks/index.md) page.

## Trailarr and the TMDB terms

Trailarr reads the video lists of TMDB with your key, and it downloads the videos from YouTube. It does not store or publish the data of TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB.
