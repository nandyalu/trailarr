<!-- <p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-512-lg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-light-512-lg.png">
    <img alt="Trailarr logo with name" src="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-primary-512-lg.png" width=50%>
  </picture>
</p> -->
![Trailarr Logo](https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-512-lg.png#only-dark)
![Trailarr Logo](https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-light-512-lg.png#only-light)

<!-- # Trailarr -->

[![Python](https://img.shields.io/badge/python-3.13-3670A0?style=flat&logo=python)](https://www.python.org/){:target="_blank"}
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com){:target="_blank"}
[![Angular](https://img.shields.io/badge/angular-19.2.10-%23DD0031.svg?style=flat&logo=angular)](https://angular.dev/){:target="_blank"}
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/nandyalu/trailarr){:target="_blank"}

[![Docker Build](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml/badge.svg)](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml){:target="_blank"}
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black){:target="_blank"}
[![CodeFactor](https://www.codefactor.io/repository/github/nandyalu/trailarr/badge)](https://www.codefactor.io/repository/github/nandyalu/trailarr){:target="_blank"}
[![Docker Pulls](https://badgen.net/docker/pulls/nandyalu/trailarr?icon=docker&label=pulls)](https://hub.docker.com/r/nandyalu/trailarr/){:target="_blank"}
[![GitHub Issues](https://img.shields.io/github/issues/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/issues){:target="_blank"}
[![GitHub last commit](https://img.shields.io/github/last-commit/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/commits/){:target="_blank"}


Trailarr is a Docker application to download and manage trailers for your [Radarr](https://radarr.video/){:target="_blank"}, and [Sonarr](https://sonarr.tv/){:target="_blank"} libraries.

Github: [https://github.com/nandyalu/trailarr/](https://github.com/nandyalu/trailarr/){:target="_blank"} 

Docker Hub: [https://hub.docker.com/r/nandyalu/trailarr/](https://hub.docker.com/r/nandyalu/trailarr/){:target="_blank"}

Documentation: [https://nandyalu.github.io/trailarr](https://nandyalu.github.io/trailarr){:target="_blank"}

Reddit:
[https://www.reddit.com/r/trailarr](https://www.reddit.com/r/trailarr){:target=_blank}

Discord: [https://discord.gg/KKPr5kQEzQ](https://discord.gg/KKPr5kQEzQ){:target="_blank"}

## Features

- Manages multiple Radarr and Sonarr instances to find media
- Runs in background like Radarr/Sonarr.
- Checks if a trailer already exists for movie/series. Download it if set to monitor.
- Downloads trailer and organizes it in the media folder.
- Follows plex naming conventions. Works with [Plex](https://www.plex.tv/){:target="_blank"}, [Emby](https://emby.media/){:target="_blank"}, [Jellyfin](https://jellyfin.org/){:target="_blank"}, etc.
- Downloads trailers for trailer id's set in Radarr/Sonarr.
- Searches for a trailer if not set in Radarr/Sonarr.
- Option to download desired video as trailer for any movie/series.
- Converts audio, video and subtitles to desired formats. Hardware Acceleration supported for NVIDIA GPUs.
- Beautiful and responsive UI to manage trailers and view details of movies and series.
- Built with Angular and FastAPI.

## Installation & Setup

See the [Documentation](https://nandyalu.github.io/trailarr/){:target="_blank"} for detailed instructions on how to [install](./install.md) and [setup](./setup/connections.md) Trailarr.

## Dependencies

Trailarr is built using the following libraries and tools:

- [Angular](https://angular.dev/){:target="_blank"}
- [Ffmpeg](https://ffmpeg.org/){:target="_blank"}
- [FastAPI](https://fastapi.tiangolo.com){:target="_blank"}
- [Python](https://www.python.org/){:target="_blank"}
- [Yt-dlp](https://github.com/yt-dlp/yt-dlp){:target="_blank"}


## Support

If you have any questions or need help, please read the [FAQ](https://nandyalu.github.io/trailarr/help/faq/) first. 

If you still need help, please use the below:

- [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"}
- [Reddit](https://www.reddit.com/r/trailarr){:target="_blank"}

> **Note:** Please do not use the GitHub issues for support requests!


If you like the project, please consider giving us a star on [GitHub](https://github.com/nandyalu/trailarr){:target="_blank"}.

## Issues

If you encounter any bugs/issues, please create an issue on the [GitHub repository](https://github.com/nandyalu/issues){:target="_blank"} or post on our [Discord Server](https://discord.gg/KKPr5kQEzQ){:target="_blank"} (recommended).

## Roadmap

There are some changes that are planned for the future. These changes are not guaranteed to be implemented, but they are on the roadmap.

- [ ] Add Profiles for Trailers Quality with custom filters (include wait time between downloads)
- [x] Add custom filters to Media pages in frontend
- [ ] Add a new method for making path mappings easier
- [ ] Add options to disable conversion of downloaded videos
- [x] Update media objects to include more metadata received from Radarr/Sonarr, include media_available flag, downloaded trailer info, etc.
- [ ] Add Plex integration to send notifications to Plex and scan media signals
- [x] Add support for some fields with translated values
- [ ] Update docs for Windows path mappings
- [ ] Improve task logging
- [ ] Add Support for Hardware Acceleration using VAAPI (Intel and AMD)


If you have any suggestions or ideas for new features, please feel free to reach out on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"}. We are always looking for ways to improve the project.

## Contributing

Contributions are welcome! Please see the [Contributing](./CONTRIBUTING.md) guide for more information.

Looking for a backend (python) / frontend developers (Angular) to help with the UI, if you are interested, please reach out on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"}.

## License

This project is licensed under the terms of the GPL v3 license. See [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file) for more details.

## Disclaimer

For important legal information about using Trailarr, please refer to our [Legal Disclaimer](./help/legal-disclaimer.md).
