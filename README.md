<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-512-lg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-light-512-lg.png">
    <img alt="Trailarr logo with name" src="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-primary-512-lg.png" width=50%>
  </picture>
</p>

[![Python](https://img.shields.io/badge/python-3.12-3670A0?style=flat&logo=python)](https://www.python.org/) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com) 
[![Angular](https://img.shields.io/badge/angular-19.0.1-%23DD0031.svg?style=flat&logo=angular)](https://angular.dev/) 
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/nandyalu/trailarr)

[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Container&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/nandyalu/trailarr) 
[![Docker Build](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml/badge.svg)](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml) 
[![Docker Pulls](https://badgen.net/docker/pulls/nandyalu/trailarr?icon=docker&label=pulls)](https://hub.docker.com/r/nandyalu/trailarr/) 
[![GitHub Issues](https://img.shields.io/github/issues/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/issues) 
[![GitHub last commit](https://img.shields.io/github/last-commit/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/commits/)

Trailarr is a Docker application to download and manage trailers for your [Radarr](https://radarr.video/), and [Sonarr](https://sonarr.tv/) libraries.

Github: [https://github.com/nandyalu/trailarr/](https://github.com/nandyalu/trailarr/)

Docker Hub: [https://hub.docker.com/r/nandyalu/trailarr/](https://hub.docker.com/r/nandyalu/trailarr/)

Documentation: [https://nandyalu.github.io/trailarr](https://nandyalu.github.io/trailarr)

Reddit: [https://www.reddit.com/r/trailarr](https://www.reddit.com/r/trailarr)

Discord: [https://discord.gg/rWC3TaaK](https://discord.gg/rWC3TaaK)

## Features

- Manages multiple Radarr and Sonarr instances to find media
- Runs in background like Radarr/Sonarr.
- Checks if a trailer already exists for movie/series. Download it if set to monitor.
- Downloads trailer and organizes it in the media folder.
- Follows plex naming conventions. Works with [Plex](https://www.plex.tv/), [Emby](https://emby.media/), [Jellyfin](https://jellyfin.org/), etc.
- Downloads trailers for trailer id's set in Radarr/Sonarr.
- Searches for a trailer if not set in Radarr/Sonarr.
- Option to download desired video as trailer for any movie/series.
- Converts audio, video and subtitles to desired formats.
- Option to remove SponsorBlocks from videos (if any data is available).
- Beautiful and responsive UI to manage trailers and view details of movies and series.
- Built with Angular and FastAPI.

## Installation

See the [Installation](https://nandyalu.github.io/trailarr/install/) guide for detailed instructions on how to install Trailarr.

## Setup

See the [Setup](https://nandyalu.github.io/trailarr/setup/connections/) guide for detailed instructions on how to setup Trailarr.

## Dependencies

Trailarr is built using the following libraries and tools:

- [Angular](https://angular.dev/)
- [Ffmpeg](https://ffmpeg.org/)
- [FastAPI](https://fastapi.tiangolo.com)
- [Python](https://www.python.org/)
- [Yt-dlp](https://github.com/yt-dlp/yt-dlp)


## Support

If you have any questions or need help, please read the [FAQ](https://nandyalu.github.io/trailarr/help/faq/) first. If you still need help, please create an issue on the [GitHub repository](https://github.com/nandyalu/issues) or post a question on [Reddit](https://www.reddit.com/r/trailarr/) or join our [Discord](https://discord.gg/BAJsv76N) (recommended).

## Issues

Issues are very valuable to this project.

- Ideas are a valuable source of contributions others can make
- Problems show where this project is lacking
- With a question, you show where contributors can improve the user experience

Thank you for creating them.

## Contributing

Contributions are welcome! Please see the [Contributing](https://github.com/nandyalu/trailarr/blob/main/.github/CONTRIBUTING.md) guide for more information.

Looking for a frontend developer (Angular) to help with the UI, if you are interested, please reach out in the [Discussions](https://github.com/nandyalu/trailarr/discussions) or [Reddit](https://www.reddit.com/r/trailarr/).

## License

This project is licensed under the terms of the GPL v3 license. See [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file) for more details.

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
