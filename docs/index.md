# 

![Trailarr Logo](https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-primary-512-lg.png)

<hr>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/python-3.13-3670A0?style=flat&logo=python" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com" target="_blank"><img src="https://img.shields.io/badge/FastAPI-0.128.0-009688.svg?style=flat&logo=FastAPI" alt="FastAPI"></a>
  <a href="https://angular.dev/" target="_blank"><img src="https://img.shields.io/badge/angular-21.0.6-%23DD0031.svg?style=flat&logo=angular" alt="Angular"></a>
  <a href="https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file" target="_blank"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License: GPL v3"></a>
</p>

<p align="center">
  <a href="https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml" target="_blank"><img src="https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml/badge.svg" alt="Docker Build"></a>
  <a href="https://github.com/psf/black" target="_blank"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a>
  <a href="https://www.codefactor.io/repository/github/nandyalu/trailarr" target="_blank"><img src="https://www.codefactor.io/repository/github/nandyalu/trailarr/badge" alt="CodeFactor"></a>
  <a href="https://hub.docker.com/r/nandyalu/trailarr/" target="_blank"><img src="https://img.shields.io/docker/pulls/nandyalu/trailarr?logo=docker&label=pulls" alt="Docker Pulls"></a>
  <a href="https://github.com/nandyalu/trailarr/issues" target="_blank"><img src="https://img.shields.io/github/issues/nandyalu/trailarr?logo=github" alt="GitHub Issues"></a>
  <a href="https://github.com/nandyalu/trailarr/commits/" target="_blank"><img src="https://img.shields.io/github/last-commit/nandyalu/trailarr?logo=github" alt="GitHub last commit"></a>
</p>


Trailarr is a Docker application to download and manage trailers for your [Radarr](https://radarr.video/){:target="_blank"}, and [Sonarr](https://sonarr.tv/){:target="_blank"} libraries.

Github: [https://github.com/nandyalu/trailarr/](https://github.com/nandyalu/trailarr/){:target="_blank"} 

Docker Hub: [https://hub.docker.com/r/nandyalu/trailarr/](https://hub.docker.com/r/nandyalu/trailarr/){:target="_blank"}

Documentation: [https://nandyalu.github.io/trailarr](https://nandyalu.github.io/trailarr/)

Reddit: [https://www.reddit.com/r/trailarr](https://www.reddit.com/r/trailarr/)

Discord: [https://discord.gg/KKPr5kQEzQ](https://discord.gg/KKPr5kQEzQ){:target="_blank"}

## Features

- Manages multiple Radarr and Sonarr instances to find media
- Detects existing trailers for media items.
- Downloads trailer and organizes it in the media folder.
- Follows plex naming conventions. Works with [Plex](https://www.plex.tv/){:target="_blank"}, [Emby](https://emby.media/){:target="_blank"}, [Jellyfin](https://jellyfin.org/){:target="_blank"}, etc.
- Customizable profiles to manage trailer downloads and processing.
- Responsive UI to view media items and manage trailers.
- Built with Angular and FastAPI.

> If you like the project, please consider giving us a star on [GitHub](https://github.com/nandyalu/trailarr){:target="_blank"}, encourages us to continue improving it.

## Installation & Setup

Trailarr can be installed using Docker (recommended) or directly on Debian based systems. See the [Documentation](https://nandyalu.github.io/trailarr/) for detailed instructions on [Getting Started](https://nandyalu.github.io/trailarr/getting-started/) and [User Guide](https://nandyalu.github.io/trailarr/user-guide/).

We don't have an official video yet, but there is a video by [AlienTech42](https://www.youtube.com/@AlienTech42) on [YouTube](https://www.youtube.com/watch?v=Hz31zWEtY5k&t=8s&pp=ygUOdHJhaWxhcnIgc2V0dXA%3D){:target="_blank"} that explains Trailarr installation and setup on Unraid.

[![Setting up Trailarr - AlienTech42](http://img.youtube.com/vi/Hz31zWEtY5k/maxresdefault.jpg)](https://www.youtube.com/watch?v=Hz31zWEtY5k "Setting up Trailarr - AlienTech42"){:target="_blank"}

## Dependencies

Trailarr is built using the following libraries and tools:

- [Angular](https://angular.dev/){:target="_blank"}
- [Ffmpeg](https://ffmpeg.org/){:target="_blank"}
- [FastAPI](https://fastapi.tiangolo.com){:target="_blank"}
- [Material for Mkdocs](https://github.com/squidfunk/mkdocs-material){:target="_blank"}
- [Python](https://www.python.org/){:target="_blank"}
- [Yt-dlp](https://github.com/yt-dlp/yt-dlp){:target="_blank"}


## Support

If you have any questions or need help, please read the [FAQ](https://nandyalu.github.io/trailarr/troubleshooting/faq/) first. 

If you still need help, please use the below:

- [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"}
- [Reddit](https://www.reddit.com/r/trailarr){:target="_blank"}

> **Note:** Please do not use the GitHub issues for support requests!


## Issues

If you encounter any bugs/issues, please create an issue on the [GitHub repository](https://github.com/nandyalu/issues){:target="_blank"} or post on our [Discord Server](https://discord.gg/KKPr5kQEzQ){:target="_blank"} (recommended).

## Roadmap

There are some changes that are planned for the future. These changes are not guaranteed to be implemented, but they are on the roadmap.

- [x] Add Profiles for Trailers Quality with custom filters (include wait time between downloads)
- [x] Add custom filters to Media pages in frontend
- [x] Add a new method for making path mappings easier
- [x] Add options to disable conversion of downloaded videos
- [x] Update media objects to include more metadata received from Radarr/Sonarr, include media_available flag, downloaded trailer info, etc.
- [x] Add an option to trim videos in `Media Details` page to remove unwanted parts of the trailer. This will help in cases where the trailer has unwanted parts at the beginning or end. 🎬
- [ ] Add Plex integration to send notifications to Plex and scan media signals
- [x] Add support for some fields with translated values
- [x] Update docs for Windows path mappings
- [x] Improve task logging (in progress)
- [x] Add Support for Hardware Acceleration using VAAPI (Intel and AMD)
- [ ] Add Event tracking similar to History in Radarr/Sonarr
- [ ] Add Discord notifications for important events


If you have any suggestions or ideas for new features, please feel free to reach out on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"}. We are always looking for ways to improve the project.

## Contributing

Contributions are welcome! Please see the [Contributing](https://nandyalu.github.io/trailarr/references/contributing/) guide for more information.

Looking for a backend (python) / frontend developers (Angular) to help with the project, if you are interested, please reach out on [Discord](https://discord.gg/KKPr5kQEzQ){:target="_blank"}.

## License

This project is licensed under the terms of the GPL v3 license. See [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file) for more details.

## Disclaimer

For important legal information about using Trailarr, please refer to our [Legal Disclaimer](https://nandyalu.github.io/trailarr/references/legal-disclaimer/).
