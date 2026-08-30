# Hygiene Backlog

Small, non-blocking cleanups. Fold each into whichever release touches the area anyway;
none justify their own release. Check items off with the release that shipped them.

- [x] **H1 — API error-handling standardization** — DONE (Phase 7 Stage B, ships in
  v0.12.0). Eighteen handlers caught every exception and answered 404 with `str(e)`.
  `api/v1/errors.py` now holds the mapping: a missing item is a 404, an exception whose
  message is written for the user keeps it (ConnectionError, ConnectionTimeoutError,
  InvalidResponseError, ItemExistsError, FolderNotFoundError, FolderPathEmptyError,
  ValueError), and anything else is logged with its traceback and answered with a line
  naming only the action. The spec documents the new 500s in its own commit — 18 added
  500s plus 2 previously-undocumented 404s, no removals.

  Two things worth keeping: "Connection refused" is the *answer* for Test Connection and
  the Connection Doctor, so those keep their message and their 400 — a blanket
  genericization would have broken the feature. And `except Exception` catches
  HTTPException too, so the mapper returns a deliberate one untouched; without that the
  406 from `update_yt_id` would have become a 500.

  The first attempt shipped a NameError: `connections.py` had no module-level logger,
  so every failing connection request returned a blank 500 and logged nothing — and the
  full suite passed, because no test walks those error paths. Found by driving the
  running app. `tests/api/test_error_wiring.py` now parses each module and checks that
  every name passed to the mapper resolves.
- [x] **H2 — Decorative SVG accessibility sweep** — DONE (ships in v0.11.0): 159
  decorative inline SVGs got `aria-hidden="true" focusable="false"`; three icon-only
  buttons gained aria-labels; two stale "Trailer Exists" labels renamed "Downloaded".
- [ ] **H3 — Older API endpoints marked deprecated** (`/media/all` etc.) — actually
  remove at v1.0.0 API freeze.
- [ ] **H4 — the test suite shares one database, and the order matters.** Phase 7
  mirrored the test tree but did not fix this, so the item stays open with a sharper
  description than "update all tests".

  `conftest.pytest_configure` builds one SQLite database for the whole session, and
  every test writes into it. A test that assumes an autoincrement id therefore depends
  on which test ran first. Moving files in Stage A reshuffled pytest's collection order
  and broke `test_connection.py`, which had hardcoded `CONN_ID_1 = 1`; the fix was to
  use the id `create()` returns.

  That was one instance. Any future move, rename or new test file reshuffles the order
  again, and the next instance will look like an unrelated failure. Phases 8 to 10 all
  add tables and tests.

  The fix is a per-test transaction that rolls back, or a fresh database per module.
  Either is a change to `conftest.py` and to the handful of tests that lean on shared
  state — `test_connection.py` notes which ones near the top.
- [x] **H5 — Duplicate `displayTitle` pipes** — DONE (ships in v0.11.0): merged into
  `helpers/display-title.pipe.ts` with a `fieldKey` mode (preserves casing, strips the
  `_at` suffix) so header output is unchanged; `media/pipes/` copy deleted.
- [x] **H6 — `read_all_raw`/`downloads_raw` raw-SQL endpoints** — RESOLVED as a
  settled design decision (July 2026), not a cleanup: raw endpoints stay raw. Data is
  validated when WRITTEN to the database, so re-validating and converting every row
  into typed Python objects at read time (for the frontend or external API consumers)
  would only add memory pressure and slow responses on large libraries — raw reads
  are deliberately the efficient list-scale path. Rationale documented in CLAUDE.md
  (Key Conventions); do not convert these to typed responses.
- [x] **H7 — Startup-fix module retirement** — DONE (Phase 3, ships v0.10.2):
  `startup_fixes.py` and its tests deleted with `fix_trailer_exists_flags`
  (justification recorded in `phase-03-dynamic-status.md`).
- [ ] **H8 — Scan TODO comments** ("once the planned Issues section exists…") in
  files-scan → wired and removed in Phase 11.
- [ ] **H9 — `media.youtube_trailer_id` column retirement** once the MediaVideo table
  owns candidates (Phase 9 cleanup; UI "saved trailer id" field becomes a USER-source
  candidate).
- [x] **H11 — Release-fixture gauntlet caught up** — DONE (ships in v0.11.2): the
  ladder's rule-4 fixtures were missing for v0.11.0 and v0.11.1. Added
  `v0_11_0_columns_dropped.sql` (post-destructive-migration schema, migrated
  `has_downloads` filter) and `v0_11_1_plex_linked.sql` (Plex connection + path
  mappings, an Arr↔Plex linked show, and a poisoned library-root row with a
  misattributed trailer). The harness now takes per-fixture media counts and probes
  that a library-root row never captures media under it — verified to fail when the
  guard is removed.
