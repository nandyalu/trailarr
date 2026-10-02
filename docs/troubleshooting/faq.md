## Does this work with Plex, Emby, Jellyfin?
Yes, this works with Plex, Emby, and Jellyfin. Trailarr downloads trailers for Movies and Series, and saves them in their respective media folder. Plex, Emby, and Jellyfin can pick up these trailers and display them along with the Movie or Series.


## How can I watch the trailers?
You can watch the trailers in the Movie or Series details in Plex, Emby, or Jellyfin. Trailers downloaded by Trailarr are saved in the same folder as the Movie or Series, for Plex, Emby, and Jellyfin to recognize and display them along with the Movie or Series.

You can also watch the trailer in the Media details page by clicking on the trailer file (in Files section) and selecting `Play Video`.


## Can I use Trailarr without Radarr or Sonarr?
Yes — Trailarr also supports [Plex connections](../getting-started/03-setup/plex-connection.md) as a first-class media source, so you can run it against a Plex library without Radarr or Sonarr. Emby and Jellyfin are supported as well. That said, Radarr/Sonarr connections provide the richest metadata (including YouTube trailer links from TMDB for movies), so connecting them is recommended when available.


## Can I use Trailarr with multiple Radarr or Sonarr instances?
Yes, you can connect multiple Radarr and Sonarr instances to Trailarr. Trailarr will monitor Movies and Series from all connected Radarr and Sonarr instances and download trailers for them.


## Trailarr is not downloading trailers for some Movies or Series. Why?
Trailarr only downloads trailers for **monitored** media that match at least one enabled Profile. Check that the media item is monitored (toggle it from the library or Media Details — monitoring is fully under your control since `v0.10.1`), and that a Profile applies to it (the **Download Profiles** section on Media Details shows exactly which profiles match and why). New media start monitored or unmonitored based on the connection's [Monitor New Media](../user-guide/settings/connections/index.md#monitor-types) setting.

Also note that since `v0.10.0`, a download that failed previously is retried with an increasing delay — 1 day after the first failure, doubling up to at most one attempt per week. You can always trigger an immediate download from the Media Details page, which bypasses this wait.


