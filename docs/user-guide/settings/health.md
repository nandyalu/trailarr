# Health

{{ version_badge("add", "0.11.4") }}

The **Settings > Health** page runs live checks of the parts that Trailarr depends on. Each red or yellow result shows the fix and links to the matching docs page. The checks run when you open the page, and when you click **Run checks**. Trailarr keeps the results for 24 hours. The checks never run at startup. All checks run at the same time, and each check has its own timeout. A network mount that does not answer delays only its own check.

## The checks

| Check | What it verifies |
|---|---|
| **FFmpeg** | The configured FFmpeg executable runs, with its version. |
| **Hardware acceleration** | Which GPUs Trailarr detected (NVIDIA / Intel / AMD) and whether each GPU is enabled in settings. Before this page, Trailarr did not show the result of the detection — see [Hardware Acceleration](../../getting-started/02-installation/hardware-acceleration.md). |
| **yt-dlp** | The version and update channel (stable/nightly), with a warning when a newer version is available. Downloads often fail with an old version after YouTube changes its site. |
| **Trailarr version** | Your version against the latest release. |
| **YouTube cookies** | Whether a cookies file is set up, how many youtube.com cookies it has, and whether they are expired. |
| **Connections** | A summary of the [Connection Doctor](./connections/index.md#connection-doctor) results. When no connection has a report yet, this check runs the doctor. |
| **Image cache** | The poster/image folder exists and is writable. |
| **Disk space** | Free space on the config volume and on every media disk. Trailarr shows a warning when a media disk has less than 5 GB free. A full disk makes downloads fail with an error that does not mention space. A library that uses more than one disk gets one line for each disk. |

## YouTube download test

The **Test YouTube download** button checks that yt-dlp can read a known test video from YouTube. It uses your current settings, and your cookies file when you have one. Trailarr does not download the video.

The test contacts YouTube, so it never runs automatically. You must confirm it first. Trailarr keeps the result for 24 hours. When the test fails, the result shows the reason in plain language (sign-in required, rate limit, outdated yt-dlp) instead of a raw error.

## YouTube cookies

{{ version_badge("add", "0.11.4") }}

Some downloads fail because YouTube asks for a sign-in ("Sign in to confirm you're not a bot") or rate-limits your address. A cookies file from a signed-in browser session fixes this. You only need one when downloads fail this way — a fresh install works without it.

**Set up:**

1. In your browser, sign in to youtube.com.
2. Export cookies with an extension such as "Get cookies.txt LOCALLY" (Netscape format) — see [Export YouTube Cookies.txt file](../../troubleshooting/common-issues.md#export-youtube-cookiestxt-file).
3. On **Settings > Health**, upload the file or paste its content, then click **Save cookies**.
4. Click **Test them now** in the message that follows, to confirm the cookies work.

Trailarr stores the file in its config folder. Only the Trailarr user can read the file. Trailarr sends the file to yt-dlp for every download and every search. After you save the cookies, no page or API response shows the content again, and Trailarr never writes it to the logs. **Remove cookies** deletes the stored file.

The cookies check on this page tells you when the file has no youtube.com cookies, and when the cookies are expired. Export a new file when that happens.

!!! note "The old way still works"
    The `Yt-dlp Cookies Path` setting under [General Settings](./general-settings/index.md#yt-dlp-cookies-path) still works and points at any file path you manage yourself. The Health page is the recommended way — it stores the file with safe permissions and shows its status.

## Classified download errors

{{ version_badge("add", "0.11.4") }}

When a download fails with a known yt-dlp error, Trailarr records the reason and the fix in plain language first, and the raw error after it:

| YouTube says | Trailarr records |
|---|---|
| `Sign in to confirm you're not a bot` | YouTube requires a sign-in for this download. Set up a cookies file on Settings > Health. |
| `HTTP Error 403` / `429` | YouTube is rate-limiting or blocking downloads from this address. Wait a while, or set up a cookies file on Settings > Health. |
| `Requested format is not available` | No matching video format. This usually means yt-dlp has no JavaScript runtime (Deno) or is outdated. |
| `nsig extraction failed` / `Signature extraction failed` | YouTube changed its player and this yt-dlp version cannot read it. Update yt-dlp, and make sure a JavaScript runtime (Deno) is available. |
| Age-restricted video | The video is age-restricted. Set up a cookies file on Settings > Health to download it. |
| `Video unavailable` | The video is unavailable (removed, private, or region-locked). A search will pick a different video on the next run. |

The raw error line stays in brackets after the reason, for bug reports.
