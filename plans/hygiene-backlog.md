# Hygiene Backlog

Small, non-blocking cleanups. Fold each into whichever release touches the area anyway;
none justify their own release. Check items off with the release that shipped them.

- [ ] **H1 — API error-handling standardization**: all `api/v1` handlers use the
  pattern from `update_download_profile` (ItemNotFoundError→404, unexpected→logged 500
  with generic detail — no `str(e)` leaks, no blanket 404s). Scheduled: Phase 7 Stage B
  (touches every handler anyway).
- [ ] **H2 — Decorative SVG accessibility sweep**: `aria-hidden="true"
  focusable="false"` on presentational inline SVGs app-wide (only the v0.9.9 banner
  icon has it). Any frontend-heavy release; Phase 3's matrix UI work is a natural slot.
- [ ] **H3 — Older API endpoints marked deprecated** (`/media/all` etc.) — actually
  remove at v1.0.0 API freeze.
- [ ] **H4 — `tests/conftest.py` TODO** ("Update all tests to current codebase") —
  address during Phase 7 test-tree mirror.
- [ ] **H5 — Duplicate `displayTitle` pipes** (helpers/ vs media/pipes/) — merge in
  Phase 7 frontend light touch (keep the underscore-aware one).
- [x] **H6 — `read_all_raw`/`downloads_raw` raw-SQL endpoints** — RESOLVED as a
  settled design decision (July 2026), not a cleanup: raw endpoints stay raw. Data is
  validated when WRITTEN to the database, so re-validating and converting every row
  into typed Python objects at read time (for the frontend or external API consumers)
  would only add memory pressure and slow responses on large libraries — raw reads
  are deliberately the efficient list-scale path. Rationale documented in CLAUDE.md
  (Key Conventions); do not convert these to typed responses.
- [x] **H7 — Startup-fix module retirement** — DONE (Phase 3, ships v0.10.2):
  `startup_fixes.py` and its tests deleted with `fix_trailer_exists_flags`
  (justification recorded in `phase-03-dynamic-status.md`).
- [ ] **H8 — Scan TODO comments** ("once the planned Issues section exists…") in
  files-scan → wired and removed in Phase 11.
- [ ] **H9 — `media.youtube_trailer_id` column retirement** once the MediaVideo table
  owns candidates (Phase 9 cleanup; UI "saved trailer id" field becomes a USER-source
  candidate).
- [x] **H10 — `VACUUM` for logs.db after the daily purge** — DONE (ships in v0.10.0):
  `delete_old_logs` now uses a single batch DELETE + conditional `VACUUM` on an
  autocommit connection (`vacuum_logs_db` in `config/logs/db_utils.py`). Verified at
  50k rows: 13.3 MB → 0.14 MB in 0.32s. trailarr.db VACUUM-after-migrations still
  lands with Phase 5.
