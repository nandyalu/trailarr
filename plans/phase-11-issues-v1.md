# Phase 11 — Issues Section + v1.0.0 Stabilization

**Status:** not started · **Release:** v1.0.0 · **Depends on:** everything.
**Refresh before execution.**

## Objective

One place that answers "what needs my attention and why" — computed from the same
sources the app acts on, so it can never disagree with behavior. Plus the v1.0.0
stabilization checklist.

## Design decisions (settled)

1. **Issues are COMPUTED, not stored.** Each feed derives live from existing data; the
   only stored state is per-issue **dismissals/snoozes** (small table keyed by a stable
   issue fingerprint: `kind:entity_id[:qualifier]`, with `snoozed_until` nullable).
   Computed-not-stored is the same facts-over-flags principle as the whole roadmap —
   an issue disappears the moment reality is fixed, no reconciliation code.
2. **Feeds (kind → source):**
   - `download-failing` — DownloadAttempt rows ≥3 attempts (last_error shown).
   - `no-candidates` — per-season/typed profiles with empty TMDB candidates (Ph 9/10).
   - `unmatched-monitored` — monitored media matching zero enabled profiles.
   - `unattributed-download` — profile_id=0 active rows (formalizes v0.9.9 banner).
   - `folder-unreachable` — files-scan disk-unavailable skips (the two TODO comments in
     the scan code are wired here) + persistent health-report entries.
   - `missing-tmdb-id` — media where a TMDB-only demand exists but tmdb_id is null.
   - `profile-needs-review` — Ph 10 classification disables + Ph 9 hacky-profile
     detections.
   - `user-video-failing` — USER-source MediaVideo candidates whose downloads keep
     failing (video deleted/blocked) — user intent is reported on, never discarded.
3. **API:** `GET /issues` (grouped, counts, dismissal state) + dismiss/snooze endpoints.
   The v0.9.9 media-page banner generalizes: topnav badge with total count; new
   **Issues** page (sidenav) grouping by kind with per-item deep links (media details,
   profile editor) and actions (assign profile, dismiss, snooze 30d).
4. **Notifications:** issue transitions (new issue appeared) dispatch through the
   Apprise channels — new "Issues" pseudo-event-type subscription; batched like
   everything else (`#trailarr-issues` use case).
5. **Performance:** feeds computed on request with a short in-process cache (60s);
   heavy feeds (unmatched-monitored needs profile matching across the library) reuse
   the satisfaction helper and must stay <1s on 1,700 items — measure; precompute
   during the download task run if needed (it already walks the same data).

## v1.0.0 delight items (ship with the RC — small, high-joy)

- **Library coverage dashboard strip** on home: "N% of movies have trailers · M
  downloaded this month · K need attention (→ Issues)". Computed from existing
  stats + Issues counts; one component, no new endpoints beyond a stats extension.
- **In-UI trailer playback:** the `/api/v1/files/video` streaming endpoint (range
  support) already exists — verify whether media-details files view already plays
  trailers in-browser; if not, add click-to-play on download rows (native `<video>`,
  no player dependency). Single most joy-per-line-of-code feature available.

## v1.0.0 stabilization checklist (own milestone, after Issues ships in an RC)

- Migration gauntlet: fresh, v0.9.6, v0.9.9, each 0.1x → v1.0.0 on fixture DBs +
  config-dev copy.
- Perf pass on 1,700+ items: list load, scan cycle, download-task pass, Issues page.
- Docs audit: every settings page current, roadmap page rewritten as "delivered",
  README/index sync.
- Deprecation sweep: dead flags/env vars, commented-out code blocks from phases 2–10.
- API freeze note: declare /api/v1 stable at v1.0.0.
- Issue-tracker triage: close everything fixed along the way with release references
  (#591-class), label the remainder.

## Wargame

- W1. Issue storm on first upgrade (old library: hundreds of failing/unattributed):
  page groups + counts (not 500 rows); notifications batch to one summary.
- W2. Dismiss vs fix: dismissed issue whose reality resolves → fingerprint disappears;
  reappears later → dismissal persists? Decision: dismissal is per-fingerprint and
  permanent until "un-dismiss"; snooze is time-bound. Both listed under a "Dismissed"
  collapsible.
- W3. Feed disagreement with behavior = bug by definition — parity tests: every feed's
  fixture also asserts the corresponding behavior (e.g. unmatched-monitored media is
  indeed skipped by the download task).
- W4. Empty state: zero issues → celebratory empty page (this is the v1.0.0 trust
  moment — design it well).

## Docs to update

- **New Issues page docs** under `docs/user-guide/` (+ `mkdocs.yml` nav entry): every
  feed kind with its meaning and the fix it points to, dismiss vs snooze semantics
  (W2), the topnav badge, and the "zero issues" state.
- `docs/user-guide/settings/notifications.md` — the Issues event-type subscription
  (`#trailarr-issues` use case from the Apprise track's objective).
- `docs/troubleshooting/` — Issues absorbs several troubleshooting flows
  (unattributed downloads, folder-unreachable, failing downloads): cross-link
  common-issues/FAQ entries to the Issues page rather than duplicating diagnosis steps;
  prune entries the app now self-diagnoses.
- Delight items: coverage strip (home docs in `docs/user-guide/general/index.md`) and
  in-UI playback (media-details files section) if shipped.
- **v1.0.0 docs audit** (already in the stabilization checklist: "every settings page
  current, roadmap page rewritten as delivered, README/index sync") — explicitly
  include: `docs/llms.txt` full re-verification (commands, ports, links), a stale-claim
  grep for every term retired by Phases 2–10, and the getting-started flow walked
  end-to-end against a fresh v1.0.0 install.
- Release notes: the arc story (exit criteria); API freeze note (/api/v1 stable).

## Exit criteria

All feeds live + tested + linked-actions working; badge/count accurate; Apprise issues
channel demo; stabilization checklist complete (docs audit included); roadmap page
marked delivered; v1.0.0 release notes tell the whole arc's story.
