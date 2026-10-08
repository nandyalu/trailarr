
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

## Video Type

{{ version_badge("add", "0.14.0") }}

| Type   | Required | Default | Valid Values                                                               |
|:------:|:--------:|:-------:|:--------------------------------------------------------------------------:|
| String | Yes      | Trailer | Trailer, Teaser, Clip, Featurette, Behind the Scenes, Bloopers, Other      |

The kind of video this profile downloads. Every profile that existed before `v0.14.0` is a `Trailer` profile, and a new profile is one too.

A profile of another type takes its videos from the list that TMDB keeps for the media item. Trailarr never searches YouTube for a teaser, a clip or a featurette: a search finds trailers, and nothing in a search result says that a video is a featurette. The profile editor hides the search settings for these types and shows a note that says so.

This has three consequences for a profile that is not a `Trailer` profile:

- It needs a [TMDB API key](../../tmdb.md). Without one, no profile of another type can download anything.
- A media item needs a TMDB id. A Plex-only item without one is skipped.
- When TMDB lists no video of that type for the item, the profile waits. Trailarr asks TMDB again every seven days with the `Refresh Video Lists` task, and the [media details page](../../../library/media-details/index.md#download-profiles-section) says that the profile waits for TMDB.

Each download records its type, and a profile is satisfied only by a download of its own type. A featurette on disk never counts as the trailer of a media item, and a trailer never counts as its featurette.

The file name and the folder of a download follow its type, so Plex and Jellyfin show the video as what it is. See [File Name](file.md#file-name) and [Folder Name](file.md#folder-name) for the names that Trailarr writes.

!!! info "The type applies to the whole profile"
    One profile downloads one type. To download the trailer and the featurettes of your movies, make two profiles with the same filters: a `Trailer` profile and a `Featurette` profile. See [Example 5](../examples.md#example-5-featurettes-profile).

!!! note "Changing the type of a profile"
    When you change the type of a profile, its downloads change with it: Trailarr relabels every file that the profile downloaded to the new type. The profile stays satisfied, and nothing downloads again. The file names on disk do not change.

### Switch an extras profile {: #switch-an-extras-profile }

{{ version_badge("add", "0.14.0") }}

Before `v0.14.0`, the only way to download a featurette or a teaser was a `Trailer` profile with the word in its [Search Query](search.md#search-query), its [Include Words](search.md#include-words-in-title) or its [Folder Name](file.md#folder-name). Such a profile still works exactly as before, and the update does not change it. At the first start of `v0.14.0`, Trailarr names each such profile once in the log and suggests this setting.

To move such a profile to the new setting:

1. Open the profile and set `Video Type` to the type you want, for example `Featurette`.
2. Trailarr relabels the files that the profile downloaded, so the profile stays satisfied. Check the `Download Profiles` section of one media item to see that its file now shows the new type.
3. The search settings no longer apply. The profile now takes its videos from TMDB, in the language the profile asks for, and skips media that TMDB has no featurette for.

Keep the old setup when you want the search: a profile that searches YouTube for interviews, for example, has no type to move to, because TMDB has no interview type (TMDB lists most interviews as featurettes). A profile with `Always Search` on cannot change its type until you turn `Always Search` off.

## Priority

| Type    | Required | Default | Valid Values |
|:-------:|:--------:|:-------:|:-------------:|
| Integer | Yes      | 0       | 0 to 999     |

{{ version_badge("upd", "0.14.0") }}

The order of the profiles that match one media item. The **lowest number goes first**: a profile with priority `0` comes before a profile with priority `1`. This is what Trailarr has always done; the docs said the opposite before `v0.14.0`.

Priority does not decide whether a profile downloads. Since `v0.10.0` every matching profile downloads its own video and keeps track of it, so two matching profiles give two downloads whatever their priorities are. Priority decides the order, in four places:

- **Which profile claims a file that is already on disk.** When a scan or the startup pass finds a video that no profile owns, the first matching profile of the same [Video Type](#video-type) takes it, and the others download their own.
- **The order of the downloads in one task run.** The profile with the lowest number downloads first.
- **Which profile a new file is given at scan time**, with the same rule as the claim.
- **The order of the rows** in the `Download Profiles` section of the media details page.

!!! warning
    If two profiles have the same priority, either can go first, so give each profile its own number when the order matters to you.


## Retry Count

{{ version_badge("add", "0.6.10") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Integer | Yes      | 2       | 0 to 9        |


This setting determines how many times Trailarr should retry downloading a trailer if the previous download attempts failed. A failed download can occur due to various reasons such as network issues, YouTube restrictions, or problems with the video itself. By default, Trailarr will retry downloading a trailer 2 times before giving up. 

Setting this value to `0` will disable retries and Trailarr will only attempt to download a trailer once. 

Setting this value to a higher number will allow Trailarr to make multiple attempts to download a trailer, increasing the chances of a successful download in case of temporary issues.

!!! note "Retries vs. backoff"
    {{ version_badge("add", "0.10.0") }} Retries here happen immediately, within the same task run. If all retries fail, the download is attempted again on a later task run with an increasing delay — 1 day after the first failure, then 2 days, then 4, capped at weekly. See [Download Missing Trailers](../../../tasks/index.md#download-missing-trailers).

## Trailer Language

{{ version_badge("add", "0.13.0") }}

| Type    | Required | Default | Valid Values                     |
|:-------:|:--------:|:-------:|:--------------------------------:|
| String  | No       | empty   | empty, or an ISO 639-1 code      |

Which language of trailer this profile downloads. Leave it empty for any language, which is what every profile did before this setting existed.

{{ version_badge("upd", "0.14.0") }} The language applies to every [Video Type](#video-type) in the same way. Most featurettes and clips that TMDB lists are English or have no language, so a `Featurette` profile that asks for another language usually finds nothing and waits. Leave the language empty on a profile of another type unless you know that TMDB has videos of that type in your language.

A language here is a **filter, not a preference**. A profile that asks for `it` downloads an Italian trailer or nothing: Trailarr never downloads a German trailer instead, because a trailer in the wrong language is not what you asked for. When Trailarr knows no trailer in that language, it searches YouTube with the [Search Query](search.md#search-query) of the profile, which you write and can aim at your language.

Trailarr only knows the language of a video when something told it. TMDB records a language for each trailer it lists, and you can [add a video](../../../library/media-details/index.md#known-videos) with a language yourself. The id that Radarr reports carries no language, so a profile that asks for a language does not use it.

!!! tip "One profile per language"
    To keep an Italian trailer and an English one for the same media item, make two profiles, one with `it` and one with `en`. Each downloads its own trailer and keeps track of its own file.

!!! note "This setting needs a TMDB API key"
    The field is disabled until you add a [TMDB API key](../../tmdb.md) in `Settings > General`, and every profile takes any language until then. Only TMDB records which language a trailer is in, so without a key Trailarr cannot tell — and a language it cannot check would match nothing, making every download fall back to a YouTube search.

## Upgrade To TMDB Trailer

{{ version_badge("add", "0.13.1") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true, false   |

Replace a trailer that is not a TMDB trailer with a trailer that is. Use this to rebuild a library that you downloaded before you added a [TMDB API key](../../tmdb.md).

The [Download Missing Trailers](../../../tasks/index.md#download-missing-trailers) task does the replacement. For each media item, it compares the trailer of this profile with the trailers that TMDB lists:

- **The trailer is a TMDB trailer.** Trailarr keeps it. Any TMDB trailer in the [Trailer Language](#trailer-language) of the profile is a match, not only the first one.
- **The trailer is a video that you chose** on the media details page. Trailarr keeps it.
- **TMDB lists no trailer for the item** in the language of the profile. Trailarr keeps the current trailer, and asks TMDB again later.
- **The trailer is not a TMDB trailer.** Trailarr downloads a TMDB trailer to replace it.
- **Trailarr does not know which video the trailer is**, such as a file that it found on disk. Trailarr keeps it, unless [Replace Unknown Videos](#replace-unknown-videos) is on. {{ version_badge("upd", "0.13.1") }}

The [Download Profiles](../../../library/media-details/index.md#download-profiles-section) section of the media details page says what the upgrade does for each profile: which trailer it replaces and why, and which it keeps and why. To keep one trailer that the upgrade would replace, paste its YouTube link on the media details page: a video that you chose is never replaced.

A replacement only takes a TMDB trailer (or a video that you chose). It never takes a YouTube search result. When every TMDB trailer fails, Trailarr keeps the current trailer and tries again later, as for any failed download. A replacement does not look at [Skip If Plex Has A Trailer](plex.md), because the trailer in Plex is the one that Trailarr replaces.

!!! tip "A changed language replaces trailers"
    When you change the Trailer Language of a profile with this setting on, Trailarr replaces each trailer in the old language with a TMDB trailer in the new language, where TMDB lists one.

!!! note "This setting needs a TMDB API key, and `Always Search` off"
    Without a key, Trailarr has no TMDB list to compare with. [Always Search](search.md#always-search) never takes a trailer from the TMDB list. In both cases the setting can do nothing, so you cannot turn it on.

## Delete Replaced Trailer

{{ version_badge("add", "0.13.1") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | true    | true, false   |

Shows only when `Upgrade To TMDB Trailer` is on. When it is `true`, Trailarr deletes the old trailer after the TMDB trailer replaces it. The new trailer then takes the file name of the old one, when that is the name that the profile gives it. When it is `false`, Trailarr keeps both files, and does not replace the trailer again.

Trailarr deletes the old trailer only after the new one is in the media folder. A failed download never leaves a media item without a trailer.

## Replace Unknown Videos

{{ version_badge("add", "0.13.1") }}

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true, false   |

Shows only when `Upgrade To TMDB Trailer` is on. Trailarr does not know which video some trailers are: a file that it found on disk, or one that an old version saved before Trailarr recorded video ids. Nothing shows whether such a trailer is a TMDB trailer, so the upgrade cannot compare it with the TMDB list.

The setting shows how many trailers of the profile have an unknown video, out of all its trailers on disk, so you can see the impact before you turn it on. When this is `false`, Trailarr keeps these trailers, and the media details page says so for each one. Most of them came from the trailer id that Radarr reports, and Radarr takes that id from TMDB, so they are TMDB trailers already. Replacing them all would download a large part of a library again for nothing: in one real library, almost a third of the trailers had no known video id.

When this is `true`, Trailarr replaces these trailers too, with a TMDB trailer in the [Trailer Language](#trailer-language) of the profile. Turn it on for a profile whose trailers came from a YouTube search, such as a series profile: Sonarr reports no trailer id, so a series trailer from before the TMDB key is a search result.

## Stop Monitoring

{{ version_badge("upd", "0.10.2") }}

This option has been **removed in v0.10.2**. Downloads have been tracked per profile since `v0.10.0`, so it was no longer needed to prevent re-downloads — a profile that already owns a downloaded video never downloads again, and downloading never changes the media item's monitor state.

If you want multiple videos per media item, simply create multiple profiles — each matching profile downloads and keeps track of its own video.

!!! note "Overlapping profiles"
    If several of your profiles match the same media and you previously relied on a `Stop Monitoring` profile's download to suppress the others, each matching profile now downloads its own video. Narrow or split the profile filters if you want only one video per media item. Non-overlapping setups — like the default Movie/Series profiles — are unaffected.
