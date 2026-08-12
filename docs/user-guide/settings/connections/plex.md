# Plex Connection Fields

{{ version_badge("add", "0.9.0") }}

This page describes the fields available when adding or editing a **Plex** connection. For a step-by-step setup guide, see [Plex Connection](../../../getting-started/03-setup/plex-connection.md).

---

## Name

| Type   | Required | Valid Values                            |
|:------:|:--------:|:---------------------------------------:|
| String | Yes      | Any string (Min 3 characters)           |

A friendly name for this Plex connection, displayed throughout the Trailarr UI (e.g., `Plex`, `My Plex Server`).

---

## Arr Type

| Type   | Required | Valid Values          |
|:------:|:--------:|:---------------------:|
| Enum   | Yes      | `Plex`                |

Must be set to `Plex` for a Plex connection. This determines which connection flow and API Trailarr uses.

---

## Server URL

| Type   | Required | Valid Values               |
|:------:|:--------:|:--------------------------:|
| String | Yes      | Full URL to Plex server    |

The URL Trailarr uses to reach your Plex Media Server (e.g., `http://192.168.0.10:32400`).

!!! note ""
    This field is filled in automatically after you complete the OAuth sign-in and select your server. You generally do not need to edit it manually.

!!! tip "Use a local address"
    {{ version_badge("add", "0.11.0") }}
    The server list shows the URLs that Plex provides, which are often external addresses. If Plex runs on the same machine or network as Trailarr, select **Custom URL…** in the server dropdown and enter the local address (for example `http://192.168.0.10:32400`). Use the **Test** button on the same screen to check that the address is reachable before you connect.

---

## API Token

| Type   | Required | Valid Values               |
|:------:|:--------:|:--------------------------:|
| String | Yes      | Plex authentication token  |

Your Plex authentication token, used to authenticate all API requests from Trailarr to your Plex server.

!!! note ""
    This is filled in automatically during OAuth sign-in. You do not need to find or copy this manually.

---

## Monitor New Media

{{ version_badge("upd", "0.10.2") }}

| Type    | Required | Valid Values  |
|:-------:|:--------:|:-------------:|
| Boolean | Yes      | Yes or No     |

Whether media items discovered through this Plex connection should **start monitored** (a trailer will be downloaded for them). Like Arr connections, this applies only once, when a media item is first added — monitoring stays entirely under your control afterwards; syncs never change it.

!!! tip
    When setting up a Plex connection for the first time, set **Monitor New Media** to `No` until the initial library scan finishes, then switch it to `Yes` so only future additions start monitored. You can always monitor individual items by hand from the library.

!!! note "Upgrading from Monitor Types"
    Before `v0.10.2` this was a `missing` / `new` / `none` dropdown. Existing Plex connections migrate automatically: `none` becomes `No`, everything else becomes `Yes` — and your media keep their current monitor values.

---

## Library Folders

| Type   | Required | Valid Values                      |
|:------:|:--------:|:---------------------------------:|
| List   | Yes      | One or more folder path mappings  |

Maps each Plex library folder path (as Plex sees it) to the corresponding path inside Trailarr's container. This is required so Trailarr can locate media files and place downloaded trailers in the right location.

Each entry has two fields:

- **Library Folder (Plex)** — the path as reported by the Plex library scan. Read-only; populated automatically when you click **Add library folders**.
- **Path in Trailarr** — the equivalent path inside the Trailarr container. You must fill this in (use the folder browser button to navigate).

!!! warning ""
    If no library folders are configured, Trailarr cannot match or manage any media from this Plex connection.

!!! tip
    Click **Add library folders** to auto-populate entries from your Plex libraries, then fill in each **Path in Trailarr** field. Remove any libraries you do not want Trailarr to manage.

!!! info "Untracked library sections are skipped automatically"
    During each Plex sync, Trailarr compares each library section's root folder against your configured library folders. If a section's folders don't match any entry, the entire section is skipped with a single log line — no per-item noise. This is normal if you have Plex libraries (e.g. music, photos) that you haven't added path mappings for.

---

## Machine Identifier

| Type   | Required | Valid Values               |
|:------:|:--------:|:--------------------------:|
| String | Yes (internal) | Unique Plex server ID |

A unique identifier for your Plex Media Server instance, used internally by Trailarr to reliably identify the correct server.

!!! note ""
    This is filled in automatically when you select your server after OAuth sign-in. It is not editable.

---

## What a Plex Connection Does