- [ ] **H13 — `_is_path_safe` should use an allowlist** (`api/v1/files.py`). The
  cross-platform bugs are FIXED in v0.11.4; the design point is still open.

  Fixed in v0.11.4: the guard refused **every** path on Windows, because its depth
  check counted `/` characters and a Windows path has none — so a Windows direct
  install (shipped v0.11.1) could list a folder but could not play, read, rename or
  delete a trailer. The prefix match also refused real libraries at `/variable/media`
  or `/usr-data/media` for merely starting with an unsafe string, and a relative path
  was judged by wherever the process happened to be running. It now compares whole
  path components with `PurePath`, matches Windows system folders by name under the
  drive, counts components rather than slashes, and refuses relative paths outright.
  Covered by `tests/api/test_files_path_safety.py` (34 tests), which fail against the
  old implementation in 8 places.

  Still open: it remains a **denylist** of system folders. An allowlist built from the
  connection root folders (plus the log folder, which `/files/read` needs) would be
  stronger — Trailarr already knows where its media lives. `Path.resolve()` with
  `Path.is_relative_to()` is the tool. Kept out of the v0.11.4 patch on purpose: an
  allowlist can refuse a path that works today, which is not a change to make inside a
  release that is already in its PR.

  Also still open: `get_files_simple(path)` takes a caller path and lists it with **no
  check at all**. Applying the current guard there would break the folder browser,
  which legitimately lists shallow paths such as `/media/movies` that the depth
  heuristic refuses. Fix it together with the allowlist, which does not need a depth
  heuristic.

- [ ] **H14 — retire the bracketed-id fallback in the log handler.** Every backend log
  line now passes the media id with `logger.media(id)`, so the fallback in
  `config/logs/db_handler.py` — take the first `[123]` in the message as the media id —
  only serves logs from libraries, and it is what linked seven lines to the wrong title
  before Phase 7 fixed them.

  Not removed yet on purpose: a line that has not been converted would lose its link
  with no fallback, and third-party logs would never link again. Revisit once the
  explicit tag has shipped in a release or two.
  `tests/test_log_message_safety.py` already forbids a bracketed non-media id, so the
  risk of a new wrong link is small; the remaining question is only what the fallback
  still earns.

- [ ] **H15 — a failing batch delete tells the user twice.** `batch_update_media` with
  the delete action calls the same code the delete endpoint uses, which broadcasts
  "Error deleting trailer!" on a failure. The batch handler then catches the same
  exception and broadcasts "Error updating Media!". The user sees both.

  Phase 7 kept it: Stage B does not change behavior. Pick one message when something
  else touches that handler.

- [ ] **H16 — `api/v1/media.py` still holds logic.** Stage B extracted the three
  heaviest handlers (delete trailers, set YouTube id, set monitoring) and the bulk
  monitor path, taking the file from 739 lines to 691. The read handlers still build
  their own filters and shape their own responses.

  Not urgent: what is left is closer to "parse, call, return" than the rest was. Do it
  when Phase 9 or 10 touches this router anyway.

- [ ] **H17 — a register of strings that are contract, not prose.** Phase 7 rewrote
  every log message, and three sets of strings had to be left alone because something
  reads them. They are recorded here so the next prose pass does not have to rediscover
  them, and so nobody "improves" one:

  - `exceptions.py` — the message of `ItemNotFoundError` is returned as the 404 detail
    and is asserted in tests. It is API, not prose.
  - The yt-dlp and FFmpeg failure text in `services/trailers/video_v2.py` — fed to
    `classify_ytdlp_error`, which matches fragments such as "please sign in" and
    "login required". A reword can make a message start matching a signature it does
    not match today, and change the reason the user is shown.
  - `"YT-DLP Output::"` and `"FFMPEG Output::"` — `config/logs/db_handler.py` matches
    these to move the tool output into the traceback column and replace the message.
    Rewording either puts a wall of ffmpeg output back on the Logs page.

  Worth turning into a test that asserts each string still exists.

- [ ] **H18 — dead code with an expired removal note.** `database/engine.py` carries a
  commented-out `manage_session` decorator under "Remove in v0.8.0!". The version is
  v0.12.0. Nothing references it. Delete it.

- [ ] **H19 — a service cannot schedule a task.** `_schedule_refresh` stayed in
  `api/v1/connections.py` during Stage B because it registers a job with the scheduler,
  and a service importing `tasks/` would invert the layering that stage had just
  established.

  That is fine while only a handler needs it. When a service needs to schedule work —
  Phase 8's TMDB refresh is the likely first — invert it the way the event listeners
  were inverted: `tasks/` registers a callable that `services/` can call, rather than
  `services/` importing `tasks/`.

- [ ] **H20 — the DEBUG log lines were not swept.** Stage C rewrote every line at INFO
  and above, which is what a user reads on the Logs page. The 144 DEBUG lines keep their
  old wording. They are for developers, and the effort went where it was read. Fold them
  in whenever a file is open for another reason.

- [x] **H10 — `VACUUM` for logs.db after the daily purge** — DONE (ships in v0.10.0):
  `delete_old_logs` now uses a single batch DELETE + conditional `VACUUM` on an
  autocommit connection (`vacuum_logs_db` in `config/logs/db_utils.py`). Verified at
  50k rows: 13.3 MB → 0.14 MB in 0.32s. trailarr.db VACUUM-after-migrations still
  lands with Phase 5.
