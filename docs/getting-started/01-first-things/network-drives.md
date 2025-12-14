If you have a network drive that you want to use with Trailarr, you can use it in the following ways.

## **Mount the network drive on the host system**

The recommended way is to mount the network drive on your host system (the machine running Docker) and then bind mount that directory into the Trailarr container.

For example, if you have a network drive mounted at `/mnt/network_drive` on your host, you can add the following volume mapping to your `docker-compose.yml`:

```yaml
volumes:
  - /mnt/network_drive:/data/network_drive
```

This will make the contents of the network drive available inside the Trailarr container at `/data/network_drive`.

## **Use Docker Network mount**

Alternatively, you can use Docker's built-in support for network mounts. This method is less common and may require additional configuration depending on your network storage solution.

!!! tip ""
    If you are on Windows and using SMB shares, and regular mounting doesn't work, this method might help. Refer to the Docker documentation for more details on [using SMB shares with Docker](https://docs.docker.com/engine/storage/volumes/#create-cifssamba-volumes){:target="_blank"} and [Docker Compose Volumes](https://docs.docker.com/reference/compose-file/volumes/){:target="_blank"}.

For example, if you're using an SMB/NFS share, you can add a volume like this:

```yaml
services:
    trailarr:
    image: nandyalu/trailarr:latest
    container_name: trailarr
    environment:
        - TZ=America/New_York # Change to your timezone
        # Other options here
    volumes:
        - trailarr_data:/config # Docker volume for appdata
        - movies:/media/movies # Network drive for movies
        - tv:/media/tv # Network drive for TV shows
    ports:
        - 7889:7889
    restart: unless-started
volumes:
    movies:
        driver_opts:
            type: "cifs" # or "nfs" depending on your setup
            o: "username=xxxx,password=xxxx,uid=1000,gid=1000,file_mode=0777,dir_mode=0777,nosuid,nodev"
            device: "//0.168.1.111/movies/"
    tv:
        driver_opts:
            type: "cifs" # or "nfs" depending on your setup
            o: "username=xxxx,password=xxxx,uid=1000,gid=1000,file_mode=0777,dir_mode=0777,nosuid,nodev"
            device: "//0.168.1.111/tv/"
    trailarr_data:  # volume name, should match the volume name in the service
    # Any extra options for the volume if needed
```

Make sure to adapt this to your network storage solution with the appropriate values for your setup.