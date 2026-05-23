# Download Pipeline

{{ version_badge("add", "0.10.0") }}

This page explains exactly how Trailarr finds, downloads, and tracks trailers — from the first time a media item is added to the moment a file lands on disk. Understanding this flow helps you configure profiles correctly and diagnose why a particular item is (or is not) downloading.

---

## How Trailarr Tracks Downloads

Every download attempt is tracked via a **MediaTrailerStatus** row. There is one row per *(media item, profile, season, sequence)* combination — not one row per media item. This is what makes it possible to download multiple videos for the same media item using multiple profiles or **Max Count > 1**.

### Status Values

| Status | Meaning |
|:------:|:--------|
| `Pending` | Waiting to be downloaded. The download loop will pick this up. |
| `Downloading` | Currently being processed (set at task start, cleared on finish). |
| `Downloaded` | A file has been successfully downloaded and recorded. |
| `Not Available` | TMDB was queried and no matching video exists yet. Checked again on the next weekly TMDB refresh. |
| `Failed` | All retry attempts were exhausted or the download raised an unrecoverable error. |
| `Skipped` | Another profile with **Stop Monitoring = true** already downloaded a video for this media item, so this row was bypassed. |
| `Unmonitored` | Monitoring was turned off for this media item. |

### When Rows Are Created

Rows are created in `Pending` state:

- When a new **profile is saved** — rows are created for every media item that matches the profile's filters.
- When a profile setting that affects matching (filters, scope, **Max Count**, **Download Season Videos**) is **changed** — rows are re-synchronised for all matching media.
- When media is **manually downloaded** from the UI — the selected profile's row is updated directly.

Rows are *never* deleted unless you delete the profile they belong to.

---

## The Download Loop

The **Download Missing Trailers** task (runs hourly by default) works through `Pending` rows one at a time in **profile priority order** (highest priority first). For each row it:

1. Loads the media item and its profile.
2. Checks that the media folder is accessible (creates a `FOLDER_MISSING` issue if not, and skips the media item for the rest of this run).
3. Determines the correct **video ID** using the lookup priority described below.
4. Downloads the file via yt-dlp, verifies duration and format, optionally trims silence, and moves it to the destination folder.
5. Records the download and updates the row to `Downloaded`.
6. If the profile has **Stop Monitoring = true**, marks all other `Pending` rows for that media item as `Skipped`.

If a download fails it is retried up to **Retry Count** times before the row is marked `Failed`.

!!! note "One item at a time"
    The loop processes rows one by one — it does not download multiple items in parallel. There is a progressive delay between consecutive downloads to avoid overloading yt-dlp or triggering rate limits:

    | Download No | Delay     |
    |:-----------:|:---------:|
    | 1 – 9       | 2 mins    |
    | 10 – 49     | 4 mins    |
    | 50 – 99     | 6 mins    |
    | 100 – 199   | 7 mins    |
    | 200 – 499   | 9 mins    |
    | 500+        | 10 mins   |

    Each delay also includes a random extra 0–60 seconds.

---

## Video ID Lookup Priority

This is the most important part of the pipeline. Where Trailarr looks for a video depends on the profile's **Video Type** and **TMDB Language** settings.

### `other` Type — YouTube Search Only

```
YouTube search (Search Query template)
```

The `other` type always uses a YouTube search and never consults TMDB. Use it for custom content (music videos, interviews, etc.) that is not in TMDB's video database.

---

### `trailer` Type — No TMDB Language Set

```
1. Radarr/user-set YouTube ID  (media.youtube_trailer_id)
   ↓ (if none)
2. TMDB cache on row  (row.youtube_id, populated by Refresh TMDB Videos task)
   ↓ (if none)
3. YouTube search  (Search Query template)
```

When **TMDB Language** is empty (the default), Trailarr checks for a Radarr-provided or user-set YouTube ID first. This means if Radarr already knows the trailer, it is used immediately without any TMDB or YouTube API calls.

!!! info "Where does `youtube_trailer_id` come from?"
    Radarr provides a YouTube trailer ID for most movies. Sonarr does not provide one. You can also set it manually on the Media Details page. This ID is never overwritten by TMDB-sourced IDs.

---

### `trailer` Type — TMDB Language Set (e.g. `de`, `fr`)

```
1. TMDB cache on row  (row.youtube_id, pre-fetched in the target language)
   ↓ (if none / cache miss)
2. Live TMDB lookup  (in the specified language)
   ↓ (if TMDB has no result in that language)
3. Radarr/user-set YouTube ID
   ↓ (if none)
4. YouTube search  (Search Query template)
```

Setting **TMDB Language** to a language code makes Trailarr ask TMDB for a trailer in that specific language first. This is useful when you want the German dub trailer rather than the English original, for example.

TMDB-sourced keys are **never** written back to the media item's `youtube_trailer_id` field — they are only cached on the status row. The `youtube_trailer_id` field always reflects only what Radarr provided or what you set manually.

!!! tip "TMDB Language codes"
    Use ISO 639-1 two-letter codes: `de` (German), `fr` (French), `es` (Spanish), `ja` (Japanese), etc. Leave empty to use the TMDB default (`en-US`).

---

### TMDB Types (teaser, clip, featurette, behind the scenes, bloopers, opening credits)

```
1. TMDB cache on row  (row.youtube_id, populated by Refresh TMDB Videos task)
   ↓ (if none / cache miss)
2. Live TMDB lookup  (using TMDB Language if set, otherwise en-US)
   ↓ (if TMDB has no result)
→  Mark row Not Available  (no YouTube fallback for named TMDB types)
```

