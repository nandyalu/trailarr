# Plex Connection Fields

<!-- md:version:add 0.9.0 -->

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

---

## API Token

| Type   | Required | Valid Values               |
|:------:|:--------:|:--------------------------:|
| String | Yes      | Plex authentication token  |

Your Plex authentication token, used to authenticate all API requests from Trailarr to your Plex server.

!!! note ""
    This is filled in automatically during OAuth sign-in. You do not need to find or copy this manually.

---

## Monitor Type

| Type   | Required | Valid Values                        |
|:------:|:--------:|:-----------------------------------:|
| Enum   | Yes      | `missing`, `new`, `none`            |

Controls which Plex-linked media Trailarr will download trailers for.

| Option    | Behaviour |
|-----------|-----------|
| `missing` | Downloads trailers for all Plex-linked media that does not already have a trailer. |
| `new`     | Downloads trailers only for media added to Plex **after** this connection was created. |
| `none`    | Disables trailer downloading for all media linked through this connection. |

!!! note ""
    `new` is disabled when **adding** a new connection because there is no prior state to compare against. Set it to `new` after the initial sync has completed.

!!! tip
    When setting up a Plex connection for the first time, leave Monitor Type as `none` until the initial library scan finishes, then switch to `new` so only future additions are downloaded.

!!! info ""
    `sync` is not available for Plex connections. Synced monitoring is based on Radarr/Sonarr monitored state, which does not apply to Plex.

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

!!! tip ""
    All Plex-specific behaviour (skip logic, notifications) is configured per [Trailer Profile](../profiles/index.md), not on the connection itself. A Plex connection only needs to be set up once.

---

## How Trailarr Resolves TV Show Folder Paths

To match Plex shows against Radarr/Sonarr entries, Trailarr needs to know each show's root folder path. Plex does not expose this directly, so Trailarr derives it in two steps when syncing a TV library section.

**Step 1 — Episode file scan**

Trailarr calls Plex's `/allLeaves` endpoint to collect the file path of every episode in the section. It groups those paths by show and runs `commonpath` across them to find the deepest folder that all episodes share. For example:

| Episode files | Computed common path |
|---------------|---------------------|
| `/tv/Breaking Bad (2008)/Season 1/s01e01.mkv`<br>`/tv/Breaking Bad (2008)/Season 2/s02e01.mkv` | `/tv/Breaking Bad (2008)` ✓ |
| `/tv/Arcane (2021)/Season 1/s01e01.mkv`<br>`/tv/Arcane (2021)/Season 1/s01e02.mkv` | `/tv/Arcane (2021)/Season 1` ← needs fixing |

**Step 2 — Season folder detection & title confirmation**

Single-season shows (or shows where Plex has only indexed one season so far) leave `commonpath` stuck inside the season subfolder. Trailarr then checks the last component of that path using two signals:

1. **Season folder regex** — if the last component matches a known season-folder pattern (`Season 1`, `S02`, `Series 3`, `Specials`, or localized equivalents like `Saison`, `Staffel`, `Temporada`, `Stagione`, …), Trailarr walks up one level to the show root.

2. **Fuzzy title match** — if the regex doesn't fire, Trailarr strips common decorators (`(year)`, `{tvdb-id}`, `[imdb-id]`) from the last component and compares it against the show title using fuzzy matching. A high similarity (≥ 60 %) confirms we are already at the show root. Otherwise the path is kept as-is and Trailarr falls back to a prefix-based lookup at match time.

### Naming conventions that work best

Trailarr is designed to work with the default naming schemes used by **Sonarr** and **Radarr**, which are also the conventions Plex recommends:

| Folder format | Works? |
|---------------|--------|
| `Show Name (Year)` | ✓ |
| `Show Name (Year) {tvdb-ID}` | ✓ — decorators are stripped before matching |
| `Show Name (Year) {tvdb-ID} [imdb-ID]` | ✓ |
| `Season XX` subfolders | ✓ — detected automatically |
| `Specials` / `Extras` subfolders | ✓ — detected automatically |
| Localized season folders (`Saison 1`, `Staffel 2`, …) | ✓ |
| Flat layout (all episodes directly in the show folder) | ✓ — `commonpath` already lands on the show root |

### What to check if a show is not matching

If trailers are not being linked to a specific show, check the following:

1. **Verify the folder path in Sonarr/Radarr** matches what Plex sees. The path Sonarr stores for a show must be the same path (or a parent of the path) that Plex uses for the show's files.

2. **Folder name contains the show title** — after stripping year and ID decorators, Trailarr compares the folder name against the show title. If you have renamed the folder manually to something unrelated to the show title, the fuzzy match will not fire. Use the Sonarr default naming scheme.

3. **Run a manual sync** from the Tasks page after making any folder name changes.
