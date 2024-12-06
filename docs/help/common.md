## YouTube Cookies

If you are having issues downloading trailers due to age restrictions, bot detection, etc., you can save your YouTube cookies and set the [Yt-dlp Cookies Path](../setup/settings.md#yt-dlp-cookies-path) to cookies.txt file containing YouTube cookies. This will allow the app to use the cookies to bypass restrictions.

YouTube rotates cookies frequently on open YouTube browser tabs as a security measure. To export cookies that will remain working with yt-dlp, you will need to export cookies in such a way that they are never rotated.

!!! note
    This is a hack to bypass YouTube restrictions and it might not always work. There is nothing Trailarr can do in those situations.

### Export YouTube Cookies.txt file

The suggested way to get the cookies file is:

1. Open Firefox/Chrome browser.
2. Install a cookies exporter extension like [Chrome: Get Cookies.txt locally](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?hl=en) or [Firefox: Get Cookies.txt locally](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/) or any other cookies exporter extension.
3. Open an incognito/private browsing window and login to Youtube.
4. Open a new tab and close the YouTube tab.
5. Export the cookies to a file say `cookies.txt` by setting `Export Format` to `Netscape`.
6. Then close the private browsing/incognito window so the session is never opened in the browser again.
7. Save/Copy that cookies file to Trailarr App data folder. For example, if you mapped `/var/appdata/trailarr` to `/config` in the container, save the cookies file in `/var/appdata/trailarr` folder.
8. Now open Trailarr in browser and navigate to `Settings > Trailer`. Under `Advanced` settings, set `Yt-dlp Cookies Path` to `/config/cookies.txt` (if you saved the file in `/var/appdata/trailarr` folder).
9. Any new trailers downloaded will use the cookies to bypass restrictions.

See below for more info regarding youtube downloaders and cookies:

- Yt-dlp: [Exporting YouTube cookies](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies) and [How do I pass cookies to yt-dlp?](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp).
- Youtube-dl: [How do I pass cookies to youtube-dl?](https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl)

!!! warning
    Make sure to save the cookies file in a secure location and map the volume to the container. Set the path to the cookies file in [`Yt-dlp Cookies Path` setting](../setup/settings.md#yt-dlp-cookies-path).