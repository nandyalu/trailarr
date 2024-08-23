**Volume mapping is REQUIRED!**

## AppData

Trailarr needs a folder to store the application data. You need to map a local folder to the `/data` folder in the Trailarr container.

Change `<LOCAL_APPDATA_FOLDER>` to the folder where you want to store the application data.

For example, if you want to store the application data in `/var/appdata/trailarr`, the volume mapping would look like this:
```yaml
    volumes:
        - /var/appdata/trailarr:/data
```

!!! warning
    If you are setting the `APP_DATA_DIR` environment variable, make sure to map the volume to the same directory.


## Media Folders

Trailarr needs access to the media folders of Radarr and Sonarr to monitor the media files. You need to map the media folders of Radarr and Sonarr to the Trailarr container.

Trailarr gets the media folders from the Radarr and Sonarr connections you add. So, you need to map the root folder of Radarr and Sonarr to the Trailarr container in a way that Trailarr can access the media files on the paths provided by Radarr and Sonarr. 

Some [examples](#examples) are provided below.

!!! tip
    Make sure the folder paths are correct and the Trailarr has read/write access to the folders.


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
