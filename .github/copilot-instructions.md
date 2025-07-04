---
applyTo: "**"
---
# Copilot Instructions for Trailarr

## Project Overview

Trailarr is a Dockerized application for downloading and managing trailers for Radarr and Sonarr media libraries. It integrates with Plex, Emby, and Jellyfin, and provides a modern Angular frontend and a FastAPI backend.

## Key Technologies

- **Backend:** Python 3.13, FastAPI, SQLModel, Alembic, SQLite
- **Frontend:** Angular 19, TypeScript
- **Documentation:** Mkdocs for Material, Markdown files
- **Testing:** Pytest for backend, Jest for frontend
- **Media Processing:** ffmpeg, yt-dlp
- **Containerization:** Docker, App runs in a Docker container by running `entrypoint.sh`

## Main Features

- Manage multiple Radarr/Sonarr instances
- Download, organize, and convert trailers for movies/series
- Hardware acceleration support (NVIDIA GPUs, VAAPI planned)
- Custom trailer profiles and filters
- Responsive web UI for management and monitoring
- REST API with OpenAPI/Swagger docs

## Folder Structure

- `/backend`: FastAPI app, database, core logic, API routes, tasks, config
- `/frontend`: Angular app, UI components, services, environment config
- `/assets`: Images, icons, OpenAPI docs, static files
- `/docs`: Markdown documentation, changelogs, contributing guide
- `/scripts`: Shell scripts for setup, ffmpeg, ytdlp, entrypoint, etc.

## Coding Conventions

- **Python:** PEP-8, Black formatter, type hints, specific exceptions, log errors where caught
- **Angular:** Angular Style Guide, modular components (standalone by default), Signals for reactivity and async, SCSS for styles, API calls via services
- **Commits:** Use clear, descriptive messages; follow SemVer for versioning
- Add appropriate comments and docstrings for clarity. Add comments within code to explain why and not what is being done.
- Use type annotations for better code understanding and IDE support

## API

- RESTful endpoints under `/api/v1/`
- OpenAPI spec in `/frontend/contract/swagger.yaml`
- API key authentication (query/header/cookie)
- WebSocket support for real-time updates

## Development

- Use Docker for local development and deployment
- Generate Frontend Static Files: `ng build --configuration production` which outputs to `/frontend-build/`
- Run backend with VSCode Task `Run FastAPI` which will start the FastAPI server, that serves the static files from `/frontend-build/` on app root and `/api/v1/` for API endpoints
- Tests: Pytest for backend, Jest for frontend

## Product Goals

- Seamless trailer management for media servers
- Easy setup and configuration via web UI
- Support Hardware acceleration for video processing (NVIDIA GPUs, VAAPI planned)
- Customizable trailer profiles and filters
- Real-time monitoring and notifications
- Responsive and modern UI for all devices
- Extensible for future integrations (e.g., Plex notifications)

---

**Tip:** Update this file as your app evolves to help Copilot provide the most relevant suggestions!
