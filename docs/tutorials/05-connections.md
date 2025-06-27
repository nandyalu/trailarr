# Connections

Once your Profiles are set up to your liking, it's time to add your Radarr and Sonarr connections. This allows Trailarr to communicate with your *Arr instances, discover your media, and manage trailers.

Setting up a connection involves three main steps:

1.  **Basic Connection Details & Initial Test:**
    *   Navigate to `Settings > Connections`.
    *   Click on `Add New Connection`.
    *   Fill in the basic details for your *Arr instance (e.g., Radarr or Sonarr):
        *   **Name:** A friendly name for this connection (e.g., "Main Radarr", "4K Sonarr").
        *   **Type:** Select Radarr or Sonarr.
        *   **Host:** The hostname or IP address of your *Arr instance.
        *   **Port:** The port number for your *Arr instance.
        *   **API Key:** Your API key from Radarr/Sonarr (found in its `Settings > General` section).
        *   **Base URL (Optional):** If your *Arr instance is behind a reverse proxy with a base URL (e.g., `/radarr`), enter it here.
        *   **SSL:** Enable if your *Arr instance uses HTTPS.
    *   Once these details are filled in, click the `Test` button.
    *   Trailarr will attempt to connect to the *Arr API. Upon a successful connection:
        *   The Arr API version will be displayed.
        *   Trailarr will automatically fetch the root folders configured in that *Arr instance.

2.  **Path Mappings:**
    After a successful initial test, Trailarr needs to know how to access the media files managed by this *Arr instance. This is where you map the root folders reported by the *Arr API to the paths where Trailarr can find them.
    *   For each root folder retrieved from the *Arr instance, you'll see a "Path From" and a "Path To" field.
        *   **Path From:** This is the root folder path as known by your *Arr instance (e.g., `/movies` or `/tv`). This field is usually read-only.
        *   **Path To:** This is where you tell Trailarr to find the *contents* of that "Path From" folder *within Trailarr's own file system (i.e., inside its Docker container)*.
            *   **Simple Case:** If you mapped your volumes consistently when installing Trailarr (e.g., the same host directory `/data/movies` is mapped to `/movies` in Radarr and also to `/movies` in Trailarr), then the "Path To" might be the same as "Path From".
            *   **Complex Case:** If you had to use a different internal path for Trailarr due to volume mapping conflicts (e.g., `/data/movies` on host is `/movies` in Radarr, but you mapped it to `/radarr_movies` in Trailarr), then "Path To" for a "Path From" of `/movies` would be `/radarr_movies`.
    *   To help you select the correct "Path To", there is a **folder button** next to the "Path To" input field. Clicking this button will open a file browser allowing you to visually navigate the folders visible *inside the Trailarr container* and select the appropriate directory that corresponds to the "Path From" directory.
    *   **Crucially, ensure that each "Path From" is correctly mapped to its corresponding location in Trailarr's file system.**

3.  **Validate Path Mappings & Submit:**
    *   Once you have updated the "Path To" for all root folders, the `Test` button (which might now be labeled `Validate Mappings` or similar) will become enabled again.
    *   Click this button. Trailarr will now attempt to validate these path mappings by checking if it can access them.
    *   The server will return a result indicating success or failure for each mapping.
    *   If all mappings are validated successfully, you will be able to submit (Save) the connection.

You have now successfully added an *Arr connection! Trailarr will begin to sync media information from this instance.
