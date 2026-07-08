# Phase 1 — Download ↔ Profile Attribution

**Status: DONE — shipped in v0.9.9 (July 2026).** Kept as a reference: the patterns
established here (shared matching util, startup-pass chaining, scratch-env verification)
are reused by later phases.

## What shipped

- `core/base/utils/profiles.py` — `find_matching_profiles(media, profiles,
  ignore_state_filters=False)` and `pick_profile_for_download(media, profiles, used_ids)`.
  **Critical design point:** attribution ignores `STATE_FILTER_FIELDS = {monitor, status,
  trailer_exists}` because the shipped default profiles filter on `trailer_exists=false`,
  which would never match media that already has a trailer. Any future matching-for-
  ownership must use `ignore_state_filters=True`; matching-for-download must not.
- `core/tasks/download_attribution.py` — startup claim pass (oldest download ↔ highest-
  priority unclaimed matching profile), per-download unclaimed reasons ("no profile
  filters match" vs "all matching profiles already have a download"), then chained
  `fix_trailer_exists_flags()` (order matters: the fix only sees profile-linked
  downloads), then health report (`trailer_exists=True` with zero active downloads).
- Files scan attributes new trailers at scan time; stale downloads (file gone, about to
  be marked deleted) free their profile for the replacement file in the same scan.
- Download manager: `read_unattributed()`, `update_profile_id()`.
- Startup fix covers monitored media too (breaks #591's loop; safe because chains don't
  survive restarts, so `monitor=True` at startup can't mean "chain in progress").
- UI: "Unknown" profile → assign dropdown on Media Details (PUT
  `/media/{id}/downloads/{dl_id}/profile`, `DOWNLOAD_ATTRIBUTED` event); "Unknown
  Profile" quick filter + review banner on media pages (both conditional on count > 0).

## Real-world validation

Maintainer's 292-item library copy: 2,435/2,441 downloads auto-claimed, 6 left with
logged reasons, health check clean. GitHub issue #591 (infinite re-download loop on
network storage) root-cause matches this phase + the disk-availability gate; structural
fix completes in Phase 2.

## Gotchas discovered (do not rediscover)

- CSS `position-try-fallbacks: flip-block` does NOT fire for in-flow anchors on
  scrollable pages in Chromium — popover direction must be set via a class from the
  click handler (see `downloads.component`).
- The UA popover stylesheet sets `inset: 0`; you must reset `inset: auto` before
  anchoring or the box is over-constrained.
- Tests: conftest builds the DB via `create_all` (NO alembic seeds — default profiles are
  absent in unit-test DBs; the scratch env built with `alembic upgrade head` HAS them).
- `EventType` is VARCHAR (`native_enum=False`) but stores the enum **name**
  (`DOWNLOAD_ATTRIBUTED`); the API serializes the **value** (`download_attributed`).
  Frontend `models/event.ts` must be updated for each new type (label + icon + desc).
