# Phase 9 — Video Types

**Status:** IN PROGRESS — started Oct 7, 2026 on branch `feat/phase9-video-types` (see
"Execution notes" at the end) · **Release:** v0.14.0, target ~Oct 22, 2026 · **Depends on:** Phases 5 (clean flags),
7 (paths), 8 (TMDB — non-trailer types are TMDB-only by construction).
Refreshed against the v0.13.0 code on Sep 24, 2026. Paths, names and claims below match
the `dev` branch at commit `e31cf7d2`. Items marked **Refresh note** record a conflict
between the code and a settled decision; they need a maintainer answer before execution.
Answered on Sep 24, 2026: H9 is dropped in this phase (decision 9), the duration cap is
1200 (decision 10), and the Plex names are verified (decision 2). Still open: the
naming resolution (decision 6), `Always Search` on non-trailer types (decision 5), and
manual assign across types (Pitfalls).
Amended Oct 1, 2026: decision 11 (trailer fields in the Expanded and Table views)
added, with its verification, docs and exit criteria.

## Objective

Profiles gain a `video_type` (TRAILER default); downloads record theirs. A featurette
can never again masquerade as "the trailer". Non-trailer types resolve exclusively from
TMDB candidates — no YouTube search fallback exists for them, by construction.

## Design decisions (settled)

1. **Enum `VideoType`** (VARCHAR, no migration for future additions):
   TRAILER, TEASER, CLIP, FEATURETTE, BEHIND_THE_SCENES, BLOOPERS, OTHER —
   mirrors TMDB's `type` values + OTHER for search-only/unknown.

   **Refresh note (storage shape):** the stored values must be the lowercase strings
   (`'trailer'`, `'behind_the_scenes'`, …). Phase 8 already wrote `'trailer'` into every
   `mediavideo.video_type` row, as a plain `str` column (`VIDEO_TYPE_TRAILER` in
   `database/models/mediavideo.py`). Do NOT declare the new columns as
   `sa_Enum(VideoType, native_enum=False)` like `EventType` and `VideoSource`: that form
   stores the member NAME (`'TRAILER'`), and the existing rows would stop matching. Keep
   plain VARCHAR columns and validate against a `str` enum in the models. TMDB writes
   its types in title case with spaces (`'Behind the Scenes'`), so the mapping from TMDB
   is explicit, not a `.lower()`. TMDB also documents `Opening Credits` (series) —
   check the current TMDB list at execution and map anything unknown to OTHER.
