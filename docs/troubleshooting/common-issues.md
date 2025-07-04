
## YouTube Cookies

If you are having issues downloading trailers due to age restrictions, bot detection, etc., you can save your YouTube cookies and set the [Yt-dlp Cookies Path](../user-guide/settings/general-settings/index.md#yt-dlp-cookies-path) to cookies.txt file containing YouTube cookies. This will allow the app to use the cookies to bypass restrictions.

YouTube rotates cookies frequently on open YouTube browser tabs as a security measure. To export cookies that will remain working with yt-dlp, you will need to export cookies in such a way that they are never rotated.

!!! note
    This is a hack to bypass YouTube restrictions and it might not always work. There is nothing Trailarr can do in those situations.

!!! warning "Do NOT use cookies with New Installations"
    If you are just setting up Trailarr, it is recommended to not use cookies initially for downloading trailers in bulk, as that might lead to your account being flagged for suspicious activity and YouTube placing a ban on your account. Instead, try downloading trailers without cookies first and then setup cookies once the bulk downloads are complete.
    
    Alternatively, you can try setting up a new YouTube account and use cookies from that new account.

### Export YouTube Cookies.txt file

The suggested way to get the cookies file is:

1. Open Firefox/Chrome browser.
2. Install a cookies exporter extension like [Chrome: Get Cookies.txt locally](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?hl=en) or [Firefox: Get Cookies.txt locally](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/) or any other cookies exporter extension.

    ??? note "Extension in Incognito/Private Mode"
        You might need to open your browser extension settings and allow the extension to work in incognito/private mode.

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
    Make sure to save the cookies file in a secure location and map the volume to the container. Set the path to the cookies file in [`Yt-dlp Cookies Path` setting](../user-guide/settings/general-settings/index.md#yt-dlp-cookies-path).

### Coookies not working

Sometimes the cookies might not work right away. You can try the following steps to troubleshoot:

1. Open Trailarr container shell and check if the cookies file is accessible.
2. Check the permissions of the cookies file. It should be readable and writable by the app.
3. Run the below command to try and download a trailer using the cookies file and watch out for any errors:

    ```bash
    yt-dlp -v --cookies /config/cookies.txt YOUTUBE_URL
    ```
    Replace `YOUTUBE_URL` with the actual video URL. If the download works, then the cookies file is working fine.

4. If the download fails, then the cookies file might be invalid or expired. You can try exporting the cookies again and retry the above steps.
5. If the download works with the above command, then restart the container and try downloading trailers again.
6. If the issue still persists, you can hop on to the [Discord server](https://discord.gg/KKPr5kQEzQ){:target="_blank"} for further help.


## Windows Docker Desktop Users
### Known Issue - File Access Slowness and Workaround
Windows users of Docker Desktop often experience slow read/write speeds when using volume mounts. This is a known limitation of file sharing between the Windows host and Docker containers.

Relevant threads discussing this issue:

- [File access in mounted volumes extremely slow](https://forums.docker.com/t/file-access-in-mounted-volumes-extremely-slow-cpu-bound/8076)
- [Performance volume mount](https://forums.docker.com/t/performance-volume-mount/27633)

Fortunately, there is a workaround we can use to fix this by using a docker volume. This has already been covered in Example 4 in [Volume Mappings](../getting-started/02-installation/docker-compose.md#volumes).

### Copying `cookies.txt` to the Docker Volume
If you need to add a `cookies.txt` file (for YouTube age verification), you can copy it directly into the container's volume. Follow these steps:

Steps to Copy `cookies.txt` to the Docker Volume

1. **Run the Container (if not already running):**
   Make sure the container is running.

2. **Copy the File to the Container's Volume:**
   Use the `docker cp` command to copy the file from your host machine to the container's `/config` directory:
   ```bash
   docker cp "C:\docker\trailarr\config\cookies.txt" trailarr:/config/cookies.txt
   ```

   - `"C:\docker\trailarr\config\cookies.txt"`: Path to the file on your host machine.
   - `trailarr:/config/cookies.txt`: Destination path in the container.

3. **Verify the File Exists:**
   Confirm the file was copied successfully by checking the `/config` directory in the container:
   ```bash
   docker exec -it trailarr ls /config
   ```
   You should see `cookies.txt` listed.

!!! notes
    - The `/config` directory inside the container is backed by the `trailarr_data` volume. Once the file is in the volume, it will persist even if you recreate the container.
    - If the file path or permissions cause issues, ensure the `cookies.txt` file on your host machine is accessible and readable.

