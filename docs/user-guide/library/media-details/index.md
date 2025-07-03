# Media Details

🚧 Under Construction... 🚧

Media Details of an item will be opened in Trailarr UI under URL '/media/{id}' where `{id}` is the media ID in Trailarr.

![Library - Media Details](library-media-details.png)

Media Details view offers some features for managing media items. They are described below:

## Monitor / UnMonitor

<video autoplay loop src="./monitor-toggle.mp4" title="Media - Monitor Toggle"></video>

If a trailer hasn't been downloaded for Media, it can be either Monitored or UnMonitored by clicking the icon before the Media Title.

## Status - Additional Details

<video autoplay loop src="./media-status-additional-details.mp4" title="Media - Status - Additional Details"></video>

Additional Media Status details can be viewed by hovering (click on it in Mobile) on `Status` field.

!!! tip "Season Count for TV Show"
    This will also show a `Season Count` of the selected Media if it's a TV Show. This is coming from `Sonarr` and `Trailarr` can only read it, cannot update it!

## YouTube Trailer ID

![Media - YouTube Trailer ID](media-youtube-trailer-id.png)

This is the YouTube video ID present in Trailarr for this Media item, and can be updated here!

This usually comes from `Radarr` for Movies, however `Sonarr` does not contain any such value so this will initially be empty for `TV Shows`.

### Save YouTube ID

![Media - Save YouTube Trailer ID](media-save-youtube-trailer-id.png)

A save button will appear if `YouTube Trailer ID` value has changed, prompting you to save.

!!! note ""
    Save will only save the `YouTube Trailer ID` in Trailarr, does not download trailer automatically!

### Search YouTube ID

![Media - Search YouTube Trailer ID](media-search-youtube-trailer-id.png)

A search button will appear if `YouTube Trailer ID` is not available for the `Media` in Trailarr.

This can be used to let Trailarr search for a trailer for the `Media` by selecting a `Profile`.

## Action Buttons

There are 3 actions buttons that can appear depending on the selected Media

### Watch 

- Appears when the selected Media has a YouTube Trailer ID set.
- Will open the video in YouTube in a new tab when clicked.

### Download

- Appears when a trailer is not downloaded for the selected Media OR when a new video ID/URL is added in the `YouTube Trailer ID` field.
- Clicking on this will open a dialog asking you to select a Profile to use for download.
- This will schedule a task for Trailarr to download a trailer for this Media, uses `YouTube Trailer ID` if provided/existing.

### Delete

- Appears when the selected Media has a downloaded trailer.
- Deletes the trailer file.
- Asks for a confirmation before Deleting.

!!! warning
    This will Delete the trailer file on disk! Cannot be reversed!

## Files Section

The files and folders available in the media folder will be displayed here, starting with the Media folder itself!

Click on a folder to reveal it's files.

!!! tip ""
    If you don't see your actual Media files here, that means you need to update either your [Volume Mappings](../../../getting-started/02-installation/docker-compose.md#media-folders) or [Path Mappings](../../../getting-started/03-setup/connections.md#2-path-mappings).

Clicking on a file will open a dialog with some actions available that can be performed on the file:

### Play Video

- Video files only!

Plays the selected video in a dialog. Click outside the dialog to close video!

### Video Info

- Video files only!

Reads and displays the details of the video file such as file, video, audio and subtitle formats along with language and some other relevant information.

### View Text

- Text and some subtitle files only!

Displays the content of the text file!

### Rename

Renames the selected file with the given file name!

### Delete

Deletes the selected file upon confirmation.

!!! warning
    This will Delete the trailer file on disk! Cannot be reversed!

