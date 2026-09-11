# Phase 8 — TMDB Integration

**Status:** IN PROGRESS (Sep 11, 2026, branch `feat/phase8-tmdb`) — the backbone is
built, tested and verified against the live TMDB API and a copy of the 3,704-title
library. See "Where this phase stands" at the end of this file. · **Release:** v0.13.0,
target Nov 2026 · **Depends on:** Phase 7 (shipped in v0.12.0)

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
5. **Arr ids migrate into the table:** sync writes `youtube_trailer_id` (⚠️ **only
   Radarr provides it** — see the correction below; the Sonarr parser carries the field
   to match the shared shape and it is always empty) as ARR rows. ⚠️ **The one-time
   migration does not label them**: the column cannot say where its id came from, so
   every migrated row is a SEARCH row and the first sync promotes the ids the Arr
   really reports. The user-edit heuristic below is dropped with it; one-time migration copies
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

  ⚠️ **Resolved as: skip SEARCH *and* ARR, keep USER and TMDB.** Reading the pitfall as
  "keep everything but SEARCH" left the Arr id in, which reverses what the setting is
  for. Before this phase it set `media.youtube_trailer_id` to None, so the Arr id was
  exactly what it discarded, and people turn it on because Radarr reports one trailer,
  usually English, and they want another — most often one in their own language.
  Keeping the Arr id would have handed them the trailer they turned the setting on to
  avoid. TMDB stays, because it lists a trailer per language and answers that need
  properly, which is also what makes the profile `language` field load-bearing rather
  than cosmetic.
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

## Docs to update

- **TMDB setup docs** (exit-criteria deliverable): where to get an API key, pasting it
  in Settings → General, what changes with/without a key. Home:
  `docs/user-guide/settings/general-settings/index.md` (the key field) + a setup
  walkthrough section either there or under `docs/getting-started/` — decide by size.
- `docs/user-guide/settings/profiles/…` — the new profile `language` field (general
  settings page of profiles docs) and how language interacts with resolution order
  (profile language → en → any official → ARR → search).
- `docs/user-guide/library/media-details/index.md` — "Known videos" list and the
  **Add video** flow replacing "edit YouTube id" (USER rows: never touched by
  automation, highest precedence, kept even when failing).
- `docs/troubleshooting/faq.md` — the "incorrect trailer" answer walks through editing
  the youtube trailer link: rewrite for the Add-video flow. ⚠️ That answer also claims
  "Sonarr does not provide a youtube trailer link" — decision 5 says both Radarr AND
  Sonarr provide it; verify against the parsers and fix the FAQ regardless.
- `docs/getting-started/01-first-things/environment-variables.md` — `tmdb_api_key` if
  persisted to `.env` like other settings.
- Missing `tmdb_id` guidance (decision 6): docs explain fixing TVDB linkage — put it
  in the TMDB setup page's troubleshooting subsection.
- `docs/llms.txt` — add the TMDB key to the setup-flow facts if it becomes a
  recommended setup step.
- Release notes: key-setup walkthrough (exit criteria), `always_search` semantics
  change (pitfalls); roadmap tick.

## Exit criteria

Trailer resolution provably prefers TMDB (log line per resolution source); no key = no
behavior change; candidates visible on media details; Docs section executed (TMDB setup
page live) + roadmap tick; release notes with key-setup walkthrough.

---

## Where this phase stands (Sep 11, 2026)

Branch `feat/phase8-tmdb`, 11 commits. 1734 backend tests and 138 frontend tests pass.

### Done

- **The candidates table.** `MediaVideo` with every column of decision 1, the manager
  that owns the source rules, and the migration that moves `media.youtube_trailer_id`
  into ARR rows. Verified on a copy of the real library: 2,560 ids moved in 1.1s, none
  left behind, no orphan rows.
- **The TMDB client** (`services/tmdb/`), the mapping to candidates, and the refresher.
  Live-verified against api.themoviedb.org with a real key.
- **Settings and profile.** `tmdb_api_key`, masked in the API and checked against TMDB
  before it is stored; profile `language`.
- **Resolution.** `get_video_id` reads the table, in the order USER, TMDB, ARR, SEARCH,
  and searches only when the table offers nothing. A search result is written back.
  `DownloadAttempt.last_video_id` moves a failed candidate to the end of the next run.
- **Population.** Lazy refresh with a 7-day TTL in the download task
  (`media.last_videos_refresh`), plus the `Refresh Video Lists` task every 12 hours,
  capped at 200 items per run.
