# Next Steps & What to Expect

## Repeating for Other *Arr Instances

If you have multiple Radarr or Sonarr instances (e.g., one for 4K movies, another for HD movies, one for TV shows), simply repeat the steps in the "Connections" section for each *Arr instance you want Trailarr to manage.

Each connection will be listed in `Settings > Connections`, where you can edit or remove them later if needed.

## Initial Sync and Downloads

Once your connections are set up:

1.  **Initial Sync:** Trailarr will begin to sync media items from all your configured and enabled connections. This process involves fetching lists of your movies and series.
2.  **Trailer Scan:** It will then scan your existing library (based on your path mappings) to see which trailers you already have.
3.  **Magic Happens (Downloads):** Trailarr includes a scheduled task, "Download Missing Trailers," which typically runs every hour by default (this can often be configured in `Settings > Tasks`). This task will identify media items missing trailers (according to your profiles) and attempt to download them.

**A Note on Patience:**

Please be patient, especially during the first sync and the initial "Download Missing Trailers" task. The time these operations take can vary significantly depending on:

*   **The size of your media library:** More items mean more API calls and more data to process.
*   **The number of missing trailers:** If you have a large library with few trailers, the first download run might be extensive.
*   **Your internet connection speed.**
*   **Rate limits of trailer sources.**

You can monitor Trailarr's activity through its logs (often accessible via `Settings > System > Logs` or by inspecting Docker container logs) and see the status of tasks in `Settings > Tasks`.

Enjoy your automatically managed trailer collection with Trailarr!
