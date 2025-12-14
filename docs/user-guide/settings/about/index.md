# About Trailarr Settings

The **About** page in Trailarr provides a comprehensive overview of your application instance and key statistics. Here’s what you’ll find on this page:

## Application Information
- **Version:** Displays the current Trailarr version and notifies you if an update is available, with a link to the Docker Hub page.
- **Yt-dlp Version:** Displays the version of yt-dlp installed in Trailarr and notifies you if an update is available, with a link to the PyPI page.
- **API Key:** Trailarr API key. Clicking on this will copy the API Key to your clipboard.
- **Appdata Folder:** The path to the application’s data directory.
- **Server Started:** Shows when the server was started (with timeago formatting).
- **Timezone:** The server’s configured timezone.
- **Delete Trailers (New):** Settings related to automatic removal of trailer files.
  - **On Deleting from Connection:** When enabled, trailers will be deleted when the corresponding media is removed from the connected Radarr/Sonarr instance.
  - **Only if Media Files Deleted:** When enabled together with the previous setting, trailers will only be deleted if the media files were also removed from disk.

## Statistics
- **Movies / Series:** Total number of movies and series managed.
- **Movies Monitored / Series Monitored:** Number of monitored movies and series.
- **Trailers Downloaded / Detected:** Number of trailers downloaded and detected by Trailarr.

## Login Credentials
- **Update Login:** Securely update your web UI username and password using the dialog. You’ll need your current password to make changes.

!!! tip ""
    If you only want to update `password`, fill the `New Password` leave the `New Username` empty!

## Getting Support
- **Documentation:** Link to the official documentation.
- **Discord:** Link to join the Trailarr Discord community.
- **GitHub:** View the source code or report issues.
- **Reddit:** Join the Trailarr subreddit for discussions and help.