| Feature | Description |
|---------|-------------|
| **Media linking** | Trailarr scans your Plex libraries and matches media items from Radarr/Sonarr to their Plex counterparts. |
| **Trailer detection** | The weekly [Refresh Plex Trailer Flags](../../tasks/index.md#refresh-plex-trailer-flags) task checks whether Plex has a remote trailer for each linked item and caches the result. Profiles can use this to skip downloading if Plex already has a qualifying trailer. |
| **Plex notifications** | After a trailer is downloaded, Trailarr can trigger a Plex library refresh so the new file appears in Plex immediately. |
| **Removal cleanup** {{ version_badge("add", "0.11.1") }} | When an item is no longer in your Plex library, the next sync cleans it up. A Plex-only item is deleted from Trailarr (trailer files are also deleted when [On Deleting from Connection](../general-settings/index.md#on-deleting-from-connection) is on). An item that Radarr/Sonarr still tracks only loses its Plex link (a `Plex Unlinked` event is recorded). If a library section fails to sync, the cleanup is skipped for that run so a partial sync never deletes media. |

!!! tip ""
    All Plex-specific behaviour (skip logic, notifications) is configured per [Trailer Profile](../profiles/index.md), not on the connection itself. A Plex connection only needs to be set up once.

---

## How Trailarr Resolves TV Show Folder Paths

{{ version_badge("upd", "0.11.2") }}

To match Plex shows against Radarr/Sonarr entries, Trailarr needs to know each show's root folder path. Plex does not expose this directly, so Trailarr derives it from episode files when it syncs a TV library section.

**Step 1 — Episode file scan**

Trailarr calls Plex's `/allLeaves` endpoint to collect the file path of every episode in the section. It groups those paths by show and runs `commonpath` across them to find the deepest folder that all episodes share. For example:

| Episode files | Computed common path |
|---------------|---------------------|
| `/tv/Breaking Bad (2008)/Season 1/s01e01.mkv`<br>`/tv/Breaking Bad (2008)/Season 2/s02e01.mkv` | `/tv/Breaking Bad (2008)` ✓ |
| `/tv/Arcane (2021)/Season 1/s01e01.mkv`<br>`/tv/Arcane (2021)/Season 1/s01e02.mkv` | `/tv/Arcane (2021)/Season 1` ← needs fixing |

**Step 2 — Season folder detection**

Single-season shows (or shows where Plex has only indexed one season so far) leave `commonpath` stuck inside the season subfolder. If the last component of the path matches a known season-folder pattern (`Season 1`, `S02`, `Series 3`, `Specials`, or localized equivalents like `Saison`, `Staffel`, `Temporada`, `Stagione`, …), Trailarr walks up one level to the show root. Otherwise the path is kept as-is, and the parent folder match described below acts as the safety net.

**Step 3 — Stray folder protection**

{{ version_badge("add", "0.11.2") }}

When a show has episodes in more than one folder (for example, a leftover duplicate folder from an old download or a manual import), the common path collapses to the library root. Trailarr detects this and selects the folder that contains the most episodes instead. It also logs a warning that names the show and the selected folder, so you can find and remove the stray folder in Plex.

A derived folder must always be deeper than a library root. When no safe folder can be derived — for example, all episode files sit directly in the library root — Trailarr skips the show with a warning instead of tracking it with a wrong folder. A folder at or above a library root would make one media item claim every file and trailer in the library.

### How Plex items link to media

{{ version_badge("add", "0.11.2") }}

After the folder is derived and translated through your [Library Folders](#library-folders) mappings, Trailarr matches each Plex item to media in three stages:

1. **Exact folder match** — the Plex item's folder equals a stored media folder. This is the normal case for media that Radarr/Sonarr already tracks.

2. **Parent folder match** — a stored media folder is a parent of the Plex item's folder. This covers season subfolders that step 2 above does not recognize. A stored folder at or above a library root never matches.

3. **ID match** — when the folders do not match, the item links by TMDB id (movies) or TVDB id (shows). The link is made only when exactly one media item has that id; Plex-only items from a different Plex connection and Arr items already linked to a different Plex connection are not considered.

When no stage matches, Trailarr creates a new Plex-only media item. The ID match also lets a Plex-only item follow a folder rename in Plex, so it keeps its events and download history instead of being deleted and added again.

The same rules protect the Radarr/Sonarr side: a new Arr item adopts an existing Plex-only item at the same folder, but never one whose folder is at or above a library root.

### Naming conventions that work best

Trailarr is designed to work with the default naming schemes used by **Sonarr** and **Radarr**, which are also the conventions Plex recommends:

| Folder format | Works? |
|---------------|--------|
| `Show Name (Year)` | ✓ |
| `Show Name (Year) {tvdb-ID}` | ✓ |
| `Show Name (Year) {tvdb-ID} [imdb-ID]` | ✓ |
| `Season XX` subfolders | ✓ — detected automatically |
| `Specials` / `Extras` subfolders | ✓ — detected automatically |
| Localized season folders (`Saison 1`, `Staffel 2`, …) | ✓ |
| Flat layout (all episodes directly in the show folder) | ✓ — `commonpath` already lands on the show root |

### What to check if a show is not matching

If trailers are not being linked to a specific show, check the following:

1. **Verify the folder path in Sonarr/Radarr** matches what Plex sees. The path Sonarr stores for a show must be the same path (or a parent of the path) that Plex uses for the show's files, after your path mappings are applied on both sides.

2. **Check the show's ids in Plex** — when the folders differ, Trailarr can still link the show by its TVDB id. Open the show in Plex and confirm the metadata agent found the correct match; a show without a TVDB id can only link by folder path.

3. **Check the logs for folder warnings** — a warning that names the show and mentions the library root points to a stray or duplicate folder in Plex. Remove the stray folder and refresh the Plex library.

4. **Run a manual sync** from the Tasks page after making any changes.
