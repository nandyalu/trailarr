# Parallel Track — Upgrade To TMDB Trailer

**Status:** DONE (v0.13.1, Oct 4 2026, PR #696) · **Release:** v0.13.1 · **Depends on:** Phase 8 (TMDB, shipped
v0.13.0)

After v0.13.0, users asked how to rebuild an existing library with TMDB trailers. Nothing
did it well:

- **Batch Download** excludes every video already on disk, so a title whose trailer IS
  TMDB's first choice gets TMDB's *second* choice. The old file stays, and the new one
  lands next to it as `… Trailer 2-trailer.mkv`.
- **Batch Delete + Download Missing** downloads everything again, including trailers that
  already are TMDB trailers, and titles TMDB lists nothing for get a fresh search result.

Measured on the library copy (200 random downloaded movies, real TMDB key, Sep 29, 2026):
36% have no TMDB trailer at all, 44% already have a TMDB trailer (32% exactly TMDB's
first choice), and **about 20% would really change**. Separately, 810 of 2,789 titles
with a trailer have no known video id (`unknown0000` — files claimed from disk).

## Objective

A profile setting that replaces a trailer with a TMDB trailer only when the current one
is not a TMDB trailer — as part of the normal Download Missing Trailers task, with no
separate action to run.

## Design decisions (settled with the maintainer, Sep 29, 2026)

1. **Two profile columns** (additive migration, both default so an upgrade changes
   nothing): `upgrade_to_tmdb` (bool, default False) and `delete_replaced_trailer`
   (bool, default True — the user decides whether the old file stays).
2. **A match is any TMDB trailer in the profile's language**, not only TMDB's first
   choice. Requiring the first choice would replace files again every time TMDB
   reorders its list or adds a trailer. The language is the profile's
   `effective_language` — the same filter the resolver applies.
3. **A video the user chose (USER row) also counts as a match**, and is a replacement
   target. It outranks TMDB in the resolver already, and a video the user chose is
   never something to replace.
4. **A download with no known video id is not a match.** Nothing proves it is a TMDB
   trailer. **Amended Oct 1, 2026:** it is replaced only when the new profile setting
   `Replace Unknown Videos` (`replace_unknown_videos`, default False) is on. 810 of
   2,789 trailers in the measured library have no known id, and most came from the
   Radarr id, which is TMDB's, so replacing them all re-downloaded a third of a library
   for nothing. With the setting off, the trailer stays and the pending view says why
   (`upgrade_state="unknown_kept"`); `_downloads_to_replace` also leaves such a file
   out when the profile replaces a known non-TMDB trailer next to it.
5. **Satisfaction owns the rule.** `evaluate_satisfaction` takes the media item's
   USER/TMDB trailer rows. An upgrade profile whose own downloads include no match, and
   for which targets exist, is **unsatisfied** (`upgrade=True` in its detail). One rule
   feeds the download task, the pending view and the refresh task, as Phase 3 requires.
6. **No targets means satisfied.** When TMDB was never asked, or lists nothing in the
   profile's language, the current trailer stays. The detail carries
   `awaiting_tmdb=True`, so the refresh task asks TMDB about it (7-day TTL).
