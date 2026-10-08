# TMDB

{{ version_badge("add", "0.13.0") }}

TMDB ([The Movie Database](https://www.themoviedb.org){:target="_blank"}) keeps a list of the videos that belong to a movie or a series, and the studios keep it up to date. With a TMDB API key, Trailarr reads that list and downloads a trailer from it, instead of searching YouTube and taking the best match.

Trailarr works without a key. Nothing changes for you until you add one.

Before a key, Trailarr had one id per media item at most, and it was always the same trailer for everyone. Radarr reports a trailer id, which it takes from TMDB, so a movie usually got a reasonable one — in English. Sonarr reports none at all, because its metadata comes from TVDB and TVDB holds no YouTube trailer ids, so every series trailer came from a YouTube search on the title and the year.

That single id is why [Always Search](profiles/settings/search.md#always-search) exists: if you want a trailer in your own language, the one id from Radarr is the wrong one, so you turn the setting on and let Trailarr search YouTube instead. A search is a guess, and it returns whatever matches the title.

With a key, Trailarr asks TMDB which trailers the item has, in the languages your profiles ask for, and downloads the one that matches. The Matrix, for example, has four English trailers, a French one and an Italian one. A curated trailer in your language replaces the guess, and a search stays as the fallback for when TMDB has none — and the log says when that happened, so you can see that Trailarr looked.

## What changes with a key

| Without a key | With a key |
|---|---|
| For a movie, Trailarr uses the one id that Radarr reports, which is usually an English trailer. | Trailarr uses the full list of trailers that TMDB curates, and keeps the id from Radarr as a fallback. |
| For a series, there is no id to use: Sonarr reports none, because TVDB has none. | A series gets the same curated list as a movie. |
| To get a trailer in another language, you turn on `Always Search` and take what a YouTube search returns. | Trailarr takes a trailer that TMDB lists in the language your profile asks for, and searches only when there is none. |
| Without an id, Trailarr searches YouTube for the title and the year. | Trailarr searches YouTube only when TMDB and the Arr have nothing. |
| A wrong result of a search is downloaded. | A trailer that the studio published is downloaded. |
| A profile can download trailers only. | {{ version_badge("add", "0.14.0") }} A profile can download teasers, clips, featurettes, behind-the-scenes videos and bloopers too, with its [Video Type](profiles/settings/general.md#video-type). These come from TMDB, or from a search when [Search YouTube](profiles/settings/search.md#search-youtube) is on. |

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

Trailarr asks TMDB which videos belong to a media item before it downloads a video for it. It keeps every video of every type, and it puts an official video before one that is not official inside each type. The videos show on the media details page under [Known videos](../library/media-details/index.md#known-videos), grouped by type.

{{ version_badge("upd", "0.14.0") }} Until `v0.14.0` Trailarr kept the trailers only. The update marks every list as stale, so the next `Refresh Video Lists` run fetches the other types. A large library takes a few days to refresh in full, at 200 items every 12 hours, and the download task refreshes an item it needs before that.

An answer from TMDB stays fresh for seven days. A curated list changes rarely, and asking about every item on every run would send thousands of requests.

!!! info "Trailarr may not take the first trailer TMDB lists"
    TMDB marks some short videos as trailers. The first trailer it lists for The Matrix, for example, is a 33-second anniversary spot, which is shorter than the `Min Duration` of a profile. Trailarr tries it, sees that it is too short, and moves to the next one in the list. This is normal, and the log line says which video it took.

!!! info "Which trailer of several"
    A profile has a [Trailer Language](profiles/settings/general.md#trailer-language). A profile that names one downloads a trailer in that language or searches YouTube — it never downloads another language instead. A profile that leaves it empty takes the first trailer in the list. Trailarr asks TMDB for every language its profiles want in a single request, so two profiles, one Italian and one English, cost one call and each gets its own trailer.

!!! info "With `Always Search` on"
    A profile with [Always Search](profiles/settings/search.md#always-search) on ignores every known video, including the TMDB list, and searches YouTube every time. If you turned it on to get a trailer in your language, a TMDB key and a `Trailer Language` do that better: turn `Always Search` off and set the language.

## Upgrade an existing library

{{ version_badge("add", "0.13.1") }}

A key changes which trailer Trailarr downloads next. It does not change the trailers that you already have. To replace those with TMDB trailers, turn on [Upgrade To TMDB Trailer](profiles/settings/general.md#upgrade-to-tmdb-trailer) in each profile that you want to upgrade.

Trailarr then replaces only the trailers that are not TMDB trailers. It keeps a trailer that TMDB already lists, and it keeps a trailer when TMDB lists none for the item. Most trailers from Radarr are TMDB trailers already, because Radarr takes its trailer id from TMDB. In a test on one real library, about one media item in four needed a new trailer.

[Delete Replaced Trailer](profiles/settings/general.md#delete-replaced-trailer) decides whether the old file stays next to the new one.

A trailer whose video Trailarr does not know stays, unless [Replace Unknown Videos](profiles/settings/general.md#replace-unknown-videos) is on. Most of these are TMDB trailers already, because Radarr takes its trailer id from TMDB, so replacing them would download a large part of the library again for nothing.

The [Download Profiles](../library/media-details/index.md#download-profiles-section) section of the media details page says what the upgrade does for each profile: a trailer that it replaces and why, a trailer that it keeps because it is a TMDB trailer or a video you chose, a trailer that it keeps because TMDB lists nothing in the language of the profile, and a trailer that it keeps because its video is unknown. Trailarr asks TMDB again every seven days about an item that TMDB listed nothing for.

To keep one trailer that the upgrade would replace, add its YouTube link on the media details page under [Add a video](../library/media-details/index.md#add-a-video). A video that you chose is never replaced, in any language.

When every TMDB trailer of an item fails to download, Trailarr keeps the current trailer and tries again later, with a longer wait after each failure. After two failed runs, the library pages show the item in a banner, so you can see the reason and fix it. See [Filtering](../library/index.md#filtering).

!!! info "A large library upgrades over a few days"
    Trailarr must know the TMDB list of an item before it can compare. The [Refresh Video Lists](../tasks/index.md#refresh-video-lists) task asks TMDB about 200 items in one run, every 12 hours. To go faster, run the task by hand from the Tasks page. The media details page shows which profiles will replace a trailer on the next run.

## A media item with no TMDB id

Trailarr asks TMDB about an item only when the item has a TMDB id. Radarr reports one for almost every movie. Sonarr reports one for most series, but not all: a series that Sonarr knows only by its TVDB id has none.

Such an item is not broken. Trailarr uses the id from Sonarr, or searches YouTube, exactly as it did before you added a key.

To give an item a TMDB id, fix the link in Sonarr:

1. Open the series in Sonarr.
2. Check that it is matched to the correct series. A series with the wrong match, or with no TMDB entry, reports no TMDB id.
3. Refresh the series in Sonarr, then run **Arr Data Refresh** in Trailarr from the [Tasks](../tasks/index.md) page.

## Trailarr and the TMDB terms

Trailarr reads the video lists of TMDB with your key, and it downloads the videos from YouTube. It does not store or publish the data of TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB.
