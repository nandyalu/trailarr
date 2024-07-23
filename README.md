<p align="center">
  <img src="docs/images/logo-full-512.png" width=50%>
</p>

# Trailarr2

[![Python](https://img.shields.io/badge/python-3.12-3670A0?style=flat&logo=python)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
![Angular](https://img.shields.io/badge/angular-17.3.6-%23DD0031.svg?style=flat&logo=angular)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/UNCode101/trailarr)

[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/UNCode101/trailarr)
[![Docker Image CI](https://github.com/UNCode101/trailarr/actions/workflows/docker-image.yml/badge.svg)](https://github.com/UNCode101/trailarr/actions/workflows/docker-image.yml)

Trailarr is a Docker application to download and manage trailers for your media library. It integrates with your existing services, such as [Plex](https://www.plex.tv/), [Radarr](https://radarr.video/), and [Sonarr](https://sonarr.tv/)!

## Features

- Manages multiple Radarr and Sonarr instances to find media
- Runs in background like Radarr/Sonarr.
- Checks if a trailer already exists for movie/series. Download it if set to monitor.
- Downloads trailer and organizes it in the media folder.
- Follows plex naming conventions.
- Downloads trailers for youtube trailer urls set in Radarr/Sonarr.
- Searches youtube for a trailer if not set in Radarr/Sonarr.
- Option to download desired youtube video as trailer for any movie/series.
- Converts audio, video and subtitles to desired formats.
- Beautiful and responsive UI to manage trailers and view details of movies and series.
- Built with Angular and FastAPI.

## Installation

### Docker Compose

To run the application, you need to have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system.

```docker
version: '3.2'
services:
    trailarr:
        image: trailarr:latest
        container_name: trailarr
        environment:
            - TZ=America/New_York
        ports:
            - 7889:7889
        volumes:
            - <LOCAL_APPDATA_FOLDER>:/data
            - <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDERS>
            - <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDERS>
        restart: on-failure
```

- Change `<LOCAL_APPDATA_FOLDER>` to the folder where you want to store the application data.
- Change `<LOCAL_MEDIA_FOLDER>` to the folder where your media is stored.
- Change `<RADARR_ROOT_FOLDERS>` to the folder where Radarr stores movies.
- Change `<SONARR_ROOT_FOLDERS>` to the folder where Sonarr stores TV shows.
- Repeat the volume mapping for each Radarr and Sonarr instance you want to monitor.


Run the following command to start the application:
```bash
docker-compose up -d
```

Open your browser and navigate to `http://localhost:7889` to access the application.

#### Updating

To update the application, run the following commands:
```bash
docker-compose pull trailarr
docker-compose up -d
```

### Docker CLI

To run the application using the Docker CLI, run the following command:

```bash
docker run -d \
    --name=trailarr \
    -e TZ=America/New_York \
    -p 7889:7889 \
    -v <LOCAL_APPDATA_FOLDER>:/data \
    -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDERS> \
    -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDERS> \
    --restart unless-stopped \
    trailarr:latest
```

- Change `<LOCAL_APPDATA_FOLDER>` to the folder where you want to store the application data.
- Change `<LOCAL_MEDIA_FOLDER>` to the folder where your media is stored.
- Change `<RADARR_ROOT_FOLDERS>` to the folder where Radarr stores movies.
- Change `<SONARR_ROOT_FOLDERS>` to the folder where Sonarr stores TV shows.
- Repeat the volume mapping for each Radarr and Sonarr instance you want to monitor.

Open your browser and navigate to `http://localhost:7889` to access the application.

#### Updating

To update the application, run the following commands:

Pull latest image:
```bash
docker pull trailarr
```

Stop and remove the existing container:
```bash
docker stop trailarr && docker rm trailarr
```

Finally, run the updated container using the same `docker run` command used during installation:
```bash
docker run -d ...
```


### Documentation

Coming soon...

### Support

If you need help, please craete an issue on the [GitHub repository](https://github.com/UNCode101/issues)

### Issues

Issues are very valuable to this project.

- Ideas are a valuable source of contributions others can make
- Problems show where this project is lacking
- With a question, you show where contributors can improve the user experience

Thank you for creating them.

### Contributing

Coming soon...

### License

This project is licensed under the terms of the GPL v3 license. See [GPL-3.0 license](https://github.com/UNCode101/trailarr?tab=GPL-3.0-1-ov-file) for more details.