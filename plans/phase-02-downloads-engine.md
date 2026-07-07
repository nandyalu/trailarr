# Phase 2 — Downloads-Driven Download Engine

**Status:** not started · **Release:** v0.10.0 (with `track-apprise-notifications.md`)
**Depends on:** Phase 1 (shipped) · **Blocks:** Phases 3–5

## Objective

The *Download Missing Trailers* task stops deciding from `trailer_exists` and decides
from **download records per profile**: for each monitored media item, download only for
matching profiles that don't already own an active download. Failed downloads back off.
Downloading stops flipping `monitor` off. This kills the #591 bug class structurally and
is the pivot of the whole roadmap.

## Preconditions (verify before starting)

- v0.9.9 released; attribution health warning rate in the wild is low (check issue
  tracker / Discord for "have no tracked download record" reports).
- On a copy of `config-dev`: `SELECT COUNT(*) FROM media WHERE trailer_exists=1 AND id
  NOT IN (SELECT media_id FROM download WHERE file_exists=1)` ≈ 0.
- All 716+ backend tests green on dev.

## Design decisions (settled — do not relitigate)

1. **Satisfaction rule:** profile P is *satisfied* for media M iff a `Download` row
   exists with `media_id=M.id AND profile_id=P.id AND file_exists=True`, OR an
   unattributed (`profile_id=0`, `file_exists=True`) row exists that P may claim
   (claim it on the spot via `download_manager.update_profile_id`, highest-priority
   claimant wins). Only unsatisfied matching profiles are downloaded.
2. **New table `DownloadAttempt`** keyed on `(media_id, profile_id, unit)` with
   `unit: str = "default"` — seasons become units in Phase 10; the key shape is fixed
   NOW to avoid a rework. Columns: `id`, `media_id` (FK, CASCADE), `profile_id` (int,
   NOT an FK — profiles can be deleted; stale rows are pruned lazily), `unit`
   (server_default `'default'`), `attempt_count` (int, default 0), `last_attempt_at`
   (datetime), `last_error` (str, nullable), unique constraint on
   `(media_id, profile_id, unit)`. Additive Alembic migration.
3. **Backoff:** after a FAILED download attempt, next eligible time =
   `last_attempt_at + min(2^(attempt_count-1) days, 7 days)` (1d, 2d, 4d, 7d cap).
   Success deletes the attempt row. Manual downloads (`download_trailer_by_id`, batch
   endpoint) bypass backoff and reset the row on success.
   **Skips are not attempts**: validation failures (missing folder, `wait_for_media`
   unmet, unreachable disk) do NOT increment `attempt_count` — they already have their
   own skip-event dedupe. Only an actual attempted-and-failed download counts.
4. **Monitor is no longer flipped by downloads:** remove the `monitor=False` side effect
   from `update_trailer_exists` (`core/base/database/manager/media/update.py:294-297`).
   `trailer_exists` and `status` keep being *written* (UI still reads them until Phase 3)
   but nothing reads them for download decisions.
