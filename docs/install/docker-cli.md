To run the application, you need to have [Docker](https://docs.docker.com/get-docker/){:target="_blank"} installed on your system.

## Installation

To run the application using the Docker CLI, run the following command:

```bash
docker run -d \
    --name=trailarr \
    -e TZ=America/New_York \
    -e PUID=1000 \
    -e PGID=1000 \
    -p 7889:7889 \
    -v <LOCAL_APPDATA_FOLDER>:/data \
    -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER> \
    -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER> \
    --restart unless-stopped \
    nandyalu/trailarr:latest
```

Open your browser and navigate to [http://localhost:7889](http://localhost:7889){:target="_blank"} to access the application.

!!! info
    It is recommended to use `docker-compose` to run the application, as it makes updating easier. See the [Docker Compose](./docker-compose.md) guide for more information.

## Updating

To update the application, run the following commands:

1. Pull latest image:
```bash
docker pull nandyalu/trailarr
```

2. Stop and remove the existing container:
```bash
docker stop trailarr && docker rm trailarr
```

3. Finally, run the updated container using the same `docker run` command used during installation:
```bash
docker run -d ...
```