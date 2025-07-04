## Finding Your Radarr/Sonarr Volume Mappings

To correctly configure Trailarr, you need to identify the volume mappings you used when setting up your Radarr and Sonarr Docker containers or standalone apps

*   **If you used Docker Compose:** Look at your `docker-compose.yml` file for Radarr and Sonarr. Find the `volumes:` section for each service. It will look something like this:
    ```yaml
    services:
      radarr:
        # ... other settings ...
        volumes:
          - /path/on/your/host/movies:/media/movies # <-- Radarr volume mapping
          - /path/on/your/host/radarr/config:/config
        # ... other settings ...
      sonarr:
        # ... other settings ...
        volumes:
          - /path/on/your/host/tv:/media/tv # <-- Sonarr volume mapping
          - /path/on/your/host/sonarr/config:/config
        # ... other settings ...
    ```
    In this example, `/path/on/your/host/movies` on your computer is available as `/media/movies` inside the Radarr container, and `/path/on/your/host/tv` is available as `/media/tv` inside the Sonarr container.
    
    You will need these host paths (`/path/on/your/host/movies` and `/path/on/your/host/tv`) when configuring Trailarr's volumes.

*   **If you used `docker run`:** Recall the `docker run` command you used. Look for the `-v` or `--volume` flags. For example:
    ```bash
    docker run ... -v /path/on/your/host/movies:/media/movies ... radarr_image
    docker run ... -v /path/on/your/host/tv:/media/tv ... sonarr_image
    ```
    Again, note down the host paths.

*   **If you used standalone apps:** Think of your volumes as the same path on both sides of the docker volume mapping. 

    For example: if your movies are located in `/mnt/usr/media/movies/` then you need to use the volume as:

    ```bash
    /mnt/usr/media/movies/:/mnt/usr/media/movies/
    ```

    If you are on Windows, then you would use a path like `C:\Users\YourUser\Media\Movies\` and map it to a similar path inside the container, like so:

    ```bash
    C:\\Users\\YourUser\\Media\\Movies\\:/media/movies/
    ```
    Remember these as you will need these paths when configuring Trailarr's volumes.

You will use these same host paths when setting up Trailarr's volume mappings in the next step, ensuring Trailarr can see the same media files as your *Arr instances. We'll cover this in the Installation section.
