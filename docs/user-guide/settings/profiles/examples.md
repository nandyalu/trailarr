
Trailarr automatically adds 2 Profiles when you first install it:

- **Movie Trailers**
- **Series Trailers**

These profiles are created with the default settings and filters, and can be edited or deleted as needed. You can also create your own profiles from scratch or duplicate these profiles to create new ones.

Let's go over these to understand how they work and also explain the Filters.

## Example 1: Movie Trailers Profile
The **Movie Trailers** profile is used to download trailers for movies. It comes with all the default settings as defined in the [Settings](./settings/general.md) section, and the following filters:

| ID    | Filter By        | Condition         | Filter Value        |
|:-----:|:----------------:|:-----------------:|:-------------------:|
| 1     | Is Movie         | Equals            | true                |

!!! info ""
    Ignore the `ID` column, it is just for reference.

### Filter 1

This filter checks if the media item is a movie. If the media item is a movie, the filter will match and the profile will be applied.

### Result
With this filter, the **Movie Trailers** profile applies to all movies. When the `Download Missing Trailers` task runs, it downloads a trailer only for movies where this profile does not already have one — a profile that already owns a downloaded trailer never downloads again.

!!! note "No `Trailer Exists` filter anymore"
    {{ version_badge("upd", "0.11.0") }}
    Older versions used a `Trailer Exists = false` filter here to avoid re-downloads. Downloads are tracked per profile since `v0.10.0`, so the app handles this automatically and the filter was removed in `v0.11.0`.

## Example 2: Series Trailers Profile

The **Series Trailers** profile is used to download trailers for TV series. It comes with all the default settings as defined in the [Settings](./settings/general.md) section, and the following filters:

| ID    | Filter By        | Condition         | Filter Value        |
|:-----:|:----------------:|:-----------------:|:-------------------:|
| 1     | Is Movie         | Equals            | false               |

!!! info ""
    Ignore the `ID` column, it is just for reference.

One Setting that is different from the **Movie Trailers** profile is that the **Series Trailers** profile has `Folder Enabled` set to `true`. So that Series trailers are saved in a `Trailers` folder inside the Series folder.

### Filter 1

This filter checks if the media item is a series. If the media item is a series, the filter will match and the profile will be applied.

### Result
With this filter, the **Series Trailers** profile applies to all TV series. When the `Download Missing Trailers` task runs, it downloads a trailer only for series where this profile does not already have one.

## Example 3: Spanish Movie Trailers Profile

- Create a profile by clicking on the `Add New` button in the `Profiles` page.
- Name the profile `Spanish Movie Trailers`.
- Set the below `Filter`s:

    | ID    | Filter By        | Condition         | Filter Value        |
    |:-----:|:----------------:|:-----------------:|:-------------------:|
    | 1     | Is Movie         | Equals            | true                |
    | 2     | Language         | Equals            | Spanish             |

- Click `Create` to create the profile.
- Change the following `Settings`:

    - Set `Priority` to `1` which is higher than the [Movie Trailers](#example-1-movie-trailers-profile) profile, so that this profile is used first for matching movies.
    - Set `Include Words in Title` to `Español`.
    - Set `Search Query` to `{title} {year} {is_movie} Tráiler en español`.
    - Set `Always Search` to `true`.

!!! info ""
    Make sure to save the `Include Words in Title` and `Search Query` settings by clicking the `✔` (tick) icon next to the settings.

!!! tip "NOT a foolproof solution"
    This profile is not a foolproof solution to download only Spanish trailers, as it relies on:
    
    - `Language` field in Radarr/Sonarr to be set correctly. If the language is not set to Spanish, this profile will not match.
    - The `Include Words in Title` setting to match the title of the trailer. If the trailer does not have the word `Español` in its title, it will not be downloaded.
    - The `Search Query` setting to return Spanish trailers. If search results does not contain any Spanish trailers, OR if there are no Spanish trailers available, this profile will not download any trailers.
