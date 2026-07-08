# Trailarr Roadmap to v1.0.0

This page lays out the path from the current releases to **Trailarr v1.0.0** — a series of small, careful steps that fix the app's longest-standing pain points and add the most-requested features, without disrupting your existing library.

## Why this roadmap exists

Since Trailarr added support for **multiple Trailer Profiles**, a few core concepts haven't kept up:

- **Monitor status is confusing.** Too many things update it — connection syncs, downloads, file scans — and it's very sensitive to trailer downloads. It's hard to understand how *monitoring*, *profiles*, and *downloads* relate to each other, and the app sometimes fights your intent (e.g. turning monitoring off by itself after a download).
- **`trailer_exists` is a single yes/no flag**, but with multiple profiles you can have *several* trailers per media item. One flag can't answer "which profiles already have their trailer, and which are still missing one?"
- **Some of you already work around this** with clever (hacky!) profile setups to download extras like teasers and featurettes — which then get miscounted as "the trailer".

The fix is a simpler mental model:

> **You decide what's monitored. Profiles decide what's wanted. Downloads record what exists. Trailarr downloads whatever is wanted but doesn't exist yet — and shows you exactly why.**

Once monitoring is stable and understandable, the same foundation unlocks **TMDB integration**, **multiple video types** (teasers, clips, featurettes…), and **season-specific trailers** — done properly instead of via workarounds.

## The phases

Each phase ships on its own, is verified against real libraries, and keeps your existing setup working. Version numbers and dates below are **estimates** and may shift as we validate each step — breaking changes (if any) will always be called out in the release notes.

| Version | Target | What's in it |
|---|---|---|
| **v0.9.9** | July 2026 ✅ | Phase 1 — Download ↔ Profile linking |
| **v0.10.0** | August 2026 | Phase 2 — Downloads drive the download engine, plus Notifications (Apprise) |
| **v0.10.1** | September 2026 | Phases 3 & 4 — Live status + monitoring becomes yours |
| **v0.11.0** | late September 2026 | Phase 5 — Cleanup of legacy fields |
| **v0.11.1** | October 2026 | Phase 6 — Filter by downloads & files |
| **v0.12.0** | November 2026 | Phase 7 — Internal reorganization for long-term maintainability |
| **v0.13.0** | December 2026 | Phase 8 — TMDB integration |
| **v0.14.0** | January 2027 | Phase 9 — Video types |
| **v0.15.0** | February 2027 | Phase 10 — Movie/Series profiles + season trailers |
| **v1.0.0** | Q1–Q2 2027 | Phase 11 — Issues section + stabilization |

### Phase 1 — Download ↔ Profile linking — `v0.9.9` ✅

Every downloaded trailer is now linked to the profile that owns it. Trailers found on disk are attributed to your matching profiles automatically, and you can assign a profile manually from **Media Details → Downloads** for anything the app couldn't match. This builds the data foundation everything else stands on.

*What you'll notice:* a one-time startup task, log lines about linked downloads, and a new assign option in Media Details. No behavior changes, no downloads triggered.

### Phase 2 — Downloads drive the download engine — `v0.10.0`

The **Download Missing Trailers** task stops relying on the `trailer_exists` flag. Instead, for every monitored media item it checks: *which profiles match, and which of them already have a download?* Only the genuinely missing ones are downloaded. Failed downloads back off gradually instead of retrying on every run, and downloading no longer switches monitoring off behind your back.

This is the biggest internal change of the roadmap, so it gets a major version bump and **~4 weeks of bake time** before the next phase — please report anything unexpected (wrong re-downloads, skipped items) during this window.

*What you'll notice:* smarter, quieter download runs. Items can stay monitored forever without being re-downloaded.

**Also in `v0.10.0`: Notifications via [Apprise](https://github.com/caronc/apprise).** Add your preferred notification channels — Discord, Telegram, Slack, email, and the 100+ other services Apprise supports — and choose which Trailarr events each channel receives. For example, point a `#trailarr-downloads` channel on your Discord server at *Trailer Downloaded* events, right alongside your Radarr/Sonarr/Plex notifications. Trailarr already tracks everything as events internally, so this wires those straight to your channels — and it makes the Phase 2 changes visible: you'll *see* what the new download engine does as it happens. When the Issues section arrives in v1.0.0, issue alerts plug into the same channels (e.g. a separate `#trailarr-issues` channel for things needing attention).

### Phases 3 & 4 — Live status + monitoring becomes yours — `v0.10.1`

The stored monitor status is replaced by a **live computed status** — what you see is always derived from actual downloads and your monitor flag, so it can never get stuck or drift out of sync (goodbye, stuck "downloading" states). Media Details gains a per-profile view: which profiles match this item, which are satisfied by which download, and which are still pending.

Monitoring becomes a pure user setting: connection syncs stop changing it, and the per-connection *Monitor Type* dropdown becomes a simple **"monitor new media"** toggle.

**Also here: Preview mode.** A library-wide dry run — see exactly what Trailarr *would* download and why, before it downloads anything. Fresh installs will start in preview until you explicitly enable downloads, so pointing Trailarr at a large, carefully curated library is never a leap of faith.

*Action needed (small):* if you used **Monitor: Sync**, add an `arr_monitored` filter to your profiles instead — the release notes will walk you through it. These are minor, transient changes, so only **~2 weeks** before the next step.

### Phase 5 — Cleanup of legacy fields — `v0.11.0`

With nothing depending on them anymore, the legacy `trailer_exists` and stored-status fields are removed. Custom filters that referenced them are migrated automatically (profile filters like `trailer_exists = false` are now implicit; view filters translate to a new `has_downloads` filter).

*What you'll notice:* very little — this is the payoff release where the old failure modes become impossible.

### Phase 6 — Filter by downloads & files — `v0.11.1`

Custom view filters gain a whole new family of fields: filter your library by download
count, download resolution, owning profile, download dates, files present, and more.
This is the "feel complete" release for library management — build views like *"media
whose only trailer is below 1080p"* or *"has a deleted trailer file"*. (Profile filters
deliberately don't get these fields — a profile filtering on its own output would be
circular.)