Named TMDB video types are **TMDB-only** — there is no YouTube search fallback. If TMDB does not have the video, the row is set to `Not Available` and will be checked again on the next weekly **Refresh TMDB Videos** run. Once TMDB adds the video, the row is reset to `Pending` and picked up on the next download run.

!!! warning "Requires a TMDB API Key"
    TMDB-type profiles require a **TMDB API Key** in **Settings → General → Integrations**. Without it, the row is immediately set to `Not Available`.

!!! warning "Stop Monitoring can skip TMDB-type rows before TMDB has the video"
    If you have a `trailer` profile with **Stop Monitoring = true** alongside a `featurette` profile, the featurette row may be marked `Skipped` as soon as the trailer downloads — before TMDB has had a chance to add the featurette. **Set `Stop Monitoring = false` on any trailer profile that runs alongside TMDB-type profiles.**

---

## TMDB Video Cache (`row.youtube_id`)

Each MediaTrailerStatus row has a `youtube_id` field that caches the TMDB-sourced YouTube key for that row. The **Refresh TMDB Videos** task (weekly) populates this cache:

- For **all video types**: if TMDB has a matching video, its YouTube key is saved to `row.youtube_id`.
- For **TMDB types** additionally: if a key is found the row is reset to `Pending`; if no key is found the row is set to `Not Available`.
- For **trailer type**: only the key is cached — no status change (the download loop handles trailers independently via its priority flow).

The benefit: when the download task runs, it reads the pre-cached key from the row and skips the TMDB API call entirely (saving time and API quota). A live TMDB call is only made if the cached key is absent.

---

## `always_search` and Retries

### Always Search

When **Always Search** is enabled on a profile, at the start of each download attempt:

- `media.youtube_trailer_id` is cleared (in memory only — the database value is unchanged).
- `row.youtube_id` (the TMDB cache) is also cleared.

This forces Trailarr to do a fresh YouTube search every time, ignoring any cached or Radarr-provided ID.

### Retry Behaviour

When a download fails and retries remain:

- `media.youtube_trailer_id` is cleared so the next attempt sources a fresh result.
- The failed YouTube ID is added to an **exclude list** so YouTube search won't suggest the same video again.
- `row.youtube_id` (the TMDB cache) is **not forwarded** — if the cached TMDB key caused the failure, the retry will do a fresh live TMDB lookup instead.

Each retry works through the same priority flow from the top.

---

## Row Status Flow Diagram

```
                 ┌──────────┐
  profile saved  │  Pending │ ◄─────────────────────────────────────────┐
  or media added └────┬─────┘                                           │
                      │                                                  │
           download loop picks up row                    TMDB refresh finds video
                      │                                  (NOT_AVAILABLE → Pending)
                      ▼                                                  │
              ┌──────────────┐    TMDB has no video      ┌──────────────┴──────┐
              │ live lookup  │ ─────────────────────────► │  Not Available      │
              └──────┬───────┘                            └─────────────────────┘
                     │
           video found, download succeeds
                     │
                     ▼
              ┌─────────────┐
              │ Downloaded  │
              └─────────────┘

              ┌─────────────┐
              │   Failed    │  ← all retries exhausted
              └─────────────┘

              ┌─────────────┐
              │   Skipped   │  ← stop_monitoring=true on another profile that downloaded first
              └─────────────┘

              ┌─────────────┐
              │ Unmonitored │  ← media monitoring turned off
              └─────────────┘
```

---

## Worked Examples

### Example 1 — Standard trailer (Radarr movie)

Profile: `Video Type = trailer`, `TMDB Language = (empty)`.

1. Radarr provided a YouTube ID → used immediately, no API call needed.
2. File downloads, row → `Downloaded`.

---

### Example 2 — German-dubbed trailer

Profile: `Video Type = trailer`, `TMDB Language = de`.

1. TMDB refresh pre-cached a German key on the row.
2. Download loop reads `row.youtube_id` → uses it directly.
3. File downloads, row → `Downloaded`.

If TMDB has no German version: falls back to `media.youtube_trailer_id` (Radarr's English ID), then YouTube search.

---

### Example 3 — Featurette alongside trailer

Profile A: `Video Type = trailer`, `Stop Monitoring = false`, Priority = 10.  
Profile B: `Video Type = featurette`, `Stop Monitoring = false`, Priority = 0.

1. Profile A's row (trailer) is processed first (higher priority).
2. YouTube search finds a trailer → downloaded, row A → `Downloaded`.
3. Profile B's row (featurette) is still `Pending` — not skipped because `Stop Monitoring = false`.
4. TMDB refresh (weekly) checks TMDB for a featurette. If found → row B stays/resets to `Pending`; if not found → `Not Available`.
5. On the next download run: if `Pending`, downloads featurette; if `Not Available`, skips until next TMDB refresh.

---

### Example 4 — New series, no trailer yet

Profile: `Video Type = trailer`, `TMDB Language = (empty)`.

1. Media added from Sonarr — row created in `Pending`.
2. Download loop: no `youtube_trailer_id` (Sonarr doesn't provide one), no TMDB cache → YouTube search runs.
3. yt-dlp finds a result → downloads, row → `Downloaded`.

---

### Example 5 — Teaser that doesn't exist yet

Profile: `Video Type = teaser`.

1. Row created in `Pending` after profile save.
2. Download loop: no TMDB cache → live TMDB call → TMDB has no teaser yet → row → `Not Available`.
3. Next week: **Refresh TMDB Videos** runs → TMDB now has a teaser → row reset to `Pending`.
4. Next download run: live TMDB call → key found → downloads, row → `Downloaded`.
