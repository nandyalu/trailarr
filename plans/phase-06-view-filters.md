# Phase 6 — Downloads & Files Filter Family (View Filters)

**Status:** not started · **Release:** v0.11.1 · **Depends on:** Phase 5 (virtual-field
mechanism + `has_downloads` proven)

## Objective

Give view filters first-class access to what users actually manage now: downloads and
files. **View filters only — profile (TRAILER-type) filters explicitly reject these
fields** (a profile filtering on its own outputs is circular; enforce in validation).

## Design decisions (settled)

1. **Field family** (virtual fields over `MediaRead.downloads` / files):
   | Field | Type | Semantics over the list |
   |---|---|---|
   | `has_downloads` | bool | exists (from Phase 5) |
   | `download_count` | int | count of `file_exists=True` rows |
   | `download_profile` | int (profile id; UI shows names) | ANY active download owned by profile |
   | `download_resolution` | int | ANY active download matches condition |
   | `download_added_at` | date | ANY active download matches (newest evaluated for IN_THE_LAST) |
   | `download_file_missing` | bool | any row with `file_exists=False` (deleted-file history present) |
   | `has_unknown_profile_download` | bool | formalizes the v0.9.9 quick filter |
   | files: keep `has_file`/`has_folder`; add `file_count` (int) | | via files manager |
   **ANY-semantics across the list, documented in the filter editor UI.** No ALL-variant
   this release (scope).
2. **Evaluation:** frontend `applyCustomFilter` (primary — view filtering is
   client-side over `combinedMedia` which already carries downloads) + backend
   `matches_filters` parity (used by any server-side path). Backend `_apply_filter`
   SQL translation only for fields it already handles; virtual fields evaluated
   post-query where needed — measure before optimizing.
3. **Validation:** `filter.py` gains a `VIRTUAL_DOWNLOAD_COLS` set with per-field
   type→conditions mapping (reuse existing INT/BOOL/DATE condition validators);
   `CustomFilter` create/update rejects these for `filter_type=TRAILER` with a clear
   message.
4. **UI:** filter editor (`edit-filter-dialog`) groups fields (Media / Downloads /
   Files) in the field dropdown; `download_profile` renders a profile dropdown (by
   name) storing the id — handle deleted-profile ids by showing "Deleted [id]".

## Wargame

- W1. Media with 30 downloads (post-#591 libraries): count/any semantics still O(list);
  no perf cliff on 1,700 items × client-side (measure on config-dev copy in browser).
- W2. `download_profile` filter kept after that profile is deleted → matches nothing;
  editor shows "Deleted"; no crash.
- W3. Date conditions vs timezone: downloads `added_at` are UTC; frontend Date parsing
  already handled in models — reuse `parseDate`.
- W4. Combining virtual + regular fields in one filter: AND semantics as today.
- W5. Profile-filter rejection: attempts via raw API also rejected (validation lives
  backend-side), not just hidden in UI.
- W6. Existing saved view filters: untouched; no migration.

## Pitfalls

- Frontend and backend evaluators MUST agree — add a table-driven parity test executing
  the same fixture cases against both (backend pytest + vitest sharing a JSON fixture
  checked into `tests/fixtures/filter-cases.json` and `frontend/src/…/spec`).
- `booleanFilterKeys`/`numberFilterKeys`… lists in `models/customfilter.ts` mirror
  backend col lists — update both.
- OpenAPI regen (validation error messages/model changes).

## Verification

Full suites; parity fixture green on both sides; headless: build a "Missing 1080p"
style filter in the UI (`download_resolution LESS_THAN 1080` OR `has_downloads=false`),
verify the list, edit, delete. Docs: extend the profiles/filters docs page with the new
field family + ANY-semantics note.

## Exit criteria

All family fields usable in view filters end-to-end; profile filters reject them; parity
test green; docs updated; release notes with 2 recipe examples.