2. **Additive migration:** `trailerprofile.video_type` (default 'trailer'),
   `download.video_type` (default 'trailer'), `mediavideo.video_type` already exists
   (Phase 8). One-time inference pass over existing download rows by filename/folder
   conventions: suffixes `-trailer|-teaser|-clip|-featurette|-behindthescenes|-short|
   -scene|-bloopers` and parent folders `Trailers/ Teasers/ Clips/ Featurettes/
   Behind The Scenes/ Bloopers/ Scenes/ Shorts/ Others/` (Plex/Jellyfin extras
   conventions). Unmatched → 'trailer' (status quo, safest).

   Verified: `mediavideo.video_type` exists (indexed, `str`, default `'trailer'`,
   migration `1c9c26339940`). `download` and `trailerprofile` have no type column. The
   Alembic head is `b8d43c3d4630` (`add_last_videos_refresh_to_media`), so the Phase 9
   migration takes `down_revision = "b8d43c3d4630"`.

   Scope of the inference: a download row exists today only for a file that the scan
   counted as a trailer — a file in a folder named `trailer`/`trailers` or in the
   `folder_name` of ANY profile (`get_trailer_folders()` in
   `database/manager/trailerprofile/read.py`), or a file with "trailer" in its name.
   So the inference only ever sees `Trailers/` files, `*trailer*` files, and the files
   in a hacky profile's custom folder (such as `Featurettes/`). That is W1's population.

   **Refresh note (convention names):** both players were checked on Sep 24, 2026.

   | | Plex ([movie extras](https://support.plex.tv/articles/local-files-for-trailers-and-extras/)) | Jellyfin |
   |---|---|---|
   | Folders | `Behind The Scenes`, `Deleted Scenes`, `Featurettes`, `Interviews`, `Scenes`, `Shorts`, `Trailers`, `Other` | the Plex list plus `Clips`, `Samples`, `Extras` (lowercase in its docs) |
   | Suffixes | `-behindthescenes`, `-deleted`, `-featurette`, `-interview`, `-scene`, `-short`, `-trailer`, `-other` | the Plex list plus `-clip`, `-sample`, `-extra` |

   Plex says the file name "must end in the -Extra_Type value exactly", with no space
   after the hyphen, so write the suffixes in lowercase. The folder is `Other`, not
   `Others`. For TV shows, Plex reads the same folder names in the show folder, and
   season extras in `Season XX/<type folder>/` (its TV extras page blocks automated
   reads; this comes from its search summary — this matters for Phase 10). Neither
   player knows `Teasers/`, `Bloopers/`, `-teaser` or `-bloopers`, and Plex does not
   know `Clips/` or `-clip`. For the INFERENCE (reading) this is harmless: accept the
   plan's names plus `Other/`, `-other`, `Extras/`, `-extra`, `Interviews/`,
   `-interview`. For NAMING (decision 6, writing) it matters — see the note there.
3. **Satisfaction becomes type-aware:** profile P satisfied iff active download with
   `profile_id=P.id AND video_type=P.video_type` (claiming unattributed rows also
   type-matched). DownloadAttempt key unchanged (profile carries the type).

   Code sites: the rule is `evaluate_satisfaction` in `services/satisfaction.py` (pure;
   `services/trailers/trailers/missing.py:_apply_claims` persists its claims). Two more
   places attribute files and must match on type too: `pick_profile_for_download` in
   `services/profiles.py` (scan-time attribution, called from
   `tasks/files_scan.py:_process_trailer_changes`), and
   `attribute_unattributed_downloads` in `tasks/download_attribution.py` (the
   "Attribute Trailer Downloads" startup pass, `tasks/startup_passes.py`). The manual
   assign endpoint `PUT /media/{id}/downloads/{download_id}/profile` is the fourth — see
   Pitfalls.
4. **Scan classification:** `is_trailer_file` generalizes to
   `classify_extra_file(path) -> VideoType | None`; scan records the classified type;
   the trailer-specific ffprobe size heuristics apply to TRAILER only; other types
   trust naming conventions.

   Code sites: there are TWO `is_trailer_file` implementations —
   `MediaScanner.is_trailer_file` (`services/files/media_scanner.py`, the one the scan
   uses) and `FilesHandler.is_trailer_file` (`services/files/files_handler.py`, used by
   its `get_trailer_path` helpers). Both hard-code `TRAILER_MAX_DURATION_SECONDS = 600`.
   Generalize both, or delete the `FilesHandler` copy if nothing needs it. The scan
   stores only a bool (`filefolderinfo.is_trailer`); the type lands on the download row
   through `record_new_trailer_download` (`services/trailers/trailers/service.py`).
5. **Resolution:** TRAILER keeps Phase 8 order incl. search fallback; every other type
   consumes TMDB candidates only (resolver filters `video_type`), and skips media with
   no tmdb_id (Issue feed later).

   Code path (verified): `trailer_search.get_video_id` →
   `_video_id_from_candidates` → `database/manager/mediavideo.read_candidates(media.id)`
   (its `video_type` argument defaults to `'trailer'`; pass the profile's type) →
   `services/trailers/resolver.choose_candidates`. The live search
   (`search_yt_for_trailer`, `_remember_search_result`) runs inside `get_video_id`
   itself, so the "no search" branch for non-trailer types goes there, before the
   search. For a non-trailer type only USER and TMDB rows can exist: ARR and SEARCH
   rows are always trailers.

   Phase 8 stores only trailers: `services/tmdb/videos.to_candidates` keeps TMDB type
   `Trailer` and drops the rest. Phase 9 keeps every type, and sorts official-first
   inside each type (Phase 8 plan-deviation 2 — TMDB order is not useful). No extra
   TMDB call is needed: one `/videos` call already returns every type.

   **Refresh note (`Always Search`):** Phase 8 changed `Always Search` to "take nothing
   from the table and search" (phase-08 deviation 5; `choose_candidates` returns `[]`).
   On a non-trailer profile that means "never download", because this decision forbids
   the search. Recommended resolution: validation rejects `always_search=True` with a
   non-trailer `video_type`, and the profile editor hides the search-only fields
   (`Always Search`, `Search Query`, include/exclude words) for those types.

   **Refresh note (`Trailer Language`):** Phase 8 made the profile `language` a FILTER,
   not a preference (phase-08 deviation 5), and the TMDB call asks only for the
   languages the enabled profiles name (`include_video_language`). Featurettes on TMDB
   are mostly `en` or have no language. A featurette profile that names `it` will
   usually find nothing and stay pending. Keep the filter semantics (settled in
   Phase 8); document it, and show the reason in the matrix (W3).
6. **Naming:** default file naming per type (`…-{video_type}.{ext}` suffix mapping
   matching the conventions above; folder mode maps type → conventional folder name).
   Profile file_name/folder templates gain `{video_type}` token; defaults for NEW
   profiles use it; existing profiles untouched.

   Code sites: the default `file_name` is `"{title} ({year})-trailer.{ext}"` and the
   default `folder_name` is `"Trailers"` (`database/models/trailerprofile.py`). Tokens
   live in `VALID_FILE_DICT` in the same file; add `video_type` there. The writers are
   `get_trailer_filename`, `get_trailer_path` and `move_trailer_to_folder` in
   `services/trailers/trailer_file.py`.

   **Refresh note (player conventions):** "matching the conventions above" writes names
   no player reads for TEASER (`-teaser`, `Teasers/`) and BLOOPERS, and Plex does not
   read CLIP either (see the table under decision 2, now verified for both players). A
   file a player does not recognise shows as nothing, or as a separate video.
   Recommended resolution: write only names that BOTH players read — TEASER →
   `-trailer` / `Trailers/` (players show it as a trailer; the download row still
   records `teaser`), CLIP → `-scene` / `Scenes/`, FEATURETTE → `-featurette` /
   `Featurettes/`, BEHIND_THE_SCENES → `-behindthescenes` / `Behind The Scenes/`,
   BLOOPERS and OTHER → `-other` / `Other/`. The scan must then NOT relabel a
   Trailarr-made row from its name: a path that matches an existing download keeps the
   recorded type, and the classifier runs only for files with no row.
7. **Hacky-profile detection (nudge, never forced):** startup one-time check — profiles
   whose `search_query`/`file_name` contain teaser/clip/featurette/behind keywords but
   `video_type=TRAILER` → log + (post-Phase 11: Issue). Suggest the setting; do not
   change it.

   Also check `folder_name` (such as `Featurettes`), `include_words` and
   `exclude_words` — `docs/user-guide/settings/profiles/settings/search.md` itself shows
   `teaser,clip,featurette` as an include-words example. Per README rule 1, a one-time
   check is a data migration or a registered startup pass (`tasks/startup_passes.py`)
   that is safe to re-run; a log-only nudge qualifies as a pass.
8. **UI:** profile editor type dropdown (with "TMDB-only" hint for non-trailer);
   downloads section + matrix show a type badge; "Known videos" list (Phase 8) gains a
   type column and becomes the picker for USER-source candidates.

   What Phase 8 actually shipped: the Known videos list in
   `frontend/src/app/media/media-details/media-details.component.html` shows a source
   badge, the name (a YouTube link), the language, and a remove button. It has NO
   per-row download action and NO picker — Phase 8 decision 5b's "download this one"
   was not built. A USER row is added two ways: the old **YouTube Trailer ID** field
   (`saveYtId` → `services/media.set_youtube_id`) and `POST /media/{id}/videos`
   (`yt_id`, `language`) → `services/media.add_video` →
   `database/manager/mediavideo.add_user_video`. The manager already takes a
   `video_type`; the endpoint, the service and the UI do not expose it. Phase 9 adds the
   type to that path and builds the picker/download action from scratch. With every
   TMDB type stored, the list grows (The Matrix lists featurettes before its trailers),
   so group or filter it by type.
9. **Drop `media.youtube_trailer_id` in this phase (hygiene H9).** Maintainer decision,
   Sep 24, 2026. The `mediavideo` table becomes the only record of known video ids. This
   is a destructive migration; it is the second one after Phase 5 (README ladder rule
   amended). Steps, in this order, in one migration:
   1. **Backfill.** Phase 8's migration copied the column into `mediavideo` as `SEARCH`
      rows, but the Arr sync, the search and `set_youtube_id` kept writing the column
      after that. `INSERT OR IGNORE` every non-empty value that has no row for its
      media yet, as a `SEARCH` row (same shape as migration `1c9c26339940`). The unique
      key `(media_id, video_id)` makes it safe to re-run.
   2. **Saved filters** (the Phase 5 pattern): a VIEW filter on `youtube_trailer_id`
      with `IS_EMPTY` / `IS_NOT_EMPTY` becomes a new virtual bool field `has_videos`
      (the media has any `mediavideo` row) with the same meaning. Any other operator
      (for example EQUALS one id) cannot map: delete it and log a warning with the
      filter name, as Phase 5 did. A PROFILE filter on the field gets the same rule.
   3. **Drop the column** (batch mode) and its index, if any.

   Code: remove every read and write (the ~24 backend files listed under "What Phase 8
   left" below). The Arr sync writes only its `ARR` row; notifications print the video
   id from the download row; `record_new_trailer_download` takes the id from the
   `mediavideo` row that matches the file, or none. API: `MediaRead` and the other
   media models lose the field — an API contract change; release-note it for API
   users. Frontend (`models/media.ts`, `models/customfilter.ts`,
   `services/media.service.ts`, `media-details`): the **YouTube Trailer ID** field
   becomes the add-video form on the Known videos list, and the **Watch** button
   opens the first video in the list (the one the download would take).
10. **Raise the `Maximum Duration` cap to 1200 seconds (20 minutes) for every profile**
    ([#686](https://github.com/nandyalu/trailarr/issues/686)). Maintainer decision, Sep
    24, 2026. The default stays 600, so no existing profile changes. The minimum stays
    30 (it is already 30 in the backend and in the UI). Changes:
    - Fix the backend check in `database/models/trailerprofile.py`:
      `if 90 > self.max_duration > 600:` is a chained comparison that is never true, so
      the API accepts any value today. Write it as
      `if not 90 <= self.max_duration <= 1200:`, and fix the message range. Add a test
      for 89, 90, 1200 and 1201 — this line runs only on the error path.
    - The UI slider: `[maxValue]="600"` → `1200`, and the help text "Maximum is 600" in
      `edit-profile.component.html`. The `min_duration` help text says "Default is 30",
      but the model default is 60 — make the text say 60.
    - The scan's own `TRAILER_MAX_DURATION_SECONDS = 600` (two copies, decision 4) is a
      different limit: it tells a trailer file from a movie file. It stays at 600 and
      applies to TRAILER only.
    - The validator is on `_TrailerProfileBase`, so it runs on READ too
      (`TrailerProfileRead`, and `TrailerProfile.model_validate`). The broken check let
      the API store any value, so a row above 1200 would make the profile unreadable
      after the fix. The Phase 9 migration clamps it:
      `UPDATE trailerprofile SET max_duration = 1200 WHERE max_duration > 1200`, and
      logs each profile name it changes. A value below 90 cannot exist: the working
      checks `min_duration >= 30` and `max - min >= 60` already stop it. Put a
      `max_duration = 5000` profile in the v0.13.0 catch-up fixture.

11. **Trailer fields in the Expanded and Table views** (maintainer decision, Oct 1,
    2026). The Configure Fields dialog of the library pages gains the fields of the
    trailer rows: resolution, video codec, audio codec, audio language, subtitles,
    container, duration, size, owning profile and trailer count. Frontend only: the
    list pages already hold every download row (`combinedMedia` in
    `frontend/src/app/services/media.service.ts` joins `/media/downloads_raw` into
    `media.downloads`), so there is no API change, no migration and no new request.
    It ships in this phase because the phase adds the type badge to the same display
    and `video_type` joins the same list. The base fields depend on nothing else in
    the phase and may land on `dev` first.

    - **One field registry.** The options live in four places today: two arrays in
      `frontend/src/app/media/headers/normal-header/normal-header.component.ts`
      (`expandedFieldOptions`, `tableColumnOptions`), `allColumnDefs` in
      `media-cards/table/table.component.ts`, and a chain of `@if (hasField(...))`
      blocks in `media-cards/expanded/expanded.component.html`. Replace them with one
      registry, `frontend/src/app/media/utils/media-fields.ts`: an ordered list of
      `{key, label, group: 'media' | 'trailer', value(...)}` entries, where a media
      field reads the media item and a trailer field reads one download row. The
      dialog, the table and the expanded card all read the registry. The dialog shows
      two headings, **Media** and **Trailers**, like the groups of the filter editor.
      The stored keys and the two localStorage entries (`TrailarrExpandedFields`,
      `TrailarrTableColumns`) do not change, and the defaults in `media.service.ts` do
      not change: nothing new shows until a user turns it on (README: new options off).
    - **Fields and keys.** Keys reuse the Phase 6 virtual-filter names where one
      exists, so a filter and a column share one vocabulary: `download_resolution`
      (`1080p`), `download_video_codec`, `download_audio_codec`,
      `download_audio_language`, `download_subtitles` (`srt (eng)`, or a dash),
      `download_container` (`mp4`), `download_duration` (`durationSecondsConvert`
      pipe), `download_size` (`fileSize` pipe), `download_profile` (the profile NAME
      from `ProfileService.allProfiles`; `Unknown` for `profile_id = 0` and
      `Deleted [id]` for a missing one, as Phase 6 W2), and `download_count`. This
      phase adds `download_video_type`; Phase 10 adds `download_season`. Labels carry
      the `Trailer` prefix in the table header (`Trailer Resolution`) and drop it under
      the dialog's Trailers heading. If this phase's sweep of user-facing "trailer"
      strings (Pitfalls) renames them to "video", rename these labels in the same
      sweep.
    - **Source rows.** Active downloads only (`file_exists`), the same rows the Phase
      6 filters read, so a filter and a cell never disagree. Ordered newest first (the
      `downloaded_at` order). The order is computed once per media item and shared by
      every cell, so the lines align across columns.
    - **One block per trailer, not one value per field (maintainer decision).** A
      media item can own one download per profile today, per type after this phase
      and per season after Phase 10, so the fields of one trailer stay together.
      Expanded view: below the media tags, one row of tags per trailer that holds
      every selected trailer field (`1080p · h264 · aac (eng) · srt (eng) · mp4 ·
      2:15 · 45 MB · Movies 1080p`). Table view: the row stays one per media item;
      each trailer column stacks one line per trailer, in the shared order, so the
      stacked lines read as a sub-table across the trailer columns. Decide at
      execution, with a screenshot, whether one combined `Trailers` column reads
      better on narrow tables; the stacked columns are the default. A dash when there
      is no active download.
    - **Cap.** At most `MAX_TRAILERS_PER_CARD = 3` trailers per card or cell, then a
      `+N more` line that opens the details page. One constant in the registry. Phase
      10 reuses it when seasons bring twenty trailers to one show, and may make it a
      setting then. The count field ignores the cap.
    - **Not in scope:** sorting by a trailer field (`sortOptions` stays
      `keyof Media`), the poster view, and URL persistence of the field choice (the
      existing fields use localStorage only; keep that).
    - **Tests:** vitest on the registry (`media-fields.spec.ts`): every value
      function with zero, one and three active downloads plus a deleted one; the cap;
      the profile-name fallbacks. One assertion that the registry and
      `applyDownloadFilter` (`media/utils/apply-filters.ts`) select the same rows.

## What Phase 8 left for this phase

- **The `media.youtube_trailer_id` column (hygiene H9)** — now decision 9. It is still
  read and written in 24 backend files: `get_video_id` and `download_trailer` write it,
  `record_new_trailer_download` falls back to it for a scanned file with no known id,
  the Arr sync writes it (`services/connections/base.py`), notifications print it
  (`services/notifications/dispatcher.py`), it is a filter field
  (`database/models/filter.py`), and the media details page uses it for the YouTube
  Trailer ID field and the **Watch** button. Code comments in `services/media.py` and
  migration `1c9c26339940` point here.

  The refresh recommended moving the drop to Phase 10. The maintainer decided on Sep
  24, 2026 to drop it in Phase 9 (decision 9), and amended the README ladder rule.
- **The unique key is `(media_id, video_id)`, but `replace_source_rows` works per
  `(source, video_type, season)`.** Phase 8 calls it once, for trailers. If Phase 9
  calls it once per type, a video that TMDB moves from `Teaser` to `Trailer` is not in
  the "existing" set of the new type and not in the "others" set (same source), so the
  insert raises an IntegrityError. Recommended: the TMDB refresh replaces all TMDB rows
  of a `(media, season)` in one call, and the manager takes the type from each incoming
  row. Add a test for a type change at TMDB. Phase 10 hits the same trap with seasons.
- **Existing TMDB lists hold trailers only** — see W6.
- **Duration cap and issue #686** — now decision 10; facts under Related issues.
- **Which videos on disk a download skips, and more than one video per item** (open
  question, recorded Oct 1, 2026 from the v0.13.1 review). `download_trailer` skips
  every video the item already has on disk, from any profile. Since v0.13.1 an upgrade
  skips only its own replaced trailers: with the old rule, a profile whose only TMDB
  target another profile owned had no target, and an upgrade never searches, so it
  backed off on every run. A plain download still skips all, so a second profile on the
  same item gets TMDB's second choice, exactly what `track-tmdb-upgrade.md` criticised
  in Batch Download. What the maintainer wants to settle before this phase:
  1. Two profiles that differ in output (1080p and 4K, or one folder per player) want
     the *same* video. The skip should be per profile everywhere, as the upgrade does
     now: a profile skips the videos *it* owns for the item, and a video that failed in
     this retry chain.
  2. "Two trailers per item" works today only by accident, through two overlapping
     profiles with the same settings. It is better modelled as a count on the profile
     (`video_count`, default 1): the profile owns N downloads of N distinct accepted
     videos, satisfaction counts them, and the resolver skips what the profile already
     owns. The attempt table's `unit` key was shaped for exactly this kind of
     per-profile sub-unit, as were seasons in Phase 10.
  3. Video types do not change the answer: a Teaser profile and a Trailer profile draw
     from different TMDB lists, and a skip by video id across types is harmless, since
     TMDB gives each video one type.

  Recommendation: make the skip per profile in this phase (one branch in
  `download_trailer`, the upgrade branch already shows the shape), and leave the count
  to Phase 10 or later. Until then, document that two overlapping profiles with the
  same settings get two different trailers.

## Wargame

- W1. Existing multi-profile users with a hacky featurette profile: inference relabels
  their existing featurette *files* (folder/suffix-based); their profile stays TRAILER
  until they change it → satisfaction mismatch: profile TRAILER, downloads now
  FEATURETTE → profile unsatisfied → re-download of a real trailer. ⚠️ This is the
  phase's mass-download risk. Mitigation: inference ONLY relabels rows whose owning
  profile ALSO looks hacky (detection from D7) — otherwise leave 'trailer'; plus
  release-note the exact steps ("set your extras profile's video type before/after
  upgrade; the app suggests which"). Wargame this on a constructed hacky config-dev
  variant before release.
- W2. File matches folder convention but suffix says otherwise (`Trailers/x-teaser.mkv`):
  suffix wins (more specific); table-driven classifier tests.
- W3. TMDB has no featurettes for a media: profile stays pending with no candidates —
  distinct backoff reason "no candidates" with LONG retry (candidates refresh cadence,
  not download backoff) so it doesn't hammer refresh.
  Today the matrix knows only `reason: "pending" | "backoff"`
  (`services/trailers/trailers/pending.py`, `frontend/src/app/models/pending.ts`), and
  a failed resolution raises `DownloadFailedError`, which takes the normal backoff
  (1d, 2d, 4d, capped at 7d). The candidates cadence is the 7-day TTL on
  `media.last_videos_refresh`. Such media also stay in `compute_library_pending`,
  which feeds the `Refresh Video Lists` task (`tasks/videos_refresh.py`, 200 items per
  run from a pending list of at most 1,000); make sure permanent "no candidates" items
  do not crowd out media that can download.
- W4. Mixed-type unattributed downloads + claim pass: type-aware claiming must not
  assign a teaser file to a trailer profile (extends v0.9.9 attribution logic).
  NOTE (2026-07-19): type-aware claiming creates the first state where a pending
  profile coexists with an unclaimable unattributed file (pre-P9, claim-on-spot
  resolves every such case). Per the issue-gating decision in phase-11 (4b),
  media with unresolved unattributed downloads should be SKIPPED by the download
  task from this phase on — implement the gate here (skip-not-attempt, reason
  surfaced in the matrix), don't wait for Phase 11's feed framework.
- W5. Type added to `EventType`-style VARCHAR enum later: no migration — verified by
  design. (Holds only for the plain VARCHAR storage of decision 1's refresh note.)
- W6. (Added at refresh.) First run after the upgrade: every TMDB list in the table
  holds trailers only, and `media.last_videos_refresh` says it is fresh for up to
  7 days. A new featurette profile then finds no candidates and falls into W3's
  "no candidates" state for a week. The migration must make the lists stale (set
  `media.last_videos_refresh` to NULL), and W3's state must not start until a list
  with all types has been fetched. The refresh task is capped at 200 items per run
  every 12 hours, so a 1,700-title library takes several days; the lazy refresh in the
  download task covers the rest.

## Pitfalls

- The trailer-named helpers assume "trailer": `MediaScanner.get_trailer_paths` and
  `is_trailer_file`, the `FilesHandler` copies, `get_trailer_folders`, and the cleanup
  task `trailer_cleanup` (`tasks/cleanup.py` — it checks streams only, so it works for
  any type, but its log lines say "trailer"). Sweep `services/files`, `tasks/files_scan.py`
  and `services/trailers` for hardcoded 'trailer' strings and log lines.
  (`check_trailer_exists` no longer exists.)
- The delete-trailers API/UI actions ("Delete trailer") must scope by type or rename to
  "Delete videos" with a picker — decide at execution with maintainer (UX).
  Current code: the UI is the **Delete Trailers** dialog in
  `frontend/src/app/media/headers/edit-header/edit-header.component.html`; the service
  is `services/media.delete_trailers`, which deletes EVERY live download of the item —
  after this phase that includes featurettes. `DELETE /media/{id}/trailer` is already
  deprecated in favour of `/files/delete`.
- Skip the trailer-only profile options for other types: `skip_if_plex_trailer`
  (`_check_plex_trailer` in `services/trailers/trailer.py`) must not stop a featurette
  download because Plex has a trailer.
- Manual paths: `POST /media/{id}/download?profile_id&yt_id` and the batch download
  (`tasks/download_trailers.py`) take any id for any profile — the id can come from the
  user, so no TMDB check applies, but the download records the profile's type.
  `POST /media/{id}/search` searches YouTube for a profile — refuse it for a non-trailer
  profile. `PUT /media/{id}/downloads/{download_id}/profile` (manual assign) can pair a
  featurette file with a trailer profile: reject the mismatch or record the type with
  the assignment — decide at execution. The assignment is user-owned state (README
  invariant 6).
- Frontend filter family (Phase 6): add `download_video_type` to the virtual fields —
  small, do it here. Add it to the field registry of decision 11 too, as a
  `Trailer Type` column. It is the first STRING virtual field: today there are only bool,
  int and date lists (`VIRTUAL_*_COLS` in `database/models/filter.py`,
  `virtual*FilterKeys` in `frontend/src/app/models/customfilter.ts`). Evaluation lives
  in `services/filters.py` and `frontend/src/app/media/utils/apply-filters.ts`; the
  v0.13.0 filter counts (#618) must count it too.
- `api/v1/media.py` still holds logic (hygiene H16: "do it when Phase 9 or 10 touches
  this router"). This phase touches it; take H16 only if it stays small.
- OpenAPI + client regen; docs (profiles settings pages get a Video Type section).

## Related issues

- [#686](https://github.com/nandyalu/trailarr/issues/686) "Increase the max duration
  limit" (open, Sep 22, 2026). A user grabs bonus features (behind the scenes,
  featurettes, interviews) with search-based profiles, and these often run longer than
  the 600-second cap of `Maximum Duration`. **Decided Sep 24, 2026: the cap becomes
  1200 seconds for every profile (decision 10).** The facts behind it:
  - The 600 cap is enforced only in the UI (`[maxValue]="600"` in
    `frontend/src/app/settings/profiles/edit-profile/edit-profile.component.html`) and
    in the docs (`search.md`: range 90–600). The backend check in
    `database/models/trailerprofile.py` is `if 90 > self.max_duration > 600:`, a chained
    comparison that is never true, so the API accepts any value.
  - `max_duration` also applies to TMDB candidates: `trailer_file.verify_download`
    rejects the file after the download. So a long TMDB featurette fails for a
    featurette profile unless the cap moves — the cap is relevant to Phase 9 itself,
    not only to search users.
  - The scan has its own `TRAILER_MAX_DURATION_SECONDS = 600` (two copies). Decision 4
    already limits it to TRAILER; keep it there.
  - TMDB has no "interview" type (they are usually `Featurette`). A user who searches
    for interviews keeps a TRAILER-type search profile, which is W1's hacky profile.
    The startup nudge (decision 7) must not tell them to switch to a type that cannot
    search.

## Verification

Classifier table tests (all conventions × case variants); satisfaction type-matrix
tests; scratch env: profile TEASER on a movie with TMDB teasers → downloads teaser with
correct name; hacky-profile fixture upgrade produces suggestions and NO unexpected
downloads (assert download task dry pass). config-dev copy: inference pass summary
reviewed by maintainer before release.

`max_duration` (decision 10, hygiene H24): tests for 89, 90, 1200 and 1201 through the
API (`POST`/`PUT` of a profile), not only the model; a gauntlet run from the fixture
row with `max_duration = 5000` ends at 1200 and the profile list still loads; the
profile editor slider reaches 1200 in the real app.

Trailer fields (decision 11): in the real app, turn on every Trailers field in both
views and check an item with two profiles (two lines, aligned across the trailer
columns), an item with no download (dashes), an unknown-profile item (`Unknown`), and
an item with four downloads (three shown plus `+1 more`). The table scrolls sideways at
phone width with no page scroll. Field keys saved by v0.13.x still load, and a saved key
the registry no longer knows is ignored, not thrown.

Release-fixture gauntlet (`backend/tests/test_upgrade_gauntlet.py`, README rule 4):
v0.13.0 changed the schema (the `mediavideo` table, `trailerprofile.language`,
`media.last_videos_refresh`, `downloadattempt.last_video_id`) but added no fixture —
the newest one is `v0_11_3_download_filters.sql`. Add a catch-up
`v0_13_0_media_videos.sql` first (MediaVideo rows of every source including USER, a
profile with a language, a `youtube_trailer_id` with no matching `mediavideo` row, a
saved view filter on `youtube_trailer_id` for each operator, and a profile with
`max_duration = 5000`), then the hacky-extras fixture for W1 (a `Featurettes`
folder profile with its files attributed), and a v0.14.0 fixture for this phase's own
shape. Also add a test for the `replace_source_rows` type-change trap, and walk the new
error paths (no candidates, no tmdb_id, refused search) in a real run or a test that
reads the code (README: "A green suite does not mean the code runs").

## Docs to update

- `docs/user-guide/settings/profiles/settings/general.md` (or a dedicated settings
  subpage) — **Video Type** section: the type list, TRAILER-only search fallback
  ("non-trailer types come exclusively from TMDB — they need a TMDB key and a
  `tmdb_id`"), naming/folder conventions per type, the `{video_type}` template token.
  The same page has the Phase 8 **Trailer Language** section: say that the language
  filter applies to every type, and that most TMDB extras are English or have no
  language.
- `docs/user-guide/settings/profiles/examples.md` — add a real extras-profile example
  (e.g. Featurettes profile) replacing the keyword-hack pattern users invented.
- `docs/user-guide/settings/profiles/index.md` — the "Trailarr is evolving" help box
  says "Maybe (maybe, no promises!) let the user download Featurettes, Clips, etc." —
  this phase DELIVERS that; rewrite the box.
- `docs/user-guide/library/media-details/index.md` — type badges on downloads/matrix;
  Known-videos type column + USER-candidate picker; the delete action's final UX
  (pitfalls: "Delete trailer" vs "Delete videos" — document whichever is decided).
  H9 is taken (decision 9): rewrite the **YouTube Trailer ID** / **Save YouTube ID**
  sections and the **Watch** button. Grep `docs/` for `youtube_trailer_id` and
  `YouTube Trailer ID` — the filters page and the API docs name the field too.
- **Extras-profile migration guidance** (W1, the mass-download risk): a docs section
  users can be linked to from the startup nudge and release notes — exact steps for
  "I had a hacky featurette profile". Put it in the profiles docs; release notes link
  to the anchor.
- `docs/user-guide/settings/profiles/filters.md` — `download_video_type` added to the
  Phase 6 virtual-field table.
- `docs/user-guide/library/index.md` — the page never describes the **Poster**,
  **Expanded** and **Table** views or the Configure Fields dialog (shipped in v0.9.4,
  #306). Add a **Views** section before **Sorting**: the three views, the dialog, the
  **Media** and **Trailers** groups with the field list, one block per trailer and the
  cap (decision 11). Badge the Trailers group `add` 0.14.0. One screenshot per view
  with trailer fields on.
- `docs/troubleshooting/faq.md` — add/refresh "Can Trailarr download extras
  (featurettes, clips, teasers)?" — now yes, per profile video type, TMDB-only.
- Pages that Phase 8 added or changed (added at refresh):
  - `docs/user-guide/settings/tmdb.md` — "It keeps the trailers" and the "What changes
    with a key" table describe trailers only. Add the other types, and say that they
    come only from TMDB.
  - `docs/user-guide/tasks/index.md` — **Refresh Video Lists** says "media items that
    are waiting for a trailer". Say "a video".
  - `docs/user-guide/settings/profiles/settings/search.md` — **Always Search** and the
    search fields apply to trailer profiles only (decision 5 refresh note);
    **Maximum Duration** range becomes 90–1200 (decision 10), and say that it also
    applies to TMDB videos.
  - `docs/user-guide/settings/profiles/settings/file.md` — **File Name** and **Folder
    Name**: the `{video_type}` token and the per-type defaults.
  - `docs/user-guide/settings/profiles/settings/plex.md` — **Skip if Plex Trailer**
    applies to trailer profiles only.
- Release notes: extras-profile migration guidance leads (exit criteria); the
  trailer fields in the Expanded and Table views (decision 11); the
  `youtube_trailer_id` removal for API users and for saved filters (decision 9); the
  1200-second cap with credit to the #686 reporter; roadmap tick.

## Exit criteria

Type-aware satisfaction proven; zero-unexpected-downloads on hacky fixture; Docs
section executed; release notes with the extras-profile migration guidance;
`youtube_trailer_id` dropped with the backfill and filter migration (decision 9);
the `max_duration` check fixed, the cap at 1200, and stored values above 1200 clamped
(decision 10, H24) — close #686 with the release. Trailer fields show in both views from one field
registry, with the cap and the per-trailer block (decision 11).

## Execution notes (Oct 7, 2026)

Decisions the maintainer answered at the start of execution:

- Decision 5: agreed. Non-trailer profiles stay TMDB-only, no search. The profile editor hides the search settings for them and shows a small banner that says the profile does not fall back to a search. The model rejects `always_search=True` on a non-trailer profile.
- Decision 6: agreed. Trailarr writes only the names that both Plex and Jellyfin read (teaser → `-trailer`/`Trailers`, clip → `-scene`/`Scenes`, bloopers and other → `-other`/`Other`). The scan never relabels a row that exists; the classifier runs only for files with no row.
- Manual assign: the assignment records the type of the profile on the download row (user-owned state wins; a person who assigns a file says what it is). `update_profile_id(..., video_type=)`.
- quiv: `quiv.run_subprocess()` replaces `subprocess.run` for yt-dlp, ffmpeg and ffprobe in this phase, so a cancel stops the child.

Deviations from the plan as written, with the reason:

1. **W1 inference (decision 2).** The migration relabels only downloads with `profile_id = 0` from their names. A download that a profile owns keeps `trailer`, because its profile is a trailer profile and the two must agree or the profile downloads again. Instead, **a profile that changes its `video_type` relabels its own downloads** (`_relabel_downloads` in `database/manager/trailerprofile/update.py`). This gives zero unexpected downloads at upgrade AND when the user switches a hacky profile, which the plan's "relabel rows whose owning profile looks hacky" did not: it left the profile unsatisfied until the user acted.
2. **W4 gate.** The "skip media with unresolved unattributed downloads" gate is NOT implemented. With type-aware claiming, the common case is a Plex library with a `Featurettes/` folder and no featurette profile: every such movie has an unattributed featurette, and the gate would stop every trailer download in the library. A same-type unclaimable file cannot coexist with a pending profile (the claim would take it), so the narrow gate is a no-op. The unattributed file is surfaced on the media details page and stays for Phase 11's `unattributed-download` issue. Maintainer to confirm before Phase 11 re-expresses gating.
3. **Delete Trailers.** `services/media.delete_trailers` deletes the downloads of type `trailer` only; a featurette or a clip is deleted from its own row on the media details page. The action keeps its name.
4. **Per-profile skip** ("Which videos on disk a download skips"): done as recommended, one branch in `download_trailer`. `video_count` is left to Phase 10 or later.
5. **Nudge (decision 7)** is a `once` startup pass `video-type-nudge-v0.14.0` (`tasks/profile_nudge.py`), log only.
