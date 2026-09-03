# Hygiene Backlog

Small, non-blocking cleanups. Fold each into whichever release touches the area anyway;
none justify their own release. Check items off with the release that shipped them.

- [ ] **H1 — API error-handling standardization**: all `api/v1` handlers use the
  pattern from `update_download_profile` (ItemNotFoundError→404, unexpected→logged 500
  with generic detail — no `str(e)` leaks, no blanket 404s). Scheduled: Phase 7 Stage B
  (touches every handler anyway).
- [x] **H2 — Decorative SVG accessibility sweep** — DONE (ships in v0.11.0): 159
  decorative inline SVGs got `aria-hidden="true" focusable="false"`; three icon-only
  buttons gained aria-labels; two stale "Trailer Exists" labels renamed "Downloaded".
- [ ] **H3 — Older API endpoints marked deprecated** (`/media/all` etc.) — actually
  remove at v1.0.0 API freeze.
- [ ] **H4 — `tests/conftest.py` TODO** ("Update all tests to current codebase") —
  address during Phase 7 test-tree mirror.
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

- [ ] **H21 — the download task and the pending view scan the library twice, separately.**
  (H14–H20 are reserved by the Phase 7 branch, which has not merged yet — hence the gap.)

  `download/trailers/pending.py:compute_library_pending` and
  `download/trailers/missing.py` run the same scan — monitored media, enabled profiles,
  `find_matching_profiles`, `evaluate_satisfaction`, backoff — over the same rows.
  `pending.py`'s own docstring calls itself "exactly the download task's work list", and
  it already batches the attempt lookup that `missing.py` does per media. They agree
  today by coincidence, not by construction, and Phase 3 wrote `pending.py` to be THE
  single source of truth.

  Extract one generator yielding `(media, claims, unsatisfied, eligible)` and have both
  call it. The one real difference is writes: the download task applies claims, the
  pending view reports them and persists nothing — so the generator yields claims and
  lets the caller decide.

  After v0.11.5 there is a THIRD copy: the sweep design re-verifies each item against
  fresh data immediately before its download, which runs the same chain again inside
  `missing.py`. The scan and the re-verify must agree — a persistent disagreement makes
  the sweep loop propose work it then always skips (W13 in `fix-missing-trailer-scan.md`).
  The unconditional pair-consume keeps that draining, but one implementation is the real
  protection. This is a correctness item, not only a tidiness one.

  Deliberately NOT done in `fix-missing-trailer-scan.md` (v0.11.5): Phase 7 is the single
  big-churn release and it moves both files, so extracting before the reorg lands only
  buys a merge conflict. Do it after v0.12.0.

- [x] **H10 — `VACUUM` for logs.db after the daily purge** — DONE (ships in v0.10.0):
  `delete_old_logs` now uses a single batch DELETE + conditional `VACUUM` on an
  autocommit connection (`vacuum_logs_db` in `config/logs/db_utils.py`). Verified at
  50k rows: 13.3 MB → 0.14 MB in 0.32s. trailarr.db VACUUM-after-migrations still
  lands with Phase 5.
