# Phase 10 — Movie/Series Profiles + Season Trailers

**Status:** not started · **Release:** v0.15.0 · **Depends on:** Phases 8, 9.
**Refresh before execution.** This is the release with the accepted breaking change.

## Objective

Profiles become explicitly for movies or series (`for_movies: bool` — maintainer's
decision over a BOTH enum, accepting a one-time classification migration). Series
profiles may enable per-season trailers: one trailer per season up to `season_count`,
TMDB-sourced only.

## Design decisions (settled)

1. **`trailerprofile.for_movies` (bool, no BOTH)** + classification migration:
   - Profile has `is_movie` customfilter condition → classify from its value (and
     REMOVE that filter row — now redundant).
   - Else name/filter keyword heuristics: movie/film → movies; series/tv/show/season
     → series.
   - Unclassifiable → `for_movies=True` AND `enabled=False`, surfaced prominently
     (startup log + release notes + Phase 11 Issue "profile needs review") for the user
     to set correctly and re-enable. **Disabling is the breaking part — loud comms.**
2. **Matching:** `for_movies` gates before customfilter evaluation (and before
   attribution matching). The `is_movie` filter field stays valid for VIEW filters,
   removed from profile-filter validation.
3. **`per_season: bool`** on series profiles (UI hidden/disabled for movie profiles).
   Units: seasons `1..media.season_count` (skip 0/specials). `season_count` grows →
   new pending units appear automatically (feature); shrinks → orphan-season downloads
   kept, never re-downloaded (units only ever *demand*, satisfaction is per existing
   unit).
4. **`download.season_number`** (nullable int, additive). Satisfaction for per-season
   profiles: per unit `(profile, season=N)` an active download with that
   `season_number`. DownloadAttempt `unit` finally carries `"s<NN>"` values — the
   Phase 2 key shape pays off; no migration.
5. **Resolution: TMDB season videos ONLY** (`/tv/{tmdb_id}/season/{n}/videos`,
   candidates stored with `season=N`) — **no YouTube search fallback** (maintainer
   decision). Missing tmdb_id → profile pending, Issue feed.
6. **Naming/placement:** decide at execution after checking current player conventions
   (Plex/Jellyfin season-trailer support); default proposal: media-folder `Trailers/`
   with `Season {season_number:02d}` prefix; templates gain `{season_number}`.
7. Season-video refresh calls are gated to media matched by an enabled per-season
   profile (protects TMDB quota — a 500-series library × seasons is the cost center).
8. **Profile presets + import/export** (adoption item, added July 2026): profiles
   export/import as JSON (customfilter + settings, minus ids), plus a small built-in
   preset gallery ("Compact 1080p", "Original language", "Extras pack") selectable in
   the profile-create flow. Timed here because the profile schema is final after this
   phase (video_type, for_movies, per_season, language all exist). Import validates
   against current schema and reports what it created; version-stamp the JSON for
   forward compat.

## Wargame

- W1. Default profiles ("Movie Trailers"/"Series Trailers") classify cleanly via their
  `is_movie` filters — migration test asserts 0 disabled profiles on a default DB.
- W2. User's single match-all profile (no is_movie filter, generic name) → disabled ⚠️
  — the loudest scenario; release notes must lead with it ("you may need to duplicate
  it into a movie + a series profile"). Consider a migration special case: if the
  library has BOTH movies and series and the profile matched both, auto-duplicate into
  two enabled profiles (suffix " (Movies)"/" (Series)") instead of disabling — decide
  with maintainer at execution; plan default = disable, don't auto-duplicate.
- W3. Anime/specials: season 0 skipped by design; document.
- W4. `season_count=0` series (announced shows): zero units → nothing pending. Good.
- W5. A season with no TMDB videos: pending forever with "no candidates" long-cadence
  state (from Phase 9 W3) — Issues surface it; no retry storm.
- W6. Attribution/claiming with seasons: unattributed season files (users with existing
  season-trailer collections) — classifier needs season detection from filename
  (`Season 01`, `S01`) to claim into `(profile, season)`; else leave unattributed.
- W7. Media flips movie↔series (rare Arr edge): downloads keep season numbers; matching
  changes; no crash — test.

## Pitfalls

- Every `find_matching_profiles` call site gains the for_movies gate — one helper, not
  scattered checks.
- Season-unit expansion must not explode the pending endpoint/matrix UI for 30-season
  shows — matrix groups per profile with a season sub-list, collapsed by default.
- Batch download endpoints take profile ids — per-season batch semantics defined
  (download all missing units).
- OpenAPI/client regen; filter validation changes; docs (profiles + a new season
  trailers page).

## Verification

Migration matrix incl. W1/W2 fixtures + config-dev copy (maintainer reviews the
classification report before release); scratch: series with 3 seasons + TMDB key →
3 downloads with correct names; growth test (bump season_count → 1 new pending unit).

## Exit criteria

Classification report clean on config-dev; season satisfaction idempotent (two runs →
zero repeat downloads); breaking-change comms in release notes + roadmap page updated.
