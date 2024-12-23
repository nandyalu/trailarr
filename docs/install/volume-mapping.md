**Volume mapping is REQUIRED!**

## AppData

Trailarr needs a folder to store the application data. You need to map a local folder to the `/config` folder in the Trailarr container.

Change `<LOCAL_APPDATA_FOLDER>` to the folder where you want to store the application data.

For example, if you want to store the application data in `/var/appdata/trailarr`, the volume mapping would look like this:
```yaml
    volumes:
        - /var/appdata/trailarr:/config
```

!!! warning
    If you are setting the `APP_DATA_DIR` environment variable, make sure to map the volume to the same directory.


## Media Folders

Trailarr needs access to the media folders of Radarr and Sonarr to monitor the media files. You need to map the media folders of Radarr and Sonarr to the Trailarr container.

There are 2 parts to a volume mapping:

1. **Local Folder**: The folder on your system where the media files are stored.
2. **Container Folder**: The folder inside the Trailarr container where the it can access the media files.

??? example "Media Volume Mapping"
    1. If you have movies in `/mnt/disk1/media/movies` on your system, this is the local folder.
    2. If you see this folder as `/media/movies` inside the Radarr container, this is the container folder. So, you need to map it similarly to the Trailarr container as well.
    3. The volume mapping will look like:
    ```yaml
        - /mnt/disk1/media/movies:/media/movies
    ```

Trailarr gets the media folders from the Radarr and Sonarr connections you add. So, you need to map the root folder of Radarr and Sonarr to the Trailarr container in a way that Trailarr can access the media files on the paths provided by Radarr and Sonarr. 

Some [examples](#examples) are provided below. 

If you need additional help, there is a [Docker Config Tool](https://nandyalu.github.io/trailarr/help/docker-builder/builder.html){:target="_blank"} that will help you generate the docker-compose file with the correct volume mappings and path mappings.

If you are still facing issues, you can ask for help in the [Discord Server](https://discord.gg/KKPr5kQEzQ){:target="_blank"}.

!!! tip
    Make sure the folder paths are correct and the Trailarr has read/write access to the folders.

!!! warning
    If your folder paths have spaces, you need to escape them with a backslash (`\`) or enclose the path in quotes (`"`) like `/tv\ shows` or `/"tv shows"`.

### Radarr

If you want to monitor the movies in Radarr, you need to map the root folder of Radarr to the Trailarr container.

For example, if you have movies in `/mnt/disk1/media/movies` on your system, and Radarr has this folder mapped to `/media/movies` inside the Radarr container, the volume mapping would look like this:

```yaml
    volumes:
        - /mnt/disk1/media/movies:/media/movies
```

### Sonarr

If you want to monitor the TV shows in Sonarr, you need to map the root folder of Sonarr to the Trailarr container.

For example, if you have TV shows in `/mnt/disk1/media/tv` on your system, and Sonarr has this folder mapped to `/media/tv` inside the Sonarr container, the volume mapping would look like this:

```yaml
    volumes:
        - /mnt/disk1/media/tv:/media/tv
```


## Examples

### Example 1 - Different Local & Container folders

Radarr and Sonarr have different local folders mapped to different folders inside their containers.

Radarr has `/mnt/disk1/movies` mapped to `/media/movies` and Sonarr has `/mnt/disk1/tv` mapped to `/media/tv`, you can map them to Trailarr like this:

```yaml
    volumes:
        - /mnt/disk1/movies:/media/movies
        - /mnt/disk1/tv:/media/tv
```


### Example 2 - Same Local folder parent, Different Container folders

Both Radarr and Sonarr have different local folders mapped to the different folders inside their containers.

Radarr has `/mnt/disk1/media/movies` mapped to `/media/movies` and Sonarr has `/mnt/disk1/media/tv` mapped to `/media/tv`. However both mapped local folders are in the same parent folder `/mnt/disk1/media`. So, you can map the parent folder to Trailarr like this:

```yaml
    volumes:
        - /mnt/disk1/media:/media
```

OR, you can map the individual folders to Trailarr like this:

```yaml
    volumes:
        - /mnt/disk1/media/movies:/media/movies
        - /mnt/disk1/media/tv:/media/tv
```


### Example 3 - Different Local folders, Same Container folder

If you have both Radarr and Sonarr with different local folders mapped to the same folder inside their containers, you can do custom mapping of local folders and set the appropriate path mapping while adding those connections!

For example, if Radarr has `/mnt/disk1/media/movies` mapped to `/media` and Sonarr has `/mnt/disk1/media/tv` mapped to `/media`, you can do custom mapping like below:

1. Map `/mnt/disk1/media` to `/media` in Trailarr like this:
```yaml
    volumes:
        - /mnt/disk1/media/movies:/media/movies
        - /mnt/disk1/media/tv:/media/tv
```

2. Set the [path mapping](../setup/connections.md#path-mapping) for Radarr like:
![Radarr Path Mapping](radarr-mapping.png)

    !!! tip
        The `Path From` needs to match root folder inside Radarr (`/media`), and the `Path To` needs to match the folder inside Trailarr where the media is mapped (`/media/movies`).

3. Set the [path mapping](../setup/connections.md#path-mapping) for Sonarr like:
![Sonarr Path Mapping](sonarr-mapping.png)

    !!! tip
        The `Path From` needs to match root folder inside Sonarr (`/media`), and the `Path To` needs to match the folder inside Trailarr where the media is mapped (`/media/tv`).


### Example 4 - Windows Path Mapping

1. If you are using Windows, you need to modify the Windows folder path to be compatible with Linux. You can use the following format for the volume mapping:

    ```yaml
        volumes:
            /c/Users/username/Movies:/media/movies
            /c/Users/username/TV:/media/tv
    ```

    1. This will map `C:\Users\username\Movies` in your system to `/media/movies` within the Trailarr container.
    2. If you are running Radarr / Sonarr as docker containers, you need to update the `/media/movies` and `/media/tv` paths to match the paths set in the Radarr / Sonarr container volume mappings.


    !!! info "Network Shares"
        If you are using network shares, you need to mount the network share to your system as a drive and then map the local folder to the Trailarr container.

        You could possibly map the network share directly to the Trailarr container, however, Trailarr won't be able to provide support for it at this time.

2. Now, you if you are running Radarr / Sonarr as docker containers, you can skip the next step and proceed to the [Environment Variables](env-variables.md) setup.

3. Otherwise, you need to setup the [Path Mapping](../setup/connections.md#path-mapping) for Radarr and Sonarr connections, as the media folder paths in Radarr/Sonarr will look like `C:\Users\username\Movies\The Matrix (1999)`, which won't be accessible by Trailarr as it's not a valid linux path. So, we need to add a path mapping to tell Trailarr what to replace that path with.

4. Remember, in step 1 we mapped `C:\Users\username\Movies` to `/media/movies`, so you need to go into `Settings -> Connections`, open Radarr/Sonarr and Add Path Mapping like this:

```yaml
    Path From: C:\Users\username\Movies
    Path To: /media/movies
```

5. And then do similar for Sonarr like this:

```yaml
    Path From: C:\Users\username\TV
    Path To: /media/tv
```

Now, Trailarr will replace `C:\Users\username\Movies` with `/media/movies` in the media paths provided by Radarr, and `C:\Users\username\TV` with `/media/tv` in the media paths provided by Sonarr.
