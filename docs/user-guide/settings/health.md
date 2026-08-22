# Health

{{ version_badge("add", "0.11.4") }}

The **Settings > Health** page runs live checks of the pieces Trailarr depends on. Every red or yellow state names its fix and links to the matching docs page. The checks run when you open the page (cached for a day) or when you click **Run checks** — never at startup. The checks run together and each one has its own timeout, so a hung network mount delays only its own check.

## The checks

| Check | What it verifies |
|---|---|
| **FFmpeg** | The configured FFmpeg executable runs, with its version. |
| **Hardware acceleration** | Which GPUs Trailarr detected (NVIDIA / Intel / AMD) and whether each is enabled in settings. Before this page, the detection ran silently — see [Hardware Acceleration](../../getting-started/02-installation/hardware-acceleration.md). |
| **yt-dlp** | The version and update channel (stable/nightly), with a warning when a newer version is available — old versions break often when YouTube changes. |
| **Trailarr version** | Your version against the latest release. |
| **YouTube cookies** | Whether a cookies file is set up, how many youtube.com cookies it has, and whether they are expired. |
| **Connections** | A summary of the [Connection Doctor](./connections/index.md#connection-doctor) results. When no connection was checked yet, this check runs the doctor itself. |
| **Image cache** | The poster/image folder exists and is writable. |
| **Disk space** | Free space on the config volume and on every media disk. A media disk below 5 GB is a warning, because a full disk fails downloads with an error that does not mention space. Libraries split over more than one disk get one line for each. |

## YouTube download test

The **Test YouTube download** button checks that yt-dlp can read a known test video from YouTube with your current setup (including cookies, when set up). Nothing is downloaded.

The test contacts YouTube, so it never runs automatically — you confirm it first, and the result is kept for 24 hours. When it fails, the result shows the classified reason (sign-in required, rate limit, outdated yt-dlp) instead of a raw error.

## YouTube cookies

{{ version_badge("add", "0.11.4") }}

Some downloads fail because YouTube asks for a sign-in ("Sign in to confirm you're not a bot") or rate-limits your address. A cookies file from a signed-in browser session fixes this. You only need one when downloads fail this way — a fresh install works without it.

**Set up:**

1. In your browser, sign in to youtube.com.
2. Export cookies with an extension such as "Get cookies.txt LOCALLY" (Netscape format) — see [Export YouTube Cookies.txt file](../../troubleshooting/common-issues.md#export-youtube-cookiestxt-file).
3. On **Settings > Health**, upload the file or paste its content, then click **Save cookies**.
4. Click **Test them now** in the message that follows, to confirm the cookies work.

Trailarr stores the file in its config folder, readable only by the Trailarr user, and passes it to yt-dlp on every download and search. The content is write-only: no page or API response ever shows it again, and it is never written to the logs. **Remove cookies** deletes the stored file.

The cookies check on this page tells you when the file has no youtube.com cookies or when they are expired — export a fresh file when that happens.

!!! note "The old way still works"
    The `Yt-dlp Cookies Path` setting under [General Settings](./general-settings/index.md#yt-dlp-cookies-path) still works and points at any file path you manage yourself. The Health page is the recommended way — it stores the file with safe permissions and shows its status.

## Classified download errors

{{ version_badge("add", "0.11.4") }}

When a download fails with a known yt-dlp error, the attempt's recorded error now leads with a plain-language reason and the fix, instead of a raw traceback:

| YouTube says | Trailarr records |
|---|---|
| `Sign in to confirm you're not a bot` | YouTube requires a sign-in for this download. Set up a cookies file on Settings > Health. |
| `HTTP Error 403` / `429` | YouTube is rate-limiting or blocking downloads from this address. Wait a while, or set up a cookies file on Settings > Health. |
| `Requested format is not available` | No matching video format. This usually means yt-dlp has no JavaScript runtime (Deno) or is outdated. |
| `nsig extraction failed` / `Signature extraction failed` | YouTube changed its player and this yt-dlp version cannot read it. Update yt-dlp, and make sure a JavaScript runtime (Deno) is available. |
| Age-restricted video | The video is age-restricted. Set up a cookies file on Settings > Health to download it. |
| `Video unavailable` | The video is unavailable (removed, private, or region-locked). A search will pick a different video on the next run. |

The raw error line stays in brackets after the reason, for bug reports.
