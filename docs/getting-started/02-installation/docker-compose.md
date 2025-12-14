Before you begin, make sure you have reviewed the [First Things](../01-first-things/index.md) section to understand environment variables and how to find your existing Radarr/Sonarr volume mappings.

Create a `docker-compose.yml` file with the following content. Adjust the volumes and environment variables to match your setup.

```yaml
services:
  trailarr:
    image: nandyalu/trailarr:latest
    container_name: trailarr
    environment:
      - TZ=America/New_York # Change to your timezone
      # Add any other environment variables as needed.
    volumes:
      - /path/to/your/trailarr/config:/config # For Trailarr's database and logs
      # Map your Radarr media folder(s)
      - /path/on/your/host/movies:/media/movies # Example: if Radarr uses /media/movies internally
      # Map your Sonarr media folder(s)
      - /path/on/your/host/tv:/media/tv # Example: if Sonarr uses /media/tv internally
      # Add more volume mappings if you have multiple Radarr/Sonarr instances
      # or if your media is split across different locations.
      # The path on the right (e.g., /media/movies, /media/tv) is how Trailarr will see these folders.
      # The path on the left is the actual path on your Docker host system.
    ports:
      - "7889:7889" # Or choose a different host port if 7889 is taken, leave the right side as is
    restart: unless-stopped
    # Optional: Add labels, network, and other configuration as needed
```

## Explanation of options