5. **`stop_monitoring` is honored this phase** (as "stop after first successful profile
   in this run") but marked deprecated in the UI tooltip. Its fate: Phase 4.
6. **Upgrade guard:** at the start of `download_missing_trailers`, if any media has
   `trailer_exists=True` with zero active download rows AND no full files scan has
   completed since this app version first booted, log a warning, trigger
   `scan_all_media_folders`, and SKIP the download run. Persist "scan completed on
   version X" via a small `app_settings`/task-config flag. This is the only ordering
   guard in the roadmap — without it, upgrades from pre-download-tracking versions
   mass-re-download.
7. **Shadow logging (bake-window instrumentation):** for every (media, profile)
   decision, if the old signal (`trailer_exists`) and the new signal (satisfaction)
   disagree, log one structured line:
   `SIGNAL-DISAGREE media=<id> profile=<id> trailer_exists=<b> satisfied=<b> reason=…`.
   This turns every 0.10.0 install into a correctness audit. Remove in Phase 3.

## Change map

| File | Change |
|---|---|
| `core/base/database/models/downloadattempt.py` | NEW model (+ Read/Create) |
| `core/base/database/manager/downloadattempt/` | NEW manager: `get(media,profile,unit)`, `record_failure`, `clear`, `prune_for_deleted_profiles` |
| `alembic/versions/…` | additive migration (autogenerate, then hand-check) |
| `core/download/trailers/missing.py` | satisfaction filter + claim-on-spot + backoff gate + shadow logging; `_process_single_media_item` records failures/success against attempts |
| `core/download/trailer.py` | on success: clear attempt row; stop relying on status transitions for control flow (keep writes) |
| `core/base/database/manager/media/update.py` | remove monitor-flip side effect (decision 4); `update_monitoring` keeps its guardrails until Phase 4 |
| `core/tasks/files_scan.py` | the `not media.monitor` guards in `_process_trailer_changes` reconciliation can now be REMOVED (their reason — trailer_exists forcing monitor off mid-chain — is gone with decision 4). Reconcile trailer_exists from disk truth unconditionally. |
| `core/tasks/download_trailers.py` | manual/batch paths: bypass backoff, clear attempts on success; batch skip list gains "already satisfied" reason (replaces `trailer_exists` check at line ~144) |
| `core/tasks/schedules.py` | upgrade-guard flag plumbing (if stored in task config) |
| frontend | profile settings: deprecation note on Stop Monitoring; no other UI this phase |
| tests | see Test matrix |

## Execution steps

1. Model + manager + migration for `DownloadAttempt`. Migration on a `config-dev` copy.
2. Satisfaction helper (pure function, heavily unit-tested):
   `unsatisfied_profiles(media, matching_profiles) -> list[profile]` — input is
   `MediaRead` (downloads are eager-loaded on it) + matching profiles; encapsulates
   claim-on-spot decisions but performs no writes (return claims to apply).
3. Wire into `missing.py` with shadow logging. At this commit the task behavior changes.
4. Backoff: gate per (media, profile) before attempting; record failure in the
   `except` path of `_process_single_media_item`; clear on success.
5. Remove monitor-flip; remove files-scan reconcile guards; update the 2 guard-dependent
   tests (`test_stale_trailer_exists_not_corrected_when_monitored`,
   `test_new_trailer_found_while_monitored_records_but_skips_flag`) to assert the NEW
   behavior (reconciles regardless of monitor).
6. Upgrade guard.
7. Manual/batch paths.
8. Full verification protocol; release notes; roadmap page tick.

## Wargame — scenarios that must have deliberate answers

- **S1. Steady state:** all monitored media satisfied → task logs "nothing to do" and
  exits without touching yt-dlp. Verify: run task twice on scratch env; second run
  performs zero downloads (THE phase invariant).
- **S2. Monitored forever:** media with `monitor=True` and satisfied profiles stays
  monitored and is never re-downloaded — the user's "keep monitored forever" workflow.
- **S3. Trailer deleted on disk:** files scan marks download `file_exists=False` →
  profile unsatisfied → next run re-downloads. Wanted behavior; confirm scan→download
  sequencing produces exactly one new download.
- **S4. Unattributed download exists:** media matches Movie Trailers; a `profile_id=0`
  active row exists → claimed, not downloaded. If TWO profiles match and one unattributed
  row exists → highest priority claims it; the other downloads.
- **S5. Profile deleted:** downloads keep the dead `profile_id`. Satisfaction only
  consults *existing* profiles' ids, so dead-profile downloads satisfy nothing → if
  another profile matches, it downloads (per design: deleting a profile un-satisfies).
  Attempt rows for dead profiles: pruned lazily at task start. **Release-note this**:
  deleting a profile whose downloads exist and creating a similar one re-downloads.
- **S6. Profile filters edited:** newly-matching media become pending naturally; media
  no longer matching are simply skipped (downloads kept). No special handling.
- **S7. Profile disabled:** excluded from `enabled_profiles` (existing behavior) — its
  downloads still satisfy it if re-enabled. No attempts accrue while disabled.
- **S8. Failure backoff:** trailer genuinely unfindable (niche film): attempts at 0h,
  +1d, +2d, +4d, then weekly — verify eligibility math with frozen clock; verify
  `last_error` captures the final exception string (truncate to ~500 chars).
- **S9. Manual download during backoff:** user clicks download → bypasses backoff;
  success clears the attempt row so automation is clean again.
- **S10. stop_monitoring=True profile succeeds first:** run breaks after it (legacy
  semantics preserved this phase); other matching profiles stay unsatisfied →
  **they will download on the NEXT run** (previously monitor got flipped off and they
  never ran). ⚠️ This is the *download-volume cliff*: users who relied on
  stop_monitoring + overlapping profiles to get ONE trailer now eventually get one per
  matching profile. Mitigations: shadow logs quantify it; release notes call it out
  loudly; the Phase 4 decision may reintroduce an explicit "first match only" option.
  Wait— verify precisely: with `break`, unsatisfied profiles remain; next run's
  satisfaction check finds them unsatisfied and downloads. If legacy behavior must be
  fully preserved this phase, honoring stop_monitoring must ALSO mark remaining
  profiles as skipped-not-pending. **Decision: preserve legacy volume this phase** —
  when a stop_monitoring profile succeeds, treat remaining matching profiles as
  intentionally-skipped for this media (no download next run) by checking:
  "if any active download for this media belongs to a stop_monitoring=True profile →
  media is fully satisfied". Encode that in the satisfaction helper + tests.
- **S11. Media removed from Arr:** CASCADE deletes downloads and attempt rows — verify
  FK behavior in migration test.
- **S12. Two downloads, same profile:** historical duplicates (e.g. #591 libraries)
  mean multiple active rows with the same profile_id — satisfaction is `any()`, never
  assume uniqueness.
- **S13. Concurrent scan + download task:** scan claims an unattributed row for profile
  P while download task is mid-run with a stale MediaRead → duplicate download for P
  possible ONCE. Acceptable (self-heals: both rows satisfy P; cleanup optional). Do not
  add locking; note in code comment.
- **S14. `wait_for_media` gating:** media file absent → skip (not an attempt) — repeated
  every run by design; confirm skip-event dedupe keeps events quiet.
- **S15. Upgrade from v0.9.6-era install (empty downloads table):** upgrade guard fires,
  full scan runs first, downloads deferred one cycle. Simulate on scratch: media with
  trailer_exists=1, no download rows, real files on disk in tmp folders.
- **S16. Fresh install, empty library:** guard must not loop (no media → healthy).

## Pitfalls (this codebase)

- `missing.py` re-opens `read_all_generator(monitored_only=True)` per outer-loop
  iteration and processes ONE media per pass (memory design). Satisfaction filtering
  must happen inside `_find_matching…`-adjacent code so the "find next actionable
  media" loop skips satisfied media *cheaply* — don't accidentally make each pass O(N)
  downloads queries. `MediaRead.downloads` is already loaded; use it, no extra queries.
- `download_missing_trailers` currently exits early when no enabled profiles — keep.
- `trailer.py` mutates `media.youtube_trailer_id` and calls `__update_media_status`
  with DOWNLOADING/DOWNLOADED/MISSING; do NOT remove those writes yet (UI reads status
  until Phase 3) — only their *side effects on monitor* go.
- SQLite migration: additive table is safe; still test `alembic upgrade head` +
  `downgrade -1` on a config-dev copy.
- Tests that seeded `monitor=False` expectations after downloads
  (search for `monitor` assertions in `tests/core/download/`) will need updates.
- `EventType`: add `DOWNLOAD_FAILED`? NO — events already have DOWNLOAD_SKIPPED and the
  Events log would flood; attempt rows are the failure record. (Notifications track
  reads events, so failures reaching notifications wait for Phase 11 issues.)

## Test matrix

- Unit: satisfaction helper (S1–S7, S10, S12 as table-driven cases).
- Unit: backoff eligibility math (frozen datetimes), skip-vs-attempt distinction.
- Manager: DownloadAttempt CRUD + unique-key upsert + prune.
- Task-level: two-run idempotency (S1) with mocked downloader; stop_monitoring
  full-satisfaction (S10); upgrade guard (S15/S16).
- Migration: upgrade+downgrade on config-dev copy.
- Update existing: `test_missing_trailers.py`, files-scan guard tests, update.py tests
  asserting monitor flip.

## Verification protocol

1. Full backend suite; frontend build+tests (deprecation note).
2. Scratch env end-to-end: seed movie+series with real dummy trailer files on disk,
   let scan record them, run download task twice → zero downloads; delete a file,
   rescan, task downloads exactly one (mock yt-dlp or use a 2s test video).
3. **config-dev copy soak:** migrate, boot, let attribution + guard + scan + one
   download-task cycle run with yt-dlp download function stubbed to fail-fast; capture
   SIGNAL-DISAGREE lines; count must be explainable (target: 0 unexplained).
4. Kill app mid-task; restart; verify no duplicate attempts / stuck state.

## Rollback / abort

Additive-only schema → rolling back the app binary is safe; attempt table is ignored by
old code. Abort criteria: any S1 idempotency failure, or unexplained SIGNAL-DISAGREE on
config-dev.

## Exit criteria

- Two consecutive task runs on a satisfied library: 0 downloads, 0 writes.
- #591 scenario (monitor=1 + trailer on disk + tracked download) never downloads.
- Shadow-log disagreement rate on config-dev copy: 0 unexplained.
- Release notes (v0.10.0) include: the engine change, the profile-deletion caveat (S5),
  the stop_monitoring preservation note (S10), backoff description.
