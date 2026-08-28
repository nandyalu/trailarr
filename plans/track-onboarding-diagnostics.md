# Parallel Track — Onboarding & Diagnostics ("Setup Doctor")

**Status:** Milestones A+B DONE — merged to `dev` Aug 28, 2026 (PR #658),
shipping in v0.11.4; C–D not started · **Releases:** incremental —
C targets v0.13.x (post-reorg, Nov 2026), D anytime · **Depends on:** nothing hard;
C wants Phase 7 (services layer) and Phase 3 (preview endpoint)

**Milestone A execution notes (Aug 14, 2026):**

- Code lives in `core/diagnostics/` per the pitfalls rule; add to the phase-07 move map
  (`services/diagnostics/`).
- Reports were in-memory only at first. CHANGED Aug 27 (see the review notes below):
  they persist to `diagnostics-reports.json` in `APP_DATA_DIR`. A restart used to empty
  every chip to `NOT CHECKED` and ask the user to run the checks again, which is the
  opposite of what this track is for. Still no DB table: the reports are diagnostics,
  not user data, and a damaged file just means the doctor runs again.
- A1 interpretation: suggestions are made per root and verified against media samples;
  a suggestion corroborated only by the folder-name match IS still offered, but labeled
  "based on the folder name only — check before you apply" (a hard 2-sample minimum
  would leave the common fresh-install single-root case with no suggestion at all).
- Suggester bases: `/` top level (system dirs excluded) plus one level below each, plus
  existing PathMapping targets — which is how deep bases (e.g. `/mnt/user/media`) are
  found when any mapping already exists.
- Suggester stage 1 (added after real-library testing, Aug 15): search the disk for a
  tracked media folder BY NAME (BFS, depth ≤4, 25k-entry budget, likely mounts first)
  and derive the mapping by longest-common-suffix alignment of the remote and found
  paths. Fixes two failures of the shallow heuristic on the maintainer's machine: a
  library 3 levels deep got no suggestion at all, and a folder-name coincidence
  (`/media/movies/all` tail-matching a dir named `all`) produced a wrong one. Spread
  media sampling doubles as union-mount disambiguation: a candidate on one physical
  drive fails some samples while the union mount passes all. Sibling roots reuse the
  first derived mapping without re-searching. The tail heuristic remains as the
  fallback for fresh connections with no synced media.
- Suggestions are ROOT-SCOPED (maintainer decision, Aug 15): `path_from` is always the
  root folder exactly as the application reports it, never a shared shallower prefix —
  path mappings correspond 1:1 with root folders (Plex `plex_section_key` and the
  library-root guard key on them). The shallower alignment stays internal for sibling-
  root reuse. When the root already has a mapping, the suggestion carries
  `updates_existing=True`, the wording says "change to the existing mapping", the UI
  button says "Update mapping", and applying updates that row's target
  (`add_path_mapping` upserts by `path_from`) — no duplicates.
- Wargames A1–A6 each have a test in `tests/core/diagnostics/`; exit criterion verified
  end-to-end in headless Chromium: a wrong-volume setup (Arr reports `/data/*`, library
  elsewhere) got a one-click Apply that flipped the chip to HEALTHY.

**Milestone B execution notes (Aug 14, 2026):**

- Framework in `core/diagnostics/health.py`: every check async with a 10s hard timeout
  (B4); on-demand only, never at startup (B1); report cached 24h in memory.
- Checks: ffmpeg, hardware (surfaces `gpu_available_*`/`gpu_enabled_*`), yt-dlp version
  + channel + update flag, app version, cookies file validity, Connection Doctor
  summary, image-cache writability, disk space (config + sample media mount).
- Cookies UI rides the existing `yt_cookies_path` mechanism (per the VERIFY note — no
  parallel path): upload/paste stores `APP_DATA_DIR/cookies.txt` mode 600 and sets the
  setting; status endpoints never return content (B2, tested); delete removes only the
  Trailarr-managed file, never a user-provided path.
- yt-dlp live test: `--simulate` on yt-dlp's canonical test video, user-confirmed (B3),
  result cached 24h and merged into the report.
- Classified download errors: `core/download/error_classify.py` signatures (sign-in/
  bot-check, 403/429, format-unavailable → JS runtime, video-unavailable, network);
  applied where `DownloadAttempt.last_error` is stored — reason first, raw line in
  brackets. FAQ/docs wording matches (`docs/user-guide/settings/health.md`).
- The plan's "update channel" for yt-dlp reports the existing `ytdlp_nightly` setting;
  switching channels from the UI is NOT included (deliberate scope cut).

**Review changes before merge (Aug 27, 2026):** a maintainer review asked the same
question of every part — where does the app still hand work back to the user? Eleven
changes came out of it. They are recorded here because several revise decisions written
above.

- Doctor reports PERSIST (revises the in-memory note in the Milestone A notes).
- Applying a suggested mapping now also starts a sync of that connection. A correct
  mapping was only half the fix: the library stayed empty until the next scheduled sync.
- The write test runs on EVERY accessible folder, not the first one. A writable movies
  mount next to a read-only TV share used to report healthy.
- `Check all` on the Connections page (`POST /connections/doctor/run-all`).
- The Health `connections` check runs the doctor itself when no report is stored,
  instead of telling the user to go and run it. It gets a 30s timeout (network I/O).
- Health checks run concurrently (`asyncio.gather`). Sequentially, one hung mount cost
  its own timeout plus everyone else's wait.
- Disk space covers every distinct media mount (deduped by `st_dev`, config volume
  excluded), warning under 5 GiB. A full media disk fails downloads with an error that
  never mentions space. The 5 GiB threshold is a judgement call, not a measured one.
- Error signatures added: nsig/player-response (the common breakage when YouTube changes
  its player), age restriction, HTTP 410.
- After saving cookies, the Health page offers `Test them now` — the click is the
  confirmation, so B3 is satisfied without asking twice.
- Background tasks are held in a module-level set; without a strong reference the loop
  can collect a task mid-run, so the post-save check could silently never finish.
- The yt-dlp live test reaps its process after a timeout.

**Doctor on the Add/Edit Connection page (Aug 28, 2026):** the review surfaced that
`POST /connections/` REFUSES a connection Trailarr cannot reach or read, so the doctor
never got to diagnose the very mistake it explains best. `preview_doctor()` now runs the
probes for a connection with no id (`POST /connections/doctor/preview`, with the id
passed when editing so the suggester can corroborate against synced media). Nothing is
stored — no id, no report to keep. On the form, `Find folders` fills in every empty
Trailarr Path it finds; a value the user typed is NEVER overwritten and gets a
suggestion button instead. This partly pre-builds Milestone C step 2 (Doctor inline in
the wizard): the preview endpoint is the piece the wizard needs.

## Objective

Kill the first-hour failure modes that stop users from ever reaching the part of
Trailarr they'd love. Grounded in the all-time most-commented issues: #17 permission
denied (39c), #562/#97/#610 path & detection confusion, #29/#96 yt-dlp auth/cookies,
#258 posters, #116 URL base. Principle: **the app diagnoses itself and tells the user
the fix — no failure may remain silent or cryptic.**

## Milestone A — Connection Doctor (v0.11.x)

Runs automatically after saving a connection + on-demand ("Run check" per connection).

1. **Path visibility probe:** pull up to 5 sample media `folder_path`s (or root folders)
   from the Arr/Plex API; test existence + listability from inside the app.
2. **Mapping suggester:** on failure, diff the Arr-reported path prefixes against the
   container's visible mounts (walk `/` top-level + existing PathMapping rows) and
   propose a concrete `PathMapping` ("Radarr reports `/data/movies/...` — not visible
   here. Suggested mapping: `/data → /media` [Apply]"). Applying creates the PathMapping
   row (model already exists) and re-runs the probe.
3. **Permission probe:** in one accessible sample folder, create+delete
   `.trailarr-write-test`; on failure report the folder's uid/gid/mode vs the process
   uid/gid and the PUID/PGID fix (docs link). This is issue #17, solved at the source.
4. **Result surface:** per-connection status chip (healthy / issues found) on the
   connections settings page + detail dialog with each probe's outcome and fix.

### Wargame (A)

- A1. Multiple root folders with different mounts → probe each root, suggest per-root
  mappings; never suggest from a single sample.
- A2. Silently-empty network mounts (autofs/soft SMB) pass existence checks — reuse
  `_is_disk_available` semantics and label the result "reachable but empty — if this
  library is not empty, your mount may be down" rather than green.
- A3. Plex connections: sections instead of root folders; path mappings per section
  (already modeled via `plex_section_key`) — probe per section.
- A4. Bare-metal installs: no container mismatch, but permission probe still valid;
  mapping suggester should detect "path exists as reported" and short-circuit.
- A5. Windows-style paths from Arr on Docker host (`C:\...`) → detect and explain
  (remote Windows Arr), suggest mapping syntax.
- A6. Probes must be read-only except the write-test file; never touch media files.

## Milestone B — System Health page + first-class cookies (v0.11.x)

New Settings → **Health** page: a checks framework (each check: name, async run,
status, detail, remediation doc link, last-run time). Checks:

- ffmpeg present + version; hardware encoders probe (surface the existing
  `gpu_available_*` detection — today it's invisible, #259/#236/#590 territory).
- yt-dlp version + update channel; **user-triggered** live test download of a known
  tiny video (never automatic — don't hammer YouTube; cache result 24h).
- Cookies: settings UI to upload/paste a cookies.txt (stored in `APP_DATA_DIR`,
  chmod 600), validity indicator, passed to yt-dlp (VERIFY the current cookies
  mechanism from #96's fix first and build the UI on top of it — don't invent a
  parallel path).
- Connections reachability summary (re-uses Milestone A results).
- Poster/image cache sanity (#258 class): images dir writable + sample fetch.
- Disk space on `APP_DATA_DIR` + on a sample media mount.
- App version vs latest (existing update check surfaced here too).

Download-failure surfacing: when yt-dlp errors match known signatures (403, bot-check,
sign-in-required), the attempt's `last_error` (Phase 2) stores a *classified* reason and
UI/logs say "YouTube is rate-limiting or requiring sign-in — set up cookies (link)"
instead of a raw traceback.

### Wargame (B)

- B1. Health checks never block startup; page runs them on demand + daily cached.
- B2. Cookies contain credentials-equivalent tokens: never in logs, masked in API
  (write-only like Apprise URLs), EXCLUDED from diagnostics bundle (Milestone D).
- B3. yt-dlp test download behind a confirm ("this contacts YouTube once").
- B4. All checks degrade gracefully offline (no internet ≠ crash; each check times out
  independently, 10s cap).

## Milestone C — First-run guided setup (v0.13.x, post-reorg)

Wizard shown when the app has zero connections (and re-runnable from Settings → Help):

1. Welcome + what Trailarr does (one screen, not a tour).
2. Add first connection — Connection Doctor runs inline; can't advance with red
   path/permission results without an explicit "I know what I'm doing" skip.
3. Defaults: trailer language (Phase 8 field), keep-or-edit the two default profiles
   (plain-language summary of what they'll do — no filter UI here).
4. First sync runs with progress (websocket), then **preview screen** (Phase 3's
   library-wide pending view): "Trailarr would download N trailers" with the list.
5. Finish = user explicitly enables downloads (see Phase 3 preview-mode setting);
   until then the download task stays in preview.

### Wargame (C)

- C1. Existing installs must NEVER see the wizard (trigger: zero connections AND zero
  media, checked once at boot; dismissible forever).
- C2. Reverse-proxy/URL-base setups: wizard routes/assets must respect URL_BASE
  (#116 class) — test both direct and sub-directory access.
- C3. Wizard abandoned halfway: everything it did is normal state (a connection,
  possibly preview mode on) — resumable, no special partial-state cleanup.
- C4. Huge library first sync (10k items): step 4 shows progress and allows "continue
  in background"; preview paginates.

## Milestone D — Diagnostics bundle (any release)

Button in Settings → About/Health: downloads a zip with sanitized settings (all
secrets/API keys/URLs masked, cookies excluded), health-check results, app/OS/versions,
last ~500 log lines, DB shape stats (row counts only — no titles/paths unless the user
ticks "include library details"). Issue templates updated to request the bundle.

## Pitfalls (track-wide)

- Doctor/health code lives in `services/diagnostics/` (post-reorg) — if Milestone A/B
  ship pre-reorg (v0.11.x), place under `core/diagnostics/` and list it in the
  phase-07 move map.
- Every remediation message links to a specific docs anchor — write/refresh those docs
  pages in the same PR (path mappings, PUID/PGID, cookies, hardware).
- Frontend: one new Health page + connection status chips + wizard (C is the only
  big UI item); follow MD3 conventions; OpenAPI regen per milestone.

## Docs to update (per milestone)

The pitfalls rule ("every remediation message links to a specific docs anchor —
write/refresh those pages in the same PR") is the driver; concretely:

- **A (Connection Doctor):** the remediation anchors it links to must be current:
  `docs/getting-started/01-first-things/radarr-sonarr-volumes.md` (path mappings — the
  suggester's docs link), `docs/getting-started/01-first-things/environment-variables.md`
  + `docs/troubleshooting/common-issues.md` (PUID/PGID, issue #17 class),
  `docs/getting-started/01-first-things/network-drives.md` (A2's "reachable but empty").
  Document the Doctor itself on the connections settings page (status chips, Run check).
- **B (Health page + cookies):** new Health page section under
  `docs/user-guide/settings/`; move/expand the cookies documentation (currently a
  `Yt-dlp Cookies Path` mention in general-settings + FAQ) to cover the upload/paste UI
  and when cookies are needed (bot-check/sign-in errors); refresh
  `docs/getting-started/02-installation/hardware-acceleration.md` for the encoder
  probe surfacing. Classified download-failure messages should match FAQ wording.
- **C (First-run wizard):** `docs/getting-started/` is largely superseded for fresh
  installs — rewrite the flow around the wizard (docs describe what the wizard does
  and the manual path for advanced users); preview-mode default for fresh installs
  documented in general-settings; URL_BASE note in
  `docs/user-guide/reverse-proxy.md` (C2). Update `docs/llms.txt` setup-flow facts
  (it currently describes the manual connection→profile flow).
- **D (Diagnostics bundle):** document under About/Health settings docs + a
  "attach the diagnostics bundle" line in `docs/references/contributing.md` and the
  GitHub issue templates (which the milestone updates anyway).

## Exit criteria (per milestone)

A: MET — a wrong-volume docker-compose setup gets a one-click working mapping;
permission mismatch names the uid/gid fix. Verified end-to-end in headless Chromium and
against the maintainer's real library. The Add/Edit page goes further than the criterion
asked: it fills the mapping in before the connection is saved.
B: MET — health page green on a correct install; each red state names its fix; cookies
configurable in UI. Verified end-to-end on a running app.
C: fresh scratch install → working, previewed, downloads-enabled library without
touching docs. D: bundle attached to a test issue contains zero secrets (grep-verified
in a test).