7. **A replacement never searches.** It tries USER/TMDB targets only. A search result is
   not a TMDB trailer, so replacing with one would replace again on every run — a
   download loop (#591 class).
8. **A replacement ignores Skip If Plex Has A Trailer.** Plex has a trailer because
   Trailarr put the old one there.
9. **The old file is deleted only after the new one is recorded**, and only the active
   downloads of THIS profile. A failed replacement keeps the old file and records a
   failed attempt (Phase 2 backoff applies).
10. **Manual and batch downloads are unchanged.** Only the Download Missing Trailers
    task replaces; `download_trailer(..., upgrade=True)` is passed from there alone.
11. **Inert without a TMDB key or with Always Search on.** Always Search takes nothing
    from the table, so there is no TMDB trailer to upgrade to. The UI disables the
    setting in both cases and says why.

## Wargame

- W1. TMDB never asked about a satisfied title: satisfied + `awaiting_tmdb` → the Refresh
  Video Lists task asks (200 per run) → next download run replaces. First pass over a
  large library takes days at the cap; running the task by hand speeds it up.
- W2. TMDB list refreshed between satisfaction and download (lazy refresh in
  `_process_single_media_item`): `download_trailer` re-checks the targets after the
  refresh. Current trailer now matches, or no targets left → return False, no attempt.
- W3. Every TMDB target fails (deleted, too short): DownloadFailedError → backoff; old
  file kept. The resolver's `last_video_id` rotates targets across runs.
- W4. TMDB later drops the trailer Trailarr downloaded: the profile is unsatisfied again
  and replaces once with a listed trailer. Rare; accepted.
- W5. User changes the profile language (en → it): every upgrade title with an English
  trailer is replaced by an Italian one when TMDB lists one. Intended — documented.
- W6. `delete_replaced_trailer=False`: the profile owns two active downloads; one
  matches, so it is satisfied and never replaces again.
- W7. Two profiles on one title: each checks only its own downloads; one profile
  deleting its replaced file never touches the other's.
- W8. A claimed unattributed file: the claim is applied, then the same TMDB check runs
  on it — a claimed non-TMDB file is replaced.

## Verification

Full suites; table-driven satisfaction tests for decisions 2–6 and W6/W8; download-path
tests for decisions 7–9 and W2/W3; a real run on a migrated scratch copy of the library
with a real TMDB key: counts from the pending view against the measurement above, one
real replacement end to end with both settings of `delete_replaced_trailer`.

## Docs

- Profile general settings: both fields.
- TMDB page: "Upgrade an existing library" section.
- Release notes v0.13.1 (ask the maintainer).

## Where this track stands (Sep 29, 2026)

Implemented as designed. 2,112 backend and 147 frontend tests pass (new:
`test_satisfaction_upgrade.py`, `test_trailer_upgrade.py`, upgrade cases in
`test_pending.py`).

Verified on a migrated scratch copy of the library with a real TMDB key:

- 200 monitored movies with trailers. The real Refresh Video Lists task found 195
  through `media_awaiting_tmdb` (W1) and asked TMDB about each. After it: 49 upgrades
  (23 with an unknown video id), 82 awaiting TMDB, 64 already TMDB, **0 plain
  downloads**. The pending view matched a raw SQL count exactly.
- Three real YouTube replacements through `download_missing_trailers`: delete on with a
  legacy file name (new file took the profile's name), delete off (both files kept, W6
  held on the next run), delete on with the profile's name (new file took the old name
  back). Events read TRAILER_DOWNLOADED, then TRAILER_DELETED "Replaced by a TMDB
  trailer". A second run attempted nothing.
- Profile page in the real app (headless Chromium): both fields persist, the upgrade is
  disabled with Always Search on and says why, no console errors.

## Review follow-ups (Oct 1, 2026)

Copilot's review of #696 and a pitfalls pass changed the following, all on dev before
the release:

- A video the user chose is kept in any language (`upgrade_keeps`), and the old file is
  deleted only after the new download is recorded (`record_new_trailer_download` returns
  a bool).
- An upgrade leaves out only its own replaced trailers, not every video on disk for the
  item. With the old rule, a profile whose only TMDB target another profile owned had
  no target, and an upgrade never searches, so it backed off on every run (W9).
- An upgrade that is on but inert (Always Search on, or no key) does not set
  `awaiting_tmdb`: `resolver.upgrade_enabled()` is the one place that says when the
  upgrade can act. The refresh task was asking TMDB about the whole library weekly.
- `ProfileSatisfaction.upgrade_state` (`replace_not_tmdb`, `replace_unknown`,
  `matched`, `awaiting_tmdb`, `unknown_kept`) feeds the pending view and the preview
  list, and `MediaPendingView` carries `has_tmdb_id` and `tmdb_asked`, so the media
  details page says why a trailer is replaced or kept. `awaiting_tmdb` was invisible
  before: a user saw "satisfied" for a search trailer and no reason.
- Decision 4 amended: `Replace Unknown Videos`, off by default (migration
  `65e07a32e5d9`).
- The error of an upgrade with no target left reads "No TMDB trailer of 'X' could be
  downloaded, so the current trailer stays", not "No trailer found".
- The escape hatch is documented: paste the YouTube link of the trailer to keep.
- Items that fail on two runs or more show in a library banner with a `Failing
  Downloads` quick filter (`GET /media/failing`, `compute_failing_downloads`), and the
  Download Profiles row shows the last error instead of hiding it in a hover title.
  This is a first slice of the Phase 11 Issues section.

**Phase 9 note:** `upgrade_targets` and `_check_upgrade` compare trailers only. When
profiles gain `video_type`, the match must use the profile's type, or a featurette
profile would "upgrade" to a trailer.