- **UI and API.** Three endpoints on `/media/{id}/videos`; the Known videos list, the
  TMDB key field and the Trailer Language field.
- **Docs.** The TMDB page, media details, profile settings, the FAQ, the environment
  variables, `llms.txt`, draft v0.13.0 release notes.
- **A real download, end to end.** With a real key against YouTube: the resolver took
  TMDB's first trailer for The Matrix, a 33-second anniversary spot; verification
  rejected it for the 60-second minimum; the retry excluded it and took the next TMDB
  candidate, which downloaded as an 80-second, 3.2 MB file. Candidate iteration is not
  a theoretical case — TMDB marks short spots as trailers, so it earns its keep on the
  first title anyone tries. Documented on the TMDB page.

### Three decisions that the plan got wrong, and why

1. **`include_video_language` is gone from the TMDB reference.** The client asks for
   every video and the resolver picks the language instead. That also keeps the other
   languages, which the resolver wants when the asked language has none.
2. **The order TMDB returns is not useful.** The first four videos of The Matrix are
   featurettes, and the first Inception trailer in TMDB order is not official while two
   official ones follow it. `to_candidates` keeps only trailers, puts official first,
   and keeps the TMDB order inside each group.
3. **Sonarr does not report a YouTube trailer id.** Decision 5 says Radarr and Sonarr
   both provide it, and both parsers do read `youTubeTrailerId`, which is what made the
   claim look true. Sonarr's `SeriesResource` has no trailer property at all, and the
   Sonarr parser carries a comment saying so; the field exists to match the shape the
   rest of Trailarr expects, and it is always empty.

   The cause is the metadata source, which makes it a fact about the two applications
   rather than a gap to fix. Radarr takes its metadata from TMDB, which holds YouTube
   trailer ids, so a Radarr id is a TMDB trailer already — that is also why 1,822 of
   2,104 Arr ids turn out to be the very trailer TMDB lists, and why claiming (item 4)
   matters so much. Sonarr takes its metadata from TVDB, which holds none.

   The library agrees. Every YOUTUBE_ID_CHANGED event written by a sync belongs to
   Radarr media — 177 of them, none for Sonarr — and 98% of the ids stored for Sonarr
   series are exactly the video that was downloaded, against 68% for Radarr. The reason
   is `update_download_facts`, which writes the downloaded video's id back into
   `media.youtube_trailer_id` after every successful download.

   Two consequences. First, the migration cannot label these rows at all. Guessing by
   connection type was still wrong: 1,336 of the 2,462 ids stored for Radarr media are
   one of that item's own downloads, because `update_download_facts` overwrites the
   column, and no column tells those apart from an id Radarr gave. Only the Arr knows,
   and a migration must not ask it — a request to a server that is down would turn an
   upgrade into a failed start. So every migrated row is a SEARCH row, and the sync,
   which runs 30 seconds after start and already writes the Arr id, promotes the ones
   the Arr reports. Verified on the library copy: 2,560 SEARCH rows after the upgrade,
   and 392 of 400 became ARR rows after one simulated sync, the 8 series staying SEARCH.

   The user-edit heuristic of decision 5 goes with it. Its premise — a stored id that
   differs from the Arr's was hand-picked — is the same mistake: a differing id is
   usually Trailarr's own write-back. It would have marked hundreds of rows as the
   user's choice, which is the one label no automation may touch.

   Second, a series has no ARR candidate at all, so Phase 10's season trailers have no
   Arr fallback either.

4. **W6's "the first source keeps the row" is wrong at scale.** On the real library,
   1,822 of 2,104 Arr ids are the trailer TMDB lists — Radarr takes its id from TMDB, so
   agreement is the normal case. Leaving the row with the Arr showed a nameless row and
   sorted the agreed trailer below TMDB's others. A better source now takes the row and
   brings its title, language and official flag. USER rows are never taken.

### Not done

- **Season videos** (`/tv/{id}/season/{n}/videos`). The column and the manager take a
  season; nothing calls it. Phase 10 owns it, as planned.
- **Season videos beyond the column.** Listed above; Phase 10 owns it.
- **The `media.youtube_trailer_id` column** still exists and is still written. H9 in the
  hygiene backlog retires it in Phase 9, as planned.
- **Release notes are a draft** with a TBD date, and the roadmap row says in progress.
