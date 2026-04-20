## Notify Plex

<!-- md:version:add 0.9.0 -->

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

When enabled, Trailarr will trigger a Plex library scan after successfully downloading a trailer. This causes the new trailer to appear in Plex immediately, without waiting for Plex's scheduled scan interval.

!!! note ""
    This setting has no effect if no [Plex connection](../../../../getting-started/03-setup/plex-connection.md) is configured, or if the media item has not been linked to a Plex library item.

---

## Skip if Plex Trailer

<!-- md:version:add 0.9.0 -->

| Type    | Required | Default | Valid Values  |
|:-------:|:--------:|:-------:|:-------------:|
| Boolean | Yes      | false   | true or false |

When enabled, Trailarr will skip downloading a trailer for a media item if Plex already has a qualifying remote trailer available for it.

A trailer qualifies if:

- It is sourced from the internet (local trailers added manually by the user are ignored).
- Its resolution meets or exceeds the **Skip if Plex Trailer Resolution** threshold.

!!! tip ""
    This is useful if you prefer to let Plex handle trailer playback using its own built-in trailers, and only want Trailarr to download trailers for media that Plex does not already cover.

!!! note ""
    This setting has no effect if no Plex connection is configured or if the media item has not been linked to Plex.

---

## Skip if Plex Trailer Resolution

<!-- md:version:add 0.9.0 -->

| Type    | Required | Default | Valid Values          |
|:-------:|:--------:|:-------:|:---------------------:|
| Integer | Yes      | 1080    | 480, 720, 1080, 1440, 2160 |

The minimum resolution (in pixels, vertical) that a Plex trailer must meet for the skip to apply. Only used when **Skip if Plex Trailer** is enabled.

| Value | Meaning |
|------:|---------|
| `480`  | Skip if Plex has any trailer at 480p or above |
| `720`  | Skip if Plex has a trailer at 720p or above |
| `1080` | Skip if Plex has a trailer at 1080p or above *(default)* |
| `1440` | Skip if Plex has a trailer at 1440p or above |
| `2160` | Skip if Plex has a trailer at 4K (2160p) |

!!! example
    With **Skip if Plex Trailer** enabled and **Skip if Plex Trailer Resolution** set to `720`:

    - Plex has a **1080p** trailer → Trailarr **skips** the download.
    - Plex has a **480p** trailer → Trailarr **proceeds** with the download (resolution below threshold).
    - Plex has **no** remote trailer → Trailarr **proceeds** with the download.

!!! note ""
    Locally added trailers (those with a `file://` path in Plex) are always excluded from this check, regardless of their resolution. Only trailers that Plex sourced from the internet count.
