# Post-v1.0 Backlog

Ideas and deliberate deferrals, recorded so they're decisions rather than blind spots.
Revisit when v1.0.0 ships (or if the noted trigger fires earlier).

## Arr Webhooks (top candidate — "game changer")

Radarr/Sonarr push webhooks on import/upgrade/delete → Trailarr reacts in minutes
instead of at the next poll interval. The killer detail: **Trailarr can register its
own webhook automatically** via the Arr APIs (create a Notification/Connect entry
pointing at Trailarr's endpoint) — zero user setup, always in sync. Design sketch:
webhook receiver endpoint (auth via per-connection token in the registered URL),
translate payloads to targeted single-media sync + scan + download-check; polling
remains as reconciliation fallback. Extend the same pattern to Plex webhooks later.
Prereq: Phase 7 services layer (receiver calls the same services as the poll path).

## Opt-in anonymous stats — deliberate NO for now

Would give real satisfaction/failure rates instead of relying on issue reports, but
self-hosted culture is telemetry-averse. Decision (July 2026): not before v1.0; if
revisited, strictly opt-in, aggregate-only, fully documented payload.

## Quality-rejection loop — deferred, low risk (watch trigger)

`trailer_cleanup` deletes bad (silent) trailers; under the downloads-driven engine a
deleted-bad trailer could be re-downloaded (possibly the same video id). Maintainer
assessment (July 2026): <1% real-world risk — confirmed working trailers sit untouched
forever like media files. **Trigger to revisit:** any user report of a repeating
cleanup→re-download cycle. Mitigation already sketched: record rejections against the
*candidate* (rejected flag on MediaVideo row / attempt `last_video_id`) so the resolver
skips them.

## Multi-Arr duplicate folders — deemed a non-issue

TRaSH-guides convention (separate root folders per quality instance) is the widespread
setup, so Arr↔Arr folder collisions are rare by ecosystem practice; Plex-only
dual-resolution folders already merge into one media row via folder_path linking.
No linking work planned. Docs recipe (`monitor_new_media=False` on a secondary
instance) can be added to the connections docs if questions appear post-Phase 4.

## Also post-v1.0

- **UI translations / i18n** (per-profile *trailer* language ships in Phase 8; this is
  about the interface itself).
- **Broader accessibility audit** (beyond hygiene item H2's decorative-SVG sweep).
- **Committed Playwright e2e suite in CI** — the headless smoke scripts used during
  phase verifications should graduate into `frontend/e2e/` + a CI job once the UI
  stabilizes post-Phase 3 (earlier if flakiness allows).
