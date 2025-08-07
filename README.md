<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-512-lg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-light-512-lg.png">
    <img alt="Trailarr logo with name" src="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-primary-512-lg.png" width=50%>
  </picture>
</p>

[![Python](https://img.shields.io/badge/python-3.13-3670A0?style=flat&logo=python)](https://www.python.org/) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com) 
[![Angular](https://img.shields.io/badge/angular-20.1.4-%23DD0031.svg?style=flat&logo=angular)](https://angular.dev/) 
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/nandyalu/trailarr)

[![Docker Build](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml/badge.svg)](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 
[![CodeFactor](https://www.codefactor.io/repository/github/nandyalu/trailarr/badge)](https://www.codefactor.io/repository/github/nandyalu/trailarr)
[![Docker Pulls](https://badgen.net/docker/pulls/nandyalu/trailarr?icon=docker&label=pulls)](https://hub.docker.com/r/nandyalu/trailarr/) 
[![GitHub Issues](https://img.shields.io/github/issues/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/issues) 
[![GitHub last commit](https://img.shields.io/github/last-commit/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/commits/)


Trailarr is a Docker application to download and manage trailers for your [Radarr](https://radarr.video/), and [Sonarr](https://sonarr.tv/) libraries.

Github: [https://github.com/nandyalu/trailarr/](https://github.com/nandyalu/trailarr/)

Docker Hub: [https://hub.docker.com/r/nandyalu/trailarr/](https://hub.docker.com/r/nandyalu/trailarr/)

Documentation: [https://nandyalu.github.io/trailarr](https://nandyalu.github.io/trailarr)

Reddit: [https://www.reddit.com/r/trailarr](https://www.reddit.com/r/trailarr)

Discord: [https://discord.gg/KKPr5kQEzQ](https://discord.gg/KKPr5kQEzQ)

## Features

- Manages multiple Radarr and Sonarr instances to find media
- Runs in background like Radarr/Sonarr.
- Checks if a trailer already exists for movie/series. Download it if set to monitor.
- Downloads trailer and organizes it in the media folder.
- Follows plex naming conventions. Works with [Plex](https://www.plex.tv/), [Emby](https://emby.media/), [Jellyfin](https://jellyfin.org/), etc.
- Downloads trailers for trailer id's set in Radarr/Sonarr.
- Searches for a trailer if not set in Radarr/Sonarr.
- Option to download desired video as trailer for any movie/series.
- Converts audio, video and subtitles to desired formats. Hardware Acceleration supported for NVIDIA GPUs.
- Customizable profiles to manage trailer downloads and processing.
- Beautiful and responsive UI to manage trailers and view details of movies and series.
- Built with Angular and FastAPI.

## Installation

See the [Documentation](https://nandyalu.github.io/trailarr/) for detailed instructions on [Getting Started](https://nandyalu.github.io/trailarr/getting-started/) and [User Guide](https://nandyalu.github.io/trailarr/user-guide/).

We don't have an official video yet, but there is a video by [AlienTech42](https://www.youtube.com/@AlienTech42) on [YouTube](https://www.youtube.com/watch?v=Hz31zWEtY5k&t=8s&pp=ygUOdHJhaWxhcnIgc2V0dXA%3D) that explains Trailarr installation and setup on Unraid.

[![Setting up Trailarr - AlienTech42](http://img.youtube.com/vi/Hz31zWEtY5k/0.jpg)](https://www.youtube.com/watch?v=Hz31zWEtY5k "Setting up Trailarr - AlienTech42")

## Dependencies

Trailarr is built using the following libraries and tools:

- [Angular](https://angular.dev/)
- [Ffmpeg](https://ffmpeg.org/)
- [FastAPI](https://fastapi.tiangolo.com)
- [Material for Mkdocs](https://github.com/squidfunk/mkdocs-material)
- [Python](https://www.python.org/)
- [Yt-dlp](https://github.com/yt-dlp/yt-dlp)


## Support

If you have any questions or need help, please read the [FAQ](https://nandyalu.github.io/trailarr/troubleshooting/faq/) first. 

If you still need help, please use the below:

- [Discord](https://discord.gg/KKPr5kQEzQ)
- [Reddit](https://www.reddit.com/r/trailarr).

> **Note:** Please do not use the GitHub issues for support requests!


If you like the project, please consider giving us a star on [GitHub](https://github.com/nandyalu/trailarr).

## Issues

If you encounter any bugs/issues, please create an issue on the [GitHub repository](https://github.com/nandyalu/issues) or post on our [Discord Server](https://discord.gg/KKPr5kQEzQ) (recommended).

## Roadmap

There are some changes that are planned for the future. These changes are not guaranteed to be implemented, but they are on the roadmap.

- [x] Add Profiles for Trailers Quality with custom filters (include wait time between downloads)
- [x] Add custom filters to Media pages in frontend
- [x] Add a new method for making path mappings easier
- [x] Add options to disable conversion of downloaded videos
- [x] Update media objects to include more metadata received from Radarr/Sonarr, include media_available flag, downloaded trailer info, etc.
- [ ] Add an option to trim videos in `Media Details` page to remove unwanted parts of the trailer. This will help in cases where the trailer has unwanted parts at the beginning or end. 🎬
- [ ] Add Plex integration to send notifications to Plex and scan media signals
- [x] Add support for some fields with translated values
- [x] Update docs for Windows path mappings
- [ ] Improve task logging (in progress)
- [x] Add Support for Hardware Acceleration using VAAPI (Intel and AMD)


If you have any suggestions or ideas for new features, please feel free to reach out on [Discord](https://discord.gg/KKPr5kQEzQ). We are always looking for ways to improve the project.

## Contributing

Contributions are welcome! Please see the [Contributing](https://nandyalu.github.io/trailarr/references/contributing) guide for more information.

Looking for a backend (python) / frontend developers (Angular) to help with the UI, if you are interested, please reach out on [Discord](https://discord.gg/KKPr5kQEzQ).

## License

This project is licensed under the terms of the GPL v3 license. See [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file) for more details.

## Disclaimer

For important legal information about using Trailarr, please refer to our [Legal Disclaimer](https://nandyalu.github.io/trailarr/references/legal-disclaimer/).
