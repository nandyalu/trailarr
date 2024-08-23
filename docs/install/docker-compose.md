To run the application, you need to have [Docker](https://docs.docker.com/get-docker/){:target="_blank"} installed on your system.

## Installation
Follow the steps below to install the application using Docker Compose.

1. Create a new directory for the application:
```bash
mkdir trailarr && cd trailarr
```

2. Create a `docker-compose.yml` file with the following content:
```yaml
services:
    trailarr:
        image: nandyalu/trailarr:latest
        container_name: trailarr
        environment:
            - TZ=America/New_York
            - PUID=1000
            - PGID=1000
        ports:
            - 7889:7889
        volumes:
            - <LOCAL_APPDATA_FOLDER>:/data
            - <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER>
            - <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER>
        restart: on-failure
```

3. Update the env variables and volume mappings in the `docker-compose.yml` file. See [Environment Variables](env-variables.md) and [Volume Mapping](volume-mapping.md) for the details.

4. Run the following command to start the application:
```bash
docker-compose up -d
```

5. Open your browser and navigate to [http://localhost:7889](http://localhost:7889){:target="_blank"} to access the application.


## Updating

To update the application, run the following commands:

1. Pull the latest image:
```bash
docker-compose pull nandyalu/trailarr
```

2. Run the docker compose command to update the existing container:
```bash
docker-compose up -d
```