### Phase 7 — Internal reorganization — `v0.12.0`

No new features on purpose: the backend is restructured into clean layers (API,
services, database, task scheduling) so the remaining phases — and years of maintenance
after v1.0.0 — build on a foundation that's easy to reason about. Everything is verified
to behave byte-for-byte identically. If you notice *anything* different after this
release, that's a bug — please report it.

### Phase 8 — TMDB integration — `v0.13.0`

Add your own **TMDB API key** and Trailarr resolves trailers from TMDB's curated video lists (with your preferred language, set per profile) before falling back to YouTube search. Radarr/Sonarr-provided IDs and manual selections all feed one per-media list of known videos, refreshed periodically.

*What you'll notice:* far more accurate trailer picks, fewer wrong downloads. Without an API key, everything works exactly as before.

### Phase 9 — Video types — `v0.14.0`

Profiles gain a **video type**: trailer, teaser, clip, featurette, and more. Non-trailer types download exclusively from TMDB's curated lists (no YouTube guessing), and every download records its type — so a featurette is never miscounted as your trailer. If you've been using hacky profiles for extras, this is the release where the app starts doing it natively; it will detect those profiles and suggest settings.

### Phase 10 — Movie/Series profiles + season trailers — `v0.15.0`

Profiles become explicitly **for movies or for series**. Series profiles can enable **season-specific trailers** — one trailer per season, up to the show's season count, sourced from TMDB. Existing profiles are classified automatically from their names and filters; the few that can't be classified are set to movies and disabled for you to review and re-enable.

*Action possibly needed:* reviewing auto-classified profiles, and cleaning up old workaround profiles — the app will point them out.

### Phase 11 — Issues section + v1.0.0

A new **Issues** section surfaces everything that needs your attention in one place: downloads that keep failing (and why), monitored media no profile matches, unreachable folders, media missing a TMDB ID, profiles needing review. Issues plug into the notification channels from v0.10.0, so things needing attention can reach you on Discord, Telegram, or wherever you prefer. With the reconciliation model in place, this is a complete, trustworthy picture — and with it, Trailarr graduates to **v1.0.0**.

## Alongside the phases: making setup painless

The feedback is consistent: people who get Trailarr running love it — and the ones who
struggle almost always hit the same first-hour walls (path mappings, permissions,
YouTube cookies). So a **Setup & Health track** runs alongside the phases:

- **Connection Doctor** *(~v0.11.x)* — after you add a connection, Trailarr checks
  whether it can actually see and write to your media folders, and when it can't, tells
  you exactly why and offers the fix ("Radarr reports `/data/movies` but that's not
  visible here — suggested path mapping: `/data → /media` [Apply]"). Permission problems
  report the exact PUID/PGID mismatch instead of failing three tasks later.
- **Health page** *(~v0.11.x)* — one place with live checks and fixes: ffmpeg & hardware
  acceleration status, yt-dlp version and a test download, YouTube cookies setup (a
  proper UI for it, with validity checking), connection reachability, disk access and
  space. When a download fails because YouTube wants a sign-in, Trailarr will say so —
  and link the fix — instead of burying a stack trace in the logs.
- **Guided setup** *(~v0.13.x)* — a first-run wizard: add a connection (doctor runs
  inline), confirm sensible defaults, run the first sync, **preview** what would be
  downloaded, then enable downloads. Ten minutes from install to a working library,
  without reading a single docs page.
- **Diagnostics bundle** — one button that exports a sanitized report (no secrets) to
  attach to bug reports, so getting help is fast.
- **Profile presets** *(with v0.15.0)* and a **library coverage dashboard + in-app
  trailer playback** *(with v1.0.0)* round out the "enjoyable, feels complete" goal.

## Guiding principles

1. **No forced cleanups.** Every migration is automatic; manual steps are optional or clearly guided.
2. **Facts over flags.** The app stores what's true (your monitor choice, files on disk) and computes the rest — so status can never lie.
3. **Automation only writes what automation owns.** Syncs update sync data, refreshes update refreshed data — and anything you set by hand (monitoring, hand-picked videos, assigned profiles) is **never** overwritten or deleted by a background task. If your choice stops working, Trailarr tells you; it doesn't undo it.
4. **Bake time between risky steps.** Bigger changes get longer gaps so issues surface while they're still harmless.
5. **You'll always see why.** The end goal is that for any media item, Trailarr can show exactly what it will do next and why.

Feedback on any phase is very welcome — open an issue on [GitHub](https://github.com/nandyalu/trailarr/issues).