## Trailarr downloaded an incorrect trailer for a Movie or Series. How can I fix it?
Open the media details page and look at **Known videos**. The list shows every video Trailarr can download for that item, in the order it tries them: a video you chose, then the trailers that TMDB lists, then the id that Radarr or Sonarr reports, then the result of an earlier YouTube search. Trailarr takes the first one that works — see [Known videos](../user-guide/library/media-details/index.md#known-videos).

To choose a different video, find it on YouTube, paste its link into the field above the list, and click the save button. Your video goes to the top of the list, and Trailarr never removes it. Click **Download** to get it now.

{{ version_badge("upd", "0.13.0") }} Radarr reports a YouTube trailer id, and Trailarr uses it. Sonarr has no such field, because it takes its metadata from TVDB and TVDB holds no YouTube trailer ids, so for a series Trailarr searched YouTube by the title and the year — which is where a wrong trailer usually came from. A [TMDB API key](../user-guide/settings/tmdb.md) changes that the most for series: Trailarr then takes a trailer that TMDB lists instead of searching.


!!! info
    Trailarr will not delete the trailer that was already downloaded. You have to manually click on `Delete` button to delete the trailer.

## I added a TMDB API key. How do I replace my existing trailers with TMDB trailers?
{{ version_badge("add", "0.13.1") }} Turn on [Upgrade To TMDB Trailer](../user-guide/settings/profiles/settings/general.md#upgrade-to-tmdb-trailer) in the profile. You do not have to delete your trailers, and you do not have to download your whole library again.

Trailarr replaces only the trailers that are not TMDB trailers. It keeps a trailer that TMDB already lists in the [Trailer Language](../user-guide/settings/profiles/settings/general.md#trailer-language) of the profile, it keeps a trailer when TMDB lists none for the item, and it keeps a trailer whose video it does not know unless [Replace Unknown Videos](../user-guide/settings/profiles/settings/general.md#replace-unknown-videos) is on. The [Download Missing Trailers](../user-guide/tasks/index.md#download-missing-trailers) task does the replacements on its normal runs. The media details page shows, for each profile, which trailer it replaces and why, and which it keeps and why. To keep one trailer that the upgrade would replace, paste its YouTube link on the media details page: a video that you chose is never replaced.

Set [Delete Replaced Trailer](../user-guide/settings/profiles/settings/general.md#delete-replaced-trailer) to decide if the old file stays. On a large library, the upgrade takes a few days, because Trailarr asks TMDB about 200 items in each run of [Refresh Video Lists](../user-guide/tasks/index.md#refresh-video-lists). To go faster, run that task by hand from the Tasks page. See [Upgrade an existing library](../user-guide/settings/tmdb.md#upgrade-an-existing-library).

!!! warning "Do not use a batch download for this"
    A batch `Download` from the library pages does not replace a trailer. It skips the video that is already on disk and saves a second trailer next to the first one.

## Some trailers fail to download again and again. How do I find and fix them?
{{ version_badge("add", "0.13.1") }} When a download fails on two task runs, the library pages show a banner: `N media items have a trailer download that keeps failing`. Click **Review** to see those items, or pick the **Failing Downloads** quick filter. Open an item: the [Download Profiles](../user-guide/library/media-details/index.md#download-profiles-section) section shows the reason of the last failure and, when Trailarr knows it, the fix. After you fix the cause, click **Download** on the item, or select the items and use the batch **Download**: a manual download does not wait for the next retry. An item leaves the banner when a download succeeds, when you unmonitor it, or when no profile matches it any more.

## Trailarr not downloading the specified youtube video, but downloading a different video. Why?
Trailarr uses yt-dlp to download youtube videos. Some videos have restrictions on downloading, and yt-dlp might not be able to download them. The solution is to supply a cookie file (`Yt-dlp Cookies Path`) in `Settings > General` to download restricted videos. See [Settings](../user-guide/settings/general-settings/index.md#yt-dlp-cookies-path) for more info.


## Can I download multiple trailers for a Movie or Series?
Yes — create multiple [Trailer Profiles](../user-guide/settings/profiles/index.md) that match the same media. Each matching profile downloads and keeps track of its own video (for example, an English trailer profile and a Spanish trailer profile will each download one trailer). You can also manually update the youtube trailer link and click `Download` on the Media Details page to download another video at any time — it is saved alongside the existing ones.

## Media shows "Downloading" status for a long time. What should I do?
Trailarr downloads the best available video in the selected resolution, and then use ffmpeg to convert to selected audio and video codecs. This process can take some time based on the video size and your server hardware. 

Since `v0.10.1`, *Downloading* is a live indicator of an actual in-progress download — it is not stored, so it can no longer get stuck: if the app restarts mid-download the status simply resets, and the download is retried on the next task run. If you see *Downloading* for a long time, a conversion really is running — check the (debug) logs for its progress.

The amount of time it takes to convert a 3 minute video usually takes around 1-2 minutes on latest hardware (like i3-12100 or Ryzen 5 5600X). 

If you are using a Raspberry Pi or a low powered server, it might take longer to convert the video. You can check the (debug) logs to see the progress of the conversion process.

!!! info
    YouTube trailers are usually in `vp9` video codec and `opus` audio codec, so setting these codecs in Trailarr settings will prevent conversion on most downloads. Most modern players support these codecs, so you can use these codecs in Trailarr settings to speed up the process.


## Why does Trailarr wait so long between downloads?

Trailarr deliberately sleeps between trailer downloads to avoid rate-limiting by YouTube. Downloading too many videos in quick succession can get your server's IP address — or your YouTube account if you're using a cookies file — temporarily or permanently blocked.

The pause ranges from roughly 2 to 11 minutes per download, increasing as the batch gets larger. This is expected behavior. Once the initial backlog is downloaded, subsequent runs only process newly added media so the delays become infrequent.

See the [Slow Downloads](./common-issues.md#slow-downloads-long-pauses-between-trailers) section in Common Issues for the full breakdown.