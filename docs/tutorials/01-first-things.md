# First Things

This section explains a little bit about Docker volume mappings and environment variables. It also guides you on how to get the volume mappings you used to set up your Radarr and Sonarr instances, which you'll need for Trailarr.

## Docker Basics

### Environment Variables
Environment variables are used to pass configuration to your Docker containers. Trailarr uses them for various settings. You can find more details in our [Environment Variables](../getting-started/environment-variables.md) section in the 'Getting Started' guide.

### Volume Mappings
Volume mappings link a directory on your host machine to a directory inside the Docker container. This allows data to persist even if the container is stopped or removed.

For Trailarr to access your media files (to find existing trailers) and to save trailer files alongside your media (depending on your setup), it needs to know where your Radarr and Sonarr media folders are located *from Trailarr's perspective*.

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
    In this example, `/path/on/your/host/movies` on your computer is available as `/media/movies` inside the Radarr container, and `/path/on/your/host/tv` is available as `/media/tv` inside the Sonarr container. You will need these host paths (`/path/on/your/host/movies` and `/path/on/your/host/tv`) when configuring Trailarr's volumes.

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

You will use these same host paths when setting up Trailarr's volume mappings in the next step, ensuring Trailarr can see the same media files as your *Arr instances. For example, if Radarr's movies are in `/data/movies` on your host and mapped to `/media/movies` in Radarr, you'd map `/data/movies` to something like `/media/movies` or `/radarr_movies` in Trailarr. We'll cover this in the Installation section.
