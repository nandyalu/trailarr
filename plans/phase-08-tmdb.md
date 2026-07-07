# Phase 8 — TMDB Integration

**Status:** not started · **Release:** v0.13.0 · **Depends on:** Phase 7 (paths below are
post-reorg; translate via phase-07 move map if executing earlier)
**Refresh this plan before execution** — verify TMDB API terms/endpoints unchanged.

## Objective

With a user-provided TMDB API key, resolve trailer video ids from TMDB's curated lists
(per-profile language preference) before falling back to Arr-provided ids and YouTube
search. Backbone: the **media-videos candidates table**, which later phases (9, 10)
extend to non-trailer types and seasons. No key configured = behavior identical to today.

## Design decisions (settled)

1. **Table `MediaVideo`** (additive migration; ALL columns from day one):
   `id`, `media_id` (FK CASCADE), `video_id` (YouTube id), `source`
   (ARR|TMDB|SEARCH|USER, VARCHAR), `season` (int, NULL = movie/series-main),
   `video_type` (VARCHAR, default 'trailer' — full enum arrives Phase 9),
   `sequence` (int — order within (media, type, season, language) group),
   `language` (iso_639_1, nullable), `name` (TMDB video title), `official` (bool),
   `published_at` (nullable datetime), `added_at/updated_at`.
   Unique `(media_id, video_id)`.
2. **Refresh semantics:** a refresh task upserts TMDB-sourced rows and prunes
   TMDB-sourced rows TMDB no longer returns; ARR/SEARCH/USER rows persist. Pruning is
   safe: completed downloads carry their own `youtube_id`.
3. **Refresh scheduling:** `media.last_videos_refresh` timestamp (or sidecar);
   staggered periodic task refreshing only media with pending work (unsatisfied
   matching profiles) + lazy TTL fetch (7d) during the download task for others.
   Season-video calls (`/tv/{id}/season/{n}/videos`) only for media matched by a
   per-season profile (Phase 10) — none in this phase.
4. **Consumption order** in the trailer resolver: table candidates filtered
   (type=trailer, season NULL, language=profile.language-else-any) ordered
   USER > TMDB > ARR > SEARCH, then sequence → each candidate passes the existing
   duration/uploader validation → live yt-search fallback last (trailers only), and a
   successful search result is written back as a SEARCH row.
5. **Arr ids migrate into the table:** sync writes `youtube_trailer_id` (Radarr AND
   Sonarr both provide it — `*/data_parser.py`) as ARR rows; one-time migration copies
   existing `media.youtube_trailer_id` → ARR rows. **User-edit recovery heuristic:**
   on the first post-upgrade sync, when the Arr-reported id differs from a migrated
   ARR row's id, relabel that row `USER` — a differing stored id was almost certainly
   hand-picked (mislabeling is benign: slightly higher precedence for an id someone
   deliberately stored). The `media.youtube_trailer_id` column stays until Phase 9
   cleanup (H9) but the resolver reads only the table.
5b. **User-verified videos are a first-class feature (decided 2026-07-06 — keep the
   capability, kill the column):** media details' "edit YouTube id" becomes **Add
   video** (paste URL/id via `extract_youtube_id`) creating a USER row; the "Known
   videos" list supports add/remove of USER rows and a "download this one" action
   (wires into the existing download-with-yt_id flow, recording the USER row).
   USER rows are NEVER written or deleted by any automation (syncs upsert ARR rows
   only; TMDB refresh prunes TMDB rows only — cross-phase invariant #6 in
   `plans/README.md`). A failing USER id backs off per Phase 2
   and falls through to TMDB/search, but the row is kept — Phase 11 surfaces
   "your chosen video is failing" as an Issue instead of discarding user intent.
6. **Missing `tmdb_id`:** skip TMDB resolution, fall through to ARR/search (trailers
   only). No `/find` backfill (Sonarr supplies tmdbId for most series); docs explain
   fixing TVDB linkage for the rest. Media missing tmdb_id where TMDB-only content is
   requested becomes an Issue in Phase 11.
7. **Settings:** `tmdb_api_key` in app settings (persisted `.env`), validated on save
   via a cheap API call; masked in GET responses like other secrets. Profile gains
   `language` (default `en`) — additive column + UI field.
8. **Client:** `services/tmdb/` — thin aiohttp client (the app's existing pattern), 429
   retry-with-backoff, per-run in-memory response cache, api.themoviedb.org/3,
   `include_video_language={lang},en,null`.

## Wargame

- W1. Invalid/revoked key: settings save rejects; runtime 401 → disable TMDB path for
  the run, log once, fall back to search. Never fail the download task.
- W2. TMDB has trailers but none in profile language → fall back: official-en → any
  official → ARR → search. Order tested table-driven.
- W3. TMDB returns Vimeo/other `site` values → filter `site == 'YouTube'` only.
- W4. Rate limits on first full refresh of 1,700 media (~1,700 calls): stagger (e.g.
  ≤40 req/s cap, chunked task run) + refresh-only-pending policy keeps it small.
- W5. Candidate video deleted from YouTube: download fails → attempt/backoff from
  Phase 2 applies per profile, next candidate tried on next run — ensure resolver
  iterates candidates across runs (skip candidates recorded as failed in the attempt's
  last_error? simplest: try next-untried candidate per run; track last tried video_id
  on the attempt row — ADD `last_video_id` column to DownloadAttempt in this phase).
- W6. Duplicate video across sources (ARR id == TMDB id): unique (media_id, video_id)
  → upsert merges; source precedence keeps first-created; fine.
- W7. Media deleted: CASCADE removes rows; profile language edited: resolver-only
  change, no migration.
- W8. User with no key: zero TMDB calls (guard at task/service entry, not per-call).

## Pitfalls

- `always_search` profile flag and `yt_id` manual overrides interact with the resolver
  — manual `yt_id` = USER row (write it) and takes precedence; `always_search=True`
  skips table candidates? NO — redefine: always_search skips only the *stored search
  result reuse*, not TMDB/USER; document in code + release notes.
- `exclude` logic in `trailer.py:257` (excluded previous id when re-searching) is
  superseded by candidate iteration — remove carefully with the tests around it.
- OpenAPI + frontend client regen (settings, profile language field, candidates
  endpoint if the UI lists them — a read-only "Known videos" list on media details is
  in scope: small, feeds Phase 9 picker).

## Verification

Full suites; scratch env with a real TMDB key (maintainer's) resolving a known movie
(e.g. tmdb 603) — assert candidate rows, ordering, and that the downloader received the
TMDB id; key-less scratch run identical to v0.12.0 behavior; config-dev copy: refresh
task on ~50-item slice, inspect rows.

## Exit criteria

Trailer resolution provably prefers TMDB (log line per resolution source); no key = no
behavior change; candidates visible on media details; docs page for TMDB setup + roadmap
tick; release notes with key-setup walkthrough.
