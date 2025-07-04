# Next Steps & What to Expect

## Initial Sync and Downloads

Once your connections are set up:

1.  **Initial Sync:** Trailarr will begin to sync media items from all your configured and enabled connections. This process involves fetching lists of your movies and series.
2.  **Trailer Scan:** It will then scan your existing library (based on your path mappings) to see which trailers you already have.
3.  **Magic Happens (Downloads):** Trailarr includes a scheduled task, "Download Missing Trailers," which typically runs every hour by default (this can often be configured in `Settings > Tasks`). This task will identify media items missing trailers (according to your profiles) and attempt to download them.


## How does Trailarr work

- Trailarr gets all the Movies and Series from the Radarr and Sonarr connections
- Scans the media folders to find any existing trailers. Trailarr detects a file as a trailer if it meets these conditions:
    - File should be one of (`avi`, `mkv`, `mp4`, `webm`).
    - It should have the word `trailer` in it, episode files (with SXXEXX) are ignored even if they have the word `trailer` in them.
    - It should either be in the media folder itself, OR in a subfolder named `trailer`/`trailers` (not case-sensitive!).
- Runs some tasks every `60 minutes` (configurable in Settings) to refresh the media from Arrs, and `Download Missing Trailers` based on `Profiles`.


## A Note on Patience

Please be patient, especially during the first sync and the initial "Download Missing Trailers" task. The time these operations take can vary significantly depending on:

*   **The size of your media library:** More items mean more API calls and more data to process.
*   **The number of missing trailers:** If you have a large library with few trailers, the first download run might be extensive.

    !!! warning "Do NOT use 'cookies' for large downloads"
        If you have added a `cookies` file in `Settings > General` during [Setup](./03-setup/index.md), remove them until the initial downloads are completed!

        Some trailers might fail to download because they are Age-Restricted, don't worry, you can download them later!

        You can set them once those initial downloads are complete!

*   **Your internet connection speed.**
*   **Rate limits of trailer sources.**

You can monitor Trailarr's activity through its logs and/or see the status of tasks in `Settings > Tasks`.

Enjoy your automatically managed trailer collection with Trailarr! 🥳🎉
