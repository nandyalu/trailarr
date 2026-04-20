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
| **Trailer detection** | Trailarr reads the extras/trailers available in Plex for each matched item, so profiles can skip downloading if a trailer already exists. |
| **Plex notifications** | After a trailer is downloaded, Trailarr can trigger a Plex library refresh so the new file appears in Plex immediately. |

!!! tip ""
    All Plex-specific behaviour (skip logic, notifications) is configured per [Trailer Profile](../profiles/index.md), not on the connection itself. A Plex connection only needs to be set up once.
