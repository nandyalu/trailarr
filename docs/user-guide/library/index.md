# Library

The Library section in Trailarr is your central hub for browsing and managing your media collection.

![Library - Home](library-home.png)

It's comprised of three main views:

- **Home**: Media items with downloaded trailers (URL: '/home')
- **Movies**: Movies from all Radarr Connections (URL: '/movies')
- **Series**: Series from all Sonarr Connections (URL: '/series')


!!! note "Scroll to display more items"
    Library displays 50 Media items at a time until it displays them all. More items will be displayed as you reach the end.

Library views offer some features for managing media items. They are described below:

## Media Details

Clicking on any Media item will open it's details page. See [Media Details](./media-details/index.md) for more info.


## Sorting

![Library - Sorting](library-sorting.png)

Media items in the view can be sorted using the following options:

- Title
- Year
- Added
- Updated

You can select the same sort option again to switch between Ascending and Descending!


## Filtering

![Library - Filtering](library-filtering.png)


Media items in the view can be filtered using the following options:

- All: No filter applied
- Downloaded: Trailer downloaded
- Downloading: Trailer downloading
- Missing: Trailer missing (also includes monitored items)
- Monitored: Monitored for trailer download
- Unmonitored: Trailer missing (does not include monitored items)

!!! tip
    There is also an option to add a custom filter to fit your needs. These are same as `Filters` used in `Profiles` (infact they use the same mechanism underneath). For more information see [Filters](../settings/profiles/filters.md).

![Library - Filtering - Home](library-filtering-home.png)

The filters on the **Home** page are slightly different as it only contains media with downloaded items.

- All: No filter applied
- Movies: Movies only
- Series: Series only

Custom filters are also supported here!

!!! success ""
    When you make a selection for a `sort` or `filter` option, browser will remember and apply that next time.


## Trailer Tracking

Trailarr automatically tracks new trailer downloads and adds them to its database. This allows for better management and opens up possibilities for future features like downloading season-specific trailers and extras.

When a new trailer is downloaded, Trailarr extracts metadata from the file and stores it in the database. This includes information like resolution, video and audio formats, duration, and subtitles.

### Existing Trailers

The `Scan Disk for Trailers` task will scan your media folders for existing trailers and add them to the database if they are not already tracked.

For existing trailers, Trailarr will try to determine the `YouTubeId` in the following ways:

- **From Metadata**: If you have enabled the option to embed metadata in the downloaded file, Trailarr will try to extract the YouTube video URL from the file's comment field.
- **From Media Item**: If the media item has a `youtube_trailer_id` and the `downloaded_at` timestamp matches the file's creation/modification time, Trailarr will use that as the `YouTubeId`.
- **Unknown**: If the `YouTubeId` cannot be determined from the above methods, it will be set to `unknown0000`.

## Edit View

![Library - Edit Button](library-edit-button.png)

Click on the `Edit` button in the top bar to enable edit view where you can perform some batch operations.

![Library - Edit View](library-edit-view.png)

### Monitor

This will enable Monitoring of the selected Media items.

However, this will have no effect on items:

- already monitored.
- has a downloaded trailer.

### UnMonitor

This will disable Monitoring of the selected Media items. 

However, this will have no effect on items:

- already unmonitored.


### Download

This can be used to batch download trailers. Selecting this will open up a dialog asking you to choose a Profile to use for downloading.

![Library - Profile Selection Dialog](library-profile-dialog.png)

Make a selection and click 'Confirm' to start a background task to download all the trailers for selected Media items.

However, this will have no effect on items:

- with Non-Existing Media folder
- has a downloaded trailer
- media not yet downloaded (if `Wait for Media` is enabled)

### Delete

This will Delete the downloaded trailer file (if it exists).

### Cancel

Cancel the Batch Edit and go back to Normal View.

### Select All

Selects all items that are in the view based on selected filter before opening Edit View.

### Clear Selections

Clears all selections.