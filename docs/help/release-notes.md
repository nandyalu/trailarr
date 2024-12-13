## **v0.2.6-beta** - _December 13, 2024_
**Bug Fixes:** 🐛

- Fixed a bug in v0.2.5 release that caused trailer download task to fail.

**Other Changes:** ⚡

- A few minor improvements in logging for trailer downloads.
- Added logging (debug only) to indicate that cookies file is used for downloading trailers.

## **v0.2.5-beta** - _December 13, 2024_
**Other Changes:** ⚡

- Current installed version of `yt-dlp` stopped working a few days ago, updating to the latest version!
- A few minor improvements in logging for trailer downloads.
- Updated Github Actions to create PRs for dependency upgrades.

## **v0.2.4-beta** - _December 06, 2024_
**What's New:** ✨

- Added an experimental setting for `Trailer Silence Removal` that will detect and remove silence at end of video. Related to [#75](https://github.com/nandyalu/trailarr/issues/75)
- Added a button to download logs in Frontend `Logs` page, and logs now displays 1000 logs instead of 100.

**Bug Fixes:** 🐛

- Excluded words setting not updating. Fixes [#76](https://github.com/nandyalu/trailarr/issues/76)
- Remove `player_client` option in `yt-dlp` command as that can interfere with cookies when supplied.
- Fixed a bug with trailer download that is causing an exception when moving trailer to media folder. [Issue posted on Reddit](https://www.reddit.com/r/trailarr/comments/1h6rm6s/v0233beta_error/)
- Refactored trailer download method to simplify and reduce errors. Also, when a trailer download fails, the notification will now say Error instead of 'Task Finished'. Fixes [#56](https://github.com/nandyalu/trailarr/issues/56)

**Other Changes:** ⚡

- Completely refactored trailer download to handle Exceptions and logs better.
- Added a section for `YouTube Cookies` in Docs with a recommended way to get `cookies.txt` file.


## **v0.2.3-beta** - _December 04, 2024_
**What's New:** ✨

- Created a [Discord Server](https://discord.gg/BAJsv76N) for Trailarr.
- Added an option `Always Search` which when enabled will not use the YouTube trailer id provided by Arrs and searches on YouTube. Related to [#6](https://github.com/nandyalu/trailarr/issues/6)
- Added an option `Search Query` to specify the query used to search for trailers on YouTube. Fixes [#6](https://github.com/nandyalu/trailarr/issues/6)
- Added an option `Trailer Volume Level` to increase/decrease loudness of the downloaded trailer. Fixes [#41](https://github.com/nandyalu/trailarr/issues/41)
- Added options to specify the minimun and maximum duration of the trailer to download. Fixes [#59](https://github.com/nandyalu/trailarr/issues/59)
- Added an option to specify filter words to exclude trailers with those words in the title. Related to [#59](https://github.com/nandyalu/trailarr/issues/59)
- Browser authentication can now be disabled by setting `WEBUI_DISABLE_AUTH=True` env variable in docker command. Fixes [#67](https://github.com/nandyalu/trailarr/issues/67)
- Logs layout has been updated, added a search bar and increased log size to 1MB (more logs will be displayed now).


**Bug Fixes:** 🐛

- Added some exception handling so that when a trailer download fails, it continues with the next download. Closes [#70](https://github.com/nandyalu/trailarr/issues/70)
- Some other minor bug fixes in trailer downloads.


**Other Changes:** ⚡

- Updated some logs for trailer downloads. 
- Updated the search service in Frontend so that it displays a message when no results are found.
- Upgraded npm and python packages to latest available versions. Updated node to v22, Angular to v19, FastAPI to v0.115.6.
- Created API endpoints for `media` and marked `movie` and `series` endpoints for deprecation. Updated Frontend to use `media` API.
- Filtering of media is now done in the backend and sent to browser, should improve loading times.
- Minor layout changes in Swagger UI.
- Docs updated with new settings and options.


## **v0.2.2-beta** - _October 21, 2024_
**What's New:** ✨

1. Docker Update Check now displays a message in logs and `Update Available` in Settings > About page.
2. Tasks are now shown in alphabetical order in Settings > Tasks page.
3. App will now detect trailer files by looking for `trailer` in the filename instead of `-trailer.`. Fixes [#61](https://github.com/nandyalu/trailarr/issues/61)
4. Default Browser login password can be changed in web UI under `Settings > About > Password`. Related to [#31](https://github.com/nandyalu/trailarr/issues/31)
5. Password can be reset by setting `WEBUI_PASSWORD` ENV variable to `''` (empty) in docker command.
6. Fixed a typo in `Settings > About` page. Thanks to @rafapirotto for the PR [#57](https://github.com/nandyalu/trailarr/pull/57).


**Bug Fixes:** 🐛

1. Fixed an issue with create `Connection` with `Path Mappings` raising an error. Fixes [#53](https://github.com/nandyalu/trailarr/issues/53)

**Other Changes:** ⚡

1. Fixed a typo - renamed file `docket_check.py` to `docker_check.py` in `/backend/core/updates/`.
2. Better handling of `light` and `dark` modes in Frontend with `prefers-color-scheme` media query.
3. Updated `APP_VERSION` in Dev Container to `0.2.1-beta`.
4. Updated FAQ to add `Trailarr not downloading specified trailer from YouTube`.
5. Updated `Settings.md` to include instructions for getting Youtube cookies file. Fixes [#62](https://github.com/nandyalu/trailarr/issues/62)
6. Web UI Password is now hashed before storing.
7. Updated Docs to add [instructions](https://nandyalu.github.io/trailarr/setup/settings/#yt-dlp-cookies-path) on how to add a Youtube cookies file.
8. Created a [Docker Config Tool](https://nandyalu.github.io/trailarr/help/docker-builder/builder.html) under Docs for help with setting up Trailarr.


## **v0.2.1-beta** - _September 27, 2024_
**What's New:** ✨

1. App will now check for updates and display a message in logs and `Update Available` in Settings > About page.

**Bug Fixes:** 🐛

1. Add default `trailer_url` in `download_trailer` function to prevent errors when no trailer is found. Fixes #45
2. Fixed an issue with `f` keypress not working in Frontend. Fixes #44


**Other Changes:** ⚡

1. Updated Docs to indicate that changing Monitor Interval needs container restart to take effect. Fixes #43
2. Updated FAQ in Docs to include information about Trailers taking longer time to download.


## **v0.2.0-beta** - _September 22, 2024_
**What's New:** ✨

1. **BREAKING CHANGE**: Changed default `APP_DATA_DIR` (appdata folder) from `/data` to `/config`. You need to remap your app data folder in your docker compose / set `APP_DATA_DIR` Env variable to `/data` explicitly.
2. Added sort and filtering options in Movies and Series pages. Fixes [#16](https://github.com/nandyalu/trailarr/issues/16) 
3. Link to Docs page updated in About page.
4. Added an option to customize trailer file name. Supports `title`, `year`, `resolution`, `vcodec` and `acodec` options.
5. App now skips videos longer than 10 minutes and/or videos that contain `review` in the title. Should help [#36](https://github.com/nandyalu/trailarr/issues/36) 
6. Added Browser login to Frontend. Default username is `admin` with password `trailarr`. These cannot be updated now, will add an option to update them in future update. Fixes [#31](https://github.com/nandyalu/trailarr/issues/31) 
7. Renamed `DEBUG` to `LOG_LEVEL` to make it consistent with what it does.
8. Adding/Updating a connection will also run the `Arr Data Refresh` task for that connection.
9. App will now verify the downloaded trailer has an audio and a video stream, else mark it as failed and retry download. Also, added a task to clean up any existing trailers without audio/video, delete them and start monitoring those for downloading trailers for them in next run.

**Bug Fixes:** 🐛

1. Fixed a bug that was preventing the app from setting the right permissions to 'Trailers' folder (if enabled for either Movies/Series).
2. Check downloaded trailer is the expected file and contains audio and video streams. Fixes [#37](https://github.com/nandyalu/trailarr/issues/37) 
3. Fixed a bug that prevented Yt-dlp to use the cookies file even when set. Fixes [#29](https://github.com/nandyalu/trailarr/issues/29).
4. Fixed an issue with `Trailer Subtitle Format` option saving to incorrect variable. Fixes [#40](https://github.com/nandyalu/trailarr/issues/40) 
5. Fixed an issue with app not able to delete trailers with `.webm` extensions.
6. Fixed a bug that was removing all media items from library if path mappings are set for that connection and none of them match the media. 

**Other Changes:** ⚡

1. Updated Docs to include `Release Notes` and some `FAQ`s.
2. App now displays logs for video conversions after download.
3. Updated npm and python packages.
4. Added `monitor status` arg to Media object.
5. Added some functionality to always make sure path mappings end with a slash.
6. Added an example in docs for Windows users.


## **v0.1.3-beta** - _August 29, 2024_
**What's New:** ✨

- Add option to supply YouTube cookies to use with yt-dlp. Fixes [#29](https://github.com/nandyalu/trailarr/issues/29)
- Add support for multiple languages in subtitle download settings. Fixes [#25](https://github.com/nandyalu/trailarr/issues/25)

**Bug Fixes:** 🐛

- None

**Other Changes:** ⚡

- None


## **v0.1.2-beta** - _August 29, 2024_

**What's New:** ✨

- None

**Bug Fixes:** 🐛

- FIX: wait for media fails if folder doesn't already exist. Fixes [#28](https://github.com/nandyalu/trailarr/issues/28) and [#32](https://github.com/nandyalu/trailarr/issues/32)
- FIX: normalize filenames to remove unsupported characters. Fixes [#33](https://github.com/nandyalu/trailarr/issues/33)

**Other Changes:** ⚡

- None


## **v0.1.1-beta** - _August 23, 2024_

**What's New:** ✨

- Settings page layout to display settings update messages.
- Search results can now be navigated using Tab key as well as Arrow keys / mouse.
- Added Docker healthcheck command so that docker can automatically flag container as unhealthy and restart if set.
- Documentation added with Mkdocs and hosted on Github pages.

**Bug Fixes:** 🐛

- Fixed an issue that caused App version to not show up in Settings > About page.
- Updated page layout throughout website. Settings page now shows sticky settings bar.

**Other Changes:** ⚡

- Move Docker scripts into scripts folder
- Use apt-get in Dockerfile instead of apt as apt is not recommended for non-interactive.
- Docs build github action to build and deploy docs on changes.

## **v0.1.0-beta** - _August 19, 2024_

**What's New:** ✨

- Merged Movie and Series models in database into Media model. This will help with making Frontend changes to add filters and additional layouts for #16
- Server Stats in Settings > About page now shows monitored count for Movie and Series separately.
- PathMappings have been added to Arr Connections. This lets users add path mappings for individual connections if both Radarr and Sonarr have media mapped to same folder internally. Fixes #8
- Updated Home, Movies and Series pages to display 50 recent items. Related to #16 ... will make additional changes to add filters in a future update.
- Added web manifest to let app be installed as a web app (works only if served as secure [https])


**Bug Fixes:** 🐛

- Fixed a bug with database backups during container startup.
- Fix an issue where Media details page gets stuck in loading state when no media files are found on server for the requested media.

**Other Changes:** ⚡

- Minor updates to alembic (database migrations) configuration.
- Minor layout changes.


## **v0.0.8-beta** - _August 10, 2024_

**What's New:** ✨

- Default appdata folder can now be changed by setting `APP_DATA_DIR` ENV variable in docker command. If setting this make sure to use the same path in volume mapping for /data folder as well. See home for more instructions. fixes [#21](https://github.com/nandyalu/trailarr/issues/21)
- Container will now show app name as ASCII Art, along with the basic configuration.
- Database backups will be created during app startup, and if a database migration fails, database will be restored from backup and app sleeps forever to prevent restarts.

**Bug Fixes:** 🐛

- None

**Other Changes:** ⚡

- pip requirement versions upgraded.
- Update database_url to new path, if `APP_DATA_DIR` is modified. This won't have any effect on `DATABASE_URI` if it was modified using ENV variable or directly within the app.


## **v0.0.7-beta** - _August 8, 2024_

**What's New:** ✨

- Added setting to wait for media to be available before downloading trailer

**Bug Fixes:** 🐛

- None

**Other Changes:** ⚡

- None


## **v0.0.6-beta** - _August 7, 2024_

**What's New:** ✨

- Fixed issue with `PUID`/`PGID` when they already exist inside container, updated logic to use existing user/group if already exists. Fixes [#17](https://github.com/nandyalu/trailarr/issues/17) and [#13](https://github.com/nandyalu/trailarr/issues/13)
- Fixed Click me link in homepage to go to `Settings > Connections`

**Bug Fixes:** 🐛

- None

**Other Changes:** ⚡

- Updated CONTRIBUTING.md to add instructions for using devcontainer.
- Updated Github actions, Dockerfile and README.


## **v0.0.5-beta** - _August 7, 2024_

**What's New:** ✨

- Changed ffmpeg install to check OS architecture and install the correct version. Fixes [#9](https://github.com/nandyalu/trailarr/issues/9)
- Added new Setting for TESTING so that enabling debug mode does not change database to in-memory database!
- Visual improvements in Frontend!

**Bug Fixes:** 🐛

- Updated return value on failed downloads so that app will try and download another video. Fixes issues where video is not available in the country, age restricted video, etc..
- Updated RadarrDataParser to parse movie data without youTubeTrailerId. Fixes [#7](https://github.com/nandyalu/trailarr/issues/7)
- Updated API calls from Movies page. Fixes [#11](https://github.com/nandyalu/trailarr/issues/11)
- Updated Dockerfile to create appuser with the `PUID` and `PGID` supplied while creating container. Fixes [#12](https://github.com/nandyalu/trailarr/issues/12)

**Other Changes:** ⚡

- None


## **v0.0.4-beta** - _August 5, 2024_

**What's New:** ✨

- None

**Bug Fixes:** 🐛

- Do not Delete Media when *Arr Connection fails! Fixes [#5](https://github.com/nandyalu/trailarr/issues/5)

**Other Changes:** ⚡

- None


## **v0.0.3-beta** - _July 31, 2024_

**What's New:** ✨

- None

**Bug Fixes:** 🐛

- None

**Other Changes:** ⚡

- First Release - `v0.0.3-beta` with minor changes to publish docker image with `latest` tag.


## **v0.0.2-beta** - _July 31, 2024_

First Release! 🎉