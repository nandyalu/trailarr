# Phase 9 — Video Types

**Status:** not started · **Release:** v0.14.0 · **Depends on:** Phases 5 (clean flags),
7 (paths), 8 (TMDB — non-trailer types are TMDB-only by construction).
**Refresh before execution.**

## Objective

Profiles gain a `video_type` (TRAILER default); downloads record theirs. A featurette
can never again masquerade as "the trailer". Non-trailer types resolve exclusively from
TMDB candidates — no YouTube search fallback exists for them, by construction.

## Design decisions (settled)

1. **Enum `VideoType`** (VARCHAR, no migration for future additions):
   TRAILER, TEASER, CLIP, FEATURETTE, BEHIND_THE_SCENES, BLOOPERS, OTHER —
   mirrors TMDB's `type` values + OTHER for search-only/unknown.
2. **Additive migration:** `trailerprofile.video_type` (default 'trailer'),
   `download.video_type` (default 'trailer'), `mediavideo.video_type` already exists
   (Phase 8). One-time inference pass over existing download rows by filename/folder
   conventions: suffixes `-trailer|-teaser|-clip|-featurette|-behindthescenes|-short|
   -scene|-bloopers` and parent folders `Trailers/ Teasers/ Clips/ Featurettes/
   Behind The Scenes/ Bloopers/ Scenes/ Shorts/ Others/` (Plex/Jellyfin extras
   conventions). Unmatched → 'trailer' (status quo, safest).
3. **Satisfaction becomes type-aware:** profile P satisfied iff active download with
   `profile_id=P.id AND video_type=P.video_type` (claiming unattributed rows also
   type-matched). DownloadAttempt key unchanged (profile carries the type).
4. **Scan classification:** `is_trailer_file` generalizes to
   `classify_extra_file(path) -> VideoType | None`; scan records the classified type;
   the trailer-specific ffprobe size heuristics apply to TRAILER only; other types
   trust naming conventions.
5. **Resolution:** TRAILER keeps Phase 8 order incl. search fallback; every other type
   consumes TMDB candidates only (resolver filters `video_type`), and skips media with
   no tmdb_id (Issue feed later).
6. **Naming:** default file naming per type (`…-{video_type}.{ext}` suffix mapping
   matching the conventions above; folder mode maps type → conventional folder name).
   Profile file_name/folder templates gain `{video_type}` token; defaults for NEW
   profiles use it; existing profiles untouched.
7. **Hacky-profile detection (nudge, never forced):** startup one-time check — profiles
   whose `search_query`/`file_name` contain teaser/clip/featurette/behind keywords but
   `video_type=TRAILER` → log + (post-Phase 11: Issue). Suggest the setting; do not
   change it.
8. **UI:** profile editor type dropdown (with "TMDB-only" hint for non-trailer);
   downloads section + matrix show a type badge; "Known videos" list (Phase 8) gains a
   type column and becomes the picker for USER-source candidates.

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
- W4. Mixed-type unattributed downloads + claim pass: type-aware claiming must not
  assign a teaser file to a trailer profile (extends v0.9.9 attribution logic).
- W5. Type added to `EventType`-style VARCHAR enum later: no migration — verified by
  design.

## Pitfalls

- `get_trailer_paths`/`check_trailer_exists`-era helpers and the cleanup task
  (`trailer_cleanup`) assume "trailer" naming — sweep `services/files` + scan for
  hardcoded 'trailer' strings.
- The delete-trailers API/UI actions ("Delete trailer") must scope by type or rename to
  "Delete videos" with a picker — decide at execution with maintainer (UX).
- Frontend filter family (Phase 6): add `download_video_type` to the virtual fields —
  small, do it here.
- OpenAPI + client regen; docs (profiles settings pages get a Video Type section).

## Verification

Classifier table tests (all conventions × case variants); satisfaction type-matrix
tests; scratch env: profile TEASER on a movie with TMDB teasers → downloads teaser with
correct name; hacky-profile fixture upgrade produces suggestions and NO unexpected
downloads (assert download task dry pass). config-dev copy: inference pass summary
reviewed by maintainer before release.

## Docs to update

- `docs/user-guide/settings/profiles/settings/general.md` (or a dedicated settings
  subpage) — **Video Type** section: the type list, TRAILER-only search fallback
  ("non-trailer types come exclusively from TMDB — they need a TMDB key and a
  `tmdb_id`"), naming/folder conventions per type, the `{video_type}` template token.
- `docs/user-guide/settings/profiles/examples.md` — add a real extras-profile example
  (e.g. Featurettes profile) replacing the keyword-hack pattern users invented.
- `docs/user-guide/settings/profiles/index.md` — the "Trailarr is evolving" help box
  says "Maybe (maybe, no promises!) let the user download Featurettes, Clips, etc." —
  this phase DELIVERS that; rewrite the box.
- `docs/user-guide/library/media-details/index.md` — type badges on downloads/matrix;
  Known-videos type column + USER-candidate picker; the delete action's final UX
  (pitfalls: "Delete trailer" vs "Delete videos" — document whichever is decided).
- **Extras-profile migration guidance** (W1, the mass-download risk): a docs section
  users can be linked to from the startup nudge and release notes — exact steps for
  "I had a hacky featurette profile". Put it in the profiles docs; release notes link
  to the anchor.
- `docs/user-guide/settings/profiles/filters.md` — `download_video_type` added to the
  Phase 6 virtual-field table.
- `docs/troubleshooting/faq.md` — add/refresh "Can Trailarr download extras
  (featurettes, clips, teasers)?" — now yes, per profile video type, TMDB-only.
- Release notes: extras-profile migration guidance leads (exit criteria); roadmap tick.

## Exit criteria

Type-aware satisfaction proven; zero-unexpected-downloads on hacky fixture; Docs
section executed; release notes with the extras-profile migration guidance.