### General Docker Compose Options
This section is for those who are new to Docker or Docker Compose. If you are already familiar with Docker Compose, you can skip this section and go to the [`volumes` section](#volumes) below.

If you are familiar with Docker containers and/or have been using them, skip to `volumes` section and look at the examples for configuring them.

Let's go over some of the things we used here:

```yaml hl_lines="3 4"
services:
  trailarr:
    image: nandyalu/trailarr:latest
    container_name: trailarr
    # Other options here
```
`image`: Specifies the Trailarr Docker image. Using `latest` to make updating to newer versions easier. Change to a specific version if needed.

`container_name`: A friendly name for your container.

```yaml hl_lines="5 6 8-10"
services:
  trailarr:
    image: nandyalu/trailarr:latest
    container_name: trailarr
    environment:
      - TZ=America/New_York # Change to your timezone
    # Other options here
    ports:
      - 7889:7889
    restart: unless-started
```
`environment`: Set your timezone here!
  For a list of valid timezones, see [tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

`ports`: Trailarr uses port `7889` internally, we need to tell Docker to make it available to our system so that we can view Trailarr UI.
  We can use the same port `7889` or change it to a different port if it's used by some other program or container.

  To use a differnt port, change the LEFT side to your desired port!
  ```yaml
  ports:
    - 8115:7889 # <-- Changed outside port to `8115` if needed
  ```

`restart: unless-stopped`: Ensures the container restarts automatically unless you explicitly stop it.
  
!!! tip
    Trailarr has some intenal mechanisms to check if it's running as expected which will notify Docker when it's not, and Docker restarts it. This will only work when `restart` is set to either `unleass-stopped` or `always`.

***Now, those were the easy options, let's go over the hardest part: `volumes`. These needs to be setup properly for Trailarr to work for you.***

### Volumes
This is the most important part of the Docker Compose file. It allows Trailarr to access your media files and store its configuration data persistently.
We will go over the `volumes` section in detail below.
*We understand that this is going to be exhaustive, so we did our best to make it easy to understand and set them up properly.*

`volumes`: There are 2 types of volumes that are needed: AppData and Media Folders

And there are 2 parts to each volume mapping:

1. **Local Folder**: The folder on your computer/server where the media files are stored.
2. **Container Folder**: The folder inside the Trailarr container where it can access the media files.

This is used like:

```yaml
  volumes:
    - <Local Folder>:<Container Folder>
```

#### **Trailarr AppData**

```yaml hl_lines="6"
services:
  trailarr:
    image: nandyalu/trailarr:latest
    # Other options here
    volumes:
      - /path/to/your/trailarr:/config # For Trailarr's database and logs
      # Map your Radarr media folder(s)
      - /path/on/your/host/movies:/media/movies # Example: if Radarr uses /media/movies internally
      # Map your Sonarr media folder(s)
      - /path/on/your/host/tv:/media/tv # Example: if Sonarr uses /media/tv internally
    # Other options here
```

This is crucial. It maps a directory on your computer/server to `/config` inside the Trailarr container. This is where Trailarr will store its persistent data (database, logs, other configuration files, etc.,).

This is a common practice for most Docker containers. For example `Radarr` and `Sonarr` also uses a `/config` inside it's container for appdata.

If you do not provide this, trailarr will still work, but once you restart your system, it will become an amnesia patient! It will forget everything and you have to start from scratch. We don't want that right! so we need to map this to a folder on our computer/server so that the data exists even on restarting the system.

Below are some examples on how you can map this to a folder on your system. But feel free to use a folder that you think is the best.

??? example "Examples 1 & 2"
    You can use something like this

    ```yaml
    volumes:
      - /opt/trailarr/config:/config 
    ```

    Or this:

    ```yaml
    volumes:
      - /home/user/docker/trailarr:/config
    ```

??? example "Example 3 - TRaSH Guides"
    If you used TRaSH Guides for setting up `Radarr` and `Sonarr` Docker containers, they also uses a `/config` inside it's container.

    If you already have those setup like:

    ```yaml
    # Radarr Config - DO NOT USE WITH TRAILARR
    volumes:
      - /docker/appdata/radarr:/config
    ```

    Then, you can use below for Trailarr:

    ```yaml
    # USE THIS WITH TRAILARR
    volumes:
      - /docker/appdata/trailarr:/config
    ```
??? example "Example 4 - Recommended for Windows users"
    **Known Issue - File Access Slowness and Workaround**
    
    Windows users of Docker Desktop often experience slow read/write speeds when using volume mounts. This is a known limitation of file sharing between the Windows host and Docker containers.

    Fortunately, we can use a workaround by creating a `Docker Volume`.

    Here's an example Docker compose that uses a docker volume named `trailarr_data` for `/config`.

    ```yaml hl_lines="5 13"
    services:
      trailarr:
        # Other options here
        volumes:
          - trailarr_data:/config # Docker volume for appdata, the first part `trailarr_data` is the volume name
          - M:\Movies:/m/movies   # Movies drive
          - R:\TV:/r/tv           # TV series drive 1
          - S:\TV:/s/tv           # TV series drive 2
          - T:\TV:/t/tv           # TV series drive 3
        restart: unless-stopped

    volumes:
      trailarr_data:  # volume name, should match the volume name in the service
        # Any extra options for the volume if needed
    ```

    We used `trailarr_data` here, but you can use any name that makes sense to you. Update it on both the highlighted lines!

    Relevant threads discussing this issue:

    - [File access in mounted volumes extremely slow](https://forums.docker.com/t/file-access-in-mounted-volumes-extremely-slow-cpu-bound/8076)
    - [Performance volume mount](https://forums.docker.com/t/performance-volume-mount/27633)

    More information on Docker Volumes can be found in the [Docker documentation](https://docs.docker.com/engine/storage/volumes/).

!!! warning "Things to Note"
    - Do NOT change the right side `/config` part!!!
    - Replace the left side `/path/to/your/trailarr` with an actual path on your system.
    - Make sure this folder actually exists on your system and accessible.

#### **Media Folders**

```yaml hl_lines="7-10"
services:
  trailarr:
    image: nandyalu/trailarr:latest
    # Other options here
    volumes:
      - /path/to/your/trailarr:/config # For Trailarr's database and logs
      # Map your Radarr media folder(s)
      - /path/on/your/host/movies:/media/movies # Example: if Radarr uses /media/movies internally
      # Map your Sonarr media folder(s)
      - /path/on/your/host/tv:/media/tv # Example: if Sonarr uses /media/tv internally
    # Other options here
```
These are examples. You **must** update these.

*   The left side (`/path/on/your/host/...`) should be the **folder path** where media files are located in your system.
*   The right side (`:/movies`, `:/tv`) is how this path will be known *inside the Trailarr container*. You will use these paths later when configuring connections in Trailarr. 

!!! important "Use UNIQUE container folder paths"
    **Make sure these paths are unique and do not conflict with any other container's paths.**
    
    **What does this mean?**
    Let's say you used below configuration:

    ```yaml hl_lines="9 11"
    # DO NOT USE THIS
    services:
      trailarr:
        image: nandyalu/trailarr:latest
        # Other options here
        volumes:
          - /path/to/your/trailarr:/config # For Trailarr's database and logs
          # Map your Radarr media folder(s)
          - /mnt/disk1/media/movies:/media # Container Path: '/media'
          # Map your Sonarr media folder(s)
          - /mnt/disk2/media/tv:/media # Container Path: '/media'
        # Other options here
    ```

    This means we are telling Docker to link both our `Movies` and `TV` folders to `Media` folder inside Trailarr container. Docker will link `Movies` folder to `/media` folder first and then replaces it with `TV` folder later, so Trailarr will only have access to `TV` folder and not the `Movies` folder.

    You can use something like below to get around this:

    ```yaml hl_lines="9 11"
    # USE THIS INSTEAD
    services:
      trailarr:
        image: nandyalu/trailarr:latest
        # Other options here
        volumes:
          - /path/to/your/trailarr:/config # For Trailarr's database and logs
          # Map your Radarr media folder(s)
          - /mnt/disk1/media/movies:/disk1/media # <-- MODIFIED
          # Map your Sonarr media folder(s)
          - /mnt/disk2/media/tv:/disk2/media # <-- MODIFIED
        # Other options here
    ```


!!! important
    If you have a path with spaces in it, you can either:
    
    - Use quotes around the path like this: `"/path/with spaces:/media/movies"` (recommended)
    - Or escape the spaces with a backslash like this: `/path/with\ spaces:/media/movies`

Remember that we got our volumes from `Radarr` and `Sonarr` Docker compose files in [First Things](../01-first-things/index.md), we need to use them here!

Here are some examples:

??? example "Example 1 - TRaSH Guides - Same Folder in `Radarr` and `Sonarr`"
    If you have `Radarr` and `Sonarr` like below:

    ```yaml hl_lines="7 14"
    services:
      radarr:
        image: ghcr.io/hotio/radarr:latest
        # Other options here
        volumes:
          - /docker/appdata/radarr:/config
          - /data:/data
        # Other options here
      sonarr:
        image: ghcr.io/hotio/sonarr:latest
        # Other options here
        volumes:
          - /docker/appdata/sonarr:/config
          - /data:/data
        # Other options here
    ```

    This means your movies are located in `/data/movies` in both your system and the Radarr container. Similary the TV Shows are in `/data/tv`.

    So, we can use this in Trailarr:

    ```yaml hl_lines="7"
    services:
      trailarr:
        image: nandyalu/trailarr:latest
        # Other options here
        volumes:
          - /docker/appdata/trailarr:/config
          - /data:/data
        # Other options here
    ```

    Since `Radarr` and `Sonarr` both have the same volume `/data:/data` we don't need to duplicate it!

??? example "Example 2 - Different folders for `Radarr` and `Sonarr`"
    If you have `Radarr` and `Sonarr` like below:

    ```yaml hl_lines="7 14"
    services:
      radarr:
        image: ghcr.io/hotio/radarr:latest
        # Other options here
        volumes:
          - /docker/appdata/radarr:/config
          - /mnt/movies_disk/media/movies:/media/movies
        # Other options here
      sonarr:
        image: ghcr.io/hotio/sonarr:latest
        # Other options here
        volumes:
          - /docker/appdata/sonarr:/config
          - /mnt/series_disk/media/tv:/media/tv
        # Other options here
    ```

    This means your movies are located in `/mnt/movies_disk/media/movies` in your system and `/media/movies` inside Radarr container. 
    
    Similary the TV Shows are in `/mnt/series_disk/media/tv` in your system and `/media/tv` inside Sonarr container.

    So, we can use this in Trailarr as:

    ```yaml hl_lines="7 8"
    services:
      trailarr:
        image: nandyalu/trailarr:latest
        # Other options here
        volumes:
          - /docker/appdata/trailarr:/config
          - /mnt/movies_disk/media/movies:/media/movies
          - /mnt/series_disk/media/tv:/media/tv
        # Other options here
    ```

    Since `Radarr` and `Sonarr` have their media in different folders, we mapped both of them to Trailarr as is!

??? example "Example 3 - Different `Radarr` and `Sonarr` folders mapped to same container folder"
    If both your `Radarr` and `Sonarr` are mapped to same folder path on the right side like `/data` and you add them to `Trailarr` directly like below, we will have a problem (DO NOT DO THIS).


    ```yaml hl_lines="5 9 13-14"
    # DO NOT USE THIS
    radarr:
      # other config
      volumes:
        - /mnt/disk1/media/movies:/data
    sonarr:
      # other config
      volumes:
        - /mnt/disk2/media/tv:/data
    trailarr:
      # other config
      volumes:
        - /mnt/disk1/media/movies:/data # <-- DO NOT USE
        - /mnt/disk2/media/tv:/data # <-- DO NOT USE
    ```

    Basically, what happens is Docker will map `/mnt/disk1/media/movies` to `/data` inside the container without any issues.

    But then it will try to map `/mnt/disk1/media/tv` to `/data` inside the container, which will override the first mapping.

    We don't know if Docker will map them in this order, so we cannot predict which one will be available inside Trailarr.

    So instead of mapping both to same internal folder `/data`, what we do is change them a little bit, but we need to remember these for configuring [Path Mappings](../03-setup/connections.md#2-path-mappings) later!

    Here's an example of what we can do:

    ```yaml hl_lines="5 9 13-14"
    # USE THIS INSTEAD
    radarr:
      # other config
      volumes:
        - /mnt/disk1/media/movies:/data
    sonarr:
      # other config
      volumes:
        - /mnt/disk2/media/tv:/data
    trailarr:
      # other config
      volumes:
        - /mnt/disk1/media/movies:/data/movies # <-- MODIFIED
        - /mnt/disk2/media/tv:/data/tv # <-- MODIFIED
    ```

??? example "Example 4 - Windows users"
    Let's go over a simple Windows configuration. Concepts form examples 1, 2 and 3 can also be applied to Windows as well, just change the left side of volume mapping with Windows path.

    Windows volume mappings are similar to Linux/MacOS volume mappings with one change, the left side of path is different!

    Windows paths use a '\' (back-slash) and Linux/MacOS paths use '/' (forward-slash).
    
    When adding a volume mapping from Windows (Docker Desktop), you have some options, use the one that works for you:

      - Use the original path as is

        ```yaml
          volumes:
            - C:\Users\nandyalu\Videos\Movies:/data/movies
        ```
      - Use the original path with '\' but instead of '\' replace it with '\\\\'

        ```yaml
          volumes:
            - C:\\Users\\nandyalu\\Videos\\Movies:/data/movies
        ```
      - Or replace '\' with '/' by adding a '/' before the drive letter like this

        ```yaml
          volumes:
            - /C/Users/nandyalu/Videos/Movies:/data/movies
        ```
      
      - If you have network drives and the usual methods don't work, you can also try creating docker volumes for them as explained in the [Network Drives](../01-first-things/network-drives.md#use-docker-network-mount) section.
      - There might be other paths that work, if you know something else that has been working for you, feel free to keep using that! You can also share with us, so that we can add it here!


    !!! warning
        Trailarr Docker container uses `Ubuntu` OS, which is Linux, so we need to add Linux paths for right side paths in volume mapping.

    So, here's an example docker compose for Windows:

    ```yaml hl_lines="5 13"
    services:
      trailarr:
        # Other options here
        volumes:
          - trailarr_data:/config # Docker volume for appdata, the first part `trailarr_data` is the volume name
          - M:\Movies:/m/movies   # Movies drive
          - R:\TV:/r/tv           # TV series drive 1
          - S:\TV:/s/tv           # TV series drive 2
          - T:\TV:/t/tv           # TV series drive 3
        restart: unless-stopped

    volumes:
      trailarr_data:  # volume name, should match the volume name in the service
        # Any extra options for the volume if needed
    ```

??? example "Example 5 - Non-Docker `Radarr` and `Sonarr`"
    There is nothing speciial here other than the fact that you have installed `Radarr` and `Sonarr` native apps and not as Docker containers. 
    
    So, one thing that changes here is the fact that you don't have the right side path of volume mappings.

    Here's what you can do:

      - If all your media (Movies and TV Shows) are under one parent folder like `/mnt/disk1/media` with subfolders for `movies`, `tv`, then you can do this (recommended)

        ```yaml hl_lines="6"
        services:
          trailarr:
            # Other options here
            volumes:
              - /docker/appdata/trailarr:/config # appdata
              - /mnt/disk1/media:/mnt/disk1/media # Media Folders, using same path
            restart: unless-stopped
            # Other options here
        ```
      - OR this

        ```yaml hl_lines="6"
        services:
          trailarr:
            # Other options here
            volumes:
              - /docker/appdata/trailarr:/config # appdata
              - /mnt/disk1/media:/media # Media Folders, mapping to `/media` inside container
            restart: unless-stopped
            # Other options here
        ```
      - If your media is in different paths/disks then map each of them to a specific folder inside Trailarr. `/data`, `/media`, `/mnt`, `/storage` are all good choices. Just make sure you don't use a Linux system folder like `/app`, `/bin`, `/etc`, `/home`, `/var` etc.

        ```yaml hl_lines="6"
        services:
          trailarr:
            # Other options here
            volumes:
              - /docker/appdata/trailarr:/config # appdata
              - /mnt/disk1/movies:/media/movies # Movies Folder
              - /mnt/disk2/tv:/media/tv # TV Folder
            restart: unless-stopped
            # Other options here
        ```

***That's it! You have finished setting up `volumes` and `Docker Compose` for running Trailarr. Now, use the command below to start the container.***


## Run Docker Compose
Once you have customized your `docker-compose.yml` file, save it and run:
```bash
docker-compose up -d
```
To update Trailarr later, you can run:
```bash
docker-compose pull trailarr
docker-compose up -d
```

Now that Trailarr is up and running, we need to configure it to connect to our `Radarr` and `Sonarr` to let it start doing it's job - download trailers. We will go over that in the next section [Setup](../03-setup/index.md).