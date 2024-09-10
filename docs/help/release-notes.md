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