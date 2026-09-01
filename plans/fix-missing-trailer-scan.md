# Fix — Quadratic Missing-Trailer Scans

**Status:** IN PROGRESS — targets v0.11.5 (patch, off `dev`). Supersedes the approach in
PR #666 (`sittingmongoose:fix/missing-trailer-keyset-scan`), whose diagnosis is correct
and whose fix is not merged — see "PR #666 disposition" below.

## Objective

`download_missing_trailers` re-scans the whole media table once per downloaded trailer.
Remove that cost without losing the task's "keep going until there is no work left"
behaviour, and without letting a mid-run profile edit apply stale settings to a download.

Two costs multiply today. Both must go:

1. **Restart-per-download.** The `while True` at `core/download/trailers/missing.py:273`
   breaks out of the inner loop after it finds ONE item, downloads it, then scans again
   from the first row. `processed_media_ids` only holds items the pass RESOLVED — an item
   with no matching profiles hits `continue` and never enters the set, so it is read and
   evaluated again on every pass. A library of 20,000 items where 500 match walks the
   other 19,500 once per download.
2. **N+1 lazy loads inside each scan.** `Media.downloads` is a plain `Relationship`
   (`core/base/database/models/media.py:105`) and `MediaRead.downloads` is a populated
   field (line 132), but `read_all_generator` builds its statement with no eager load
   (`core/base/database/manager/media/read.py:135`). Every yielded row fires one more
   SELECT. That is N+1 per scan, and N×D across a run.

The run is long by design: the delay ladder in `docs/user-guide/tasks/index.md` sleeps 2
to 10 minutes between downloads, so 200 downloads take 13+ hours. Two consequences shape
every decision below. A mid-run profile edit is the NORMAL case, not an edge case. And an
extra database read per download is free next to a 2-minute sleep — per-download cost is
never the thing to optimise here; per-media-row cost is.

## Design decisions (settled)

1. **Sweeps, not a keyset cursor.** Split the task into a scan phase that builds a work
   list, and a download phase that consumes it, wrapped in a bounded outer sweep loop.
   Each sweep is ONE full scan. Sweep 1 does the work; sweep 2 finds what became eligible
   while sweep 1 ran and normally returns nothing. Cost goes from O(N×D) to O(S×N + D)
   with S = 2 in practice.

   A cursor (PR #666) gives a single pass but pays with semantics: an item monitored at
   hour 2 of a 13-hour run sits below the cursor and waits for the NEXT scheduled run,
   which cannot start while this one is still going.

2. **The work list is a hint about where to look, not a promise of what to do.** It holds
   media ids, each with the profile ids the scan proposed — and those profile ids are
   bookkeeping only (decision 5). They never reach the download. Every decision about
   WHAT to download is re-made in the download phase against freshly read data, so the
   set that drives yt-dlp can differ from the set the scan proposed, in both directions.

   The list must never hold `TrailerProfileRead` objects. A profile object captured
   before an hours-long download phase carries settings the user may since have changed,
   and the resulting file then reads as satisfied, so nothing retries it.

3. **Re-verify each item immediately before its download**, inside the download phase:
   read the media row by id, read the current profiles, then run the full
   `find_matching_profiles` → `evaluate_satisfaction` → `_filter_backoff_eligible` chain
   on that one item. If nothing survives, skip it and move on. This is what makes a
   mid-run profile edit come out right, and it is cheap: one indexed row plus a handful
   of profile rows, against a download measured in minutes.

   Because the chain is recomputed in full, a profile ENABLED mid-sweep is picked up for
   every item still in the list, even though the scan that built the list never saw it.

4. **`attempted` is keyed by `(media_id, profile_id)`, not by media id.** A media-id key
   is too coarse: if the user enables profile Q after item 1 downloaded, sweep 2 finds
   item 1 pending for Q and must not suppress it. The pair key matches how the rest of
   the engine already thinks — `attempts_by_key` in `core/download/trailers/pending.py:172`
   and `_filter_backoff_eligible` at `missing.py:163` are both pair-keyed.

5. **Termination is structural, and there is no sweep cap.** The download phase consumes
   every pair the scan proposed for a media item at the moment it visits that item —
   unconditionally, before the re-verify, whether or not a download follows. So each
   sweep either returns an empty work list and breaks, or consumes at least one new
   pair; consumed pairs are excluded from every later work list; the pair space is
   finite. The loop drains on its own, whatever order the database returns rows in, with
   no `ORDER BY` and no cap.

   No fixed count, and no wall-clock gate between sweeps. **A sweep that finds work is a
   sweep that SHOULD run** — that is `dev`'s "keep going until there is nothing left"
   behaviour, and a cap would stop a busy library mid-stream for no reason.

   A timer keyed to the delay ladder was considered and rejected. The empty-list break
   already covers the short-run case, so a timer would save exactly one scan on runs with
   a handful of downloads and nothing at all on the long runs this fix is about. It also
   measures the wrong quantity: how long the DOWNLOADING took, not how long the library
   had to change — new work comes from the hourly Arr refresh, the files scan, expiring
   backoff windows and user actions, none of which track the inter-download delay. And
   its constant would couple silently to the delay table in
   `docs/user-guide/tasks/index.md`: edit that table and the gate stops working, with a
   behavioural cliff (5 downloads → no second sweep, 6 → second sweep) that nothing in
   the user's mental model explains.

   The unconditional consume is what makes the drain hold. Consuming only the pairs that
   survived re-verify would let a scan re-propose a pair that re-verify keeps skipping,
   and the loop would spin with zero downloads — see W13.

6. **Profiles are re-read once per download, not hoisted out of the loop.** `dev` already
   does this (one read per pass, and a pass is one download), so keeping it is not a
   regression. It is the mechanism behind decision 3, and one profile read next to a
   2-minute sleep costs nothing.

7. **Trailers already downloaded under an old profile stay as they are.** A profile
   applies to new downloads, not to files already on disk — the same contract as the rest
   of the Arr stack, and what users expect. Reconciling an edited profile against existing
   downloads would need a satisfaction rule that compares a download's real properties
   against the profile's current ones. That is a separate feature; it does not ride along
   with this fix.

8. **Eager-load `Media.downloads` in `read_all_generator`.** Use `selectinload` together
   with `yield_per` on the execution options. `joinedload` on a collection is not
   compatible with `yield_per`, and `stream_results=True` on its own buffers the whole
   `selectinload` result. This is independently shippable and also speeds up
   `compute_library_pending`, the preview path and every other consumer.

9. **Do NOT extract the shared scan in this release.** `compute_library_pending`
   (`pending.py:154`) already performs this exact scan with batched attempts, and its own
   docstring calls itself the download task's work list. The two are parallel
   implementations that agree today and will drift. The right fix is one shared generator
   yielding `(media, claims, unsatisfied, eligible)` that both call — but Phase 7 is the
   single big-churn release and it moves both files, so a structural extraction now buys
   a merge conflict. Recorded as hygiene item H21, to be done after the reorg lands.

   Note that the scan and the download phase's re-verify are now a third copy of the same
   chain, inside `missing.py` itself. They must stay in agreement: a PERSISTENT
   disagreement is what W13 describes, and while the unconditional consume keeps the loop
   draining, the real protection is one implementation rather than three that agree by
   coincidence. H21 is therefore a correctness item, not only a tidiness one.

10. **Batch the attempt lookup in the scan phase.** `_filter_backoff_eligible` issues one
    `attempt_manager.read_for_media()` per media. In the scan phase that is per-row cost
    and must become a single `attempt_manager.read_all()` keyed by `(media_id, profile_id)`,
    exactly as `pending.py` does. In the download phase the per-item lookup is fine and
    stays.

11. **`after_id` is not added to `read_all_generator`.** The sweep design walks the
    generator once per sweep, so there is no cursor to resume from. Leaving the parameter
    out keeps the manager surface small and avoids the `_apply_filter` interaction that
    an untested `monitored_only=True` + `after_id` combination would carry.

### PR #666 disposition

The PR found a real bug and diagnosed it correctly; the profiling and the write-up are
sound. The keyset cursor is not merged because of decision 1. Credit the contributor in
the v0.11.5 release note. Whether to ask the author to revise the PR toward this plan or
to supersede it is the maintainer's call, not this plan's.

## Execution steps

Ordered so the app is releasable at every commit.

1. **Eager load.** Add `selectinload(Media.downloads)` and `yield_per` to
   `read_all_generator`. Measure a full scan before and after on a real-size library.
   Ships alone if the rest slips.
2. **Split the task.** Add a private `_build_work_list(attempted) -> list[int]` to
   `missing.py`: one pass of `read_all_generator(monitored_only=True)`, one batched
   `attempt_manager.read_all()`, generator fully consumed and closed before it returns.
   Claims are applied here (the scan phase writes; the pending view does not).
3. **Sweep loop.** Keep `while True`. It now breaks on an empty work list instead of on
   "no item found", and each iteration is one sweep rather than one download. Move the
   `trailer_profiles` / `enabled_profiles` guards ABOVE the scan so that no early-return
   path builds a generator.
4. **Download phase.** Per entry: consume every proposed pair into `attempted` FIRST,
   then re-read the media, re-read profiles, re-run the chain, skip if nothing survives,
   and otherwise call `_process_single_media_item` with the freshly read profile objects.
   The consume happens before the re-verify and before the `await` — not in a `finally`
   that a `continue` would skip.
5. **Counters.** Replace the single "Processed" number with `scanned`, `attempted`,
   `downloaded`, `skipped`. Rewrite the summary log line to the house rule (see Pitfalls).
6. **Tests**, including the restored termination test and `pytest-timeout`.
7. **Docs and release notes.**
8. **Backlog entry** for decision 9 in `hygiene-backlog.md`.

## Wargame

Every scenario needs a deliberate answer in code or a test before this exits. The first
five are the user-facing ones; assume a sweep-1 list of 200 items with 4 downloaded.

| # | Scenario | Required behaviour |
|---|---|---|
| W1 | Profile P disabled after 4 downloads | Items 5–200 drop P at re-verify. No download for P. The 4 files stay. |
| W2 | P's filter narrowed | Items that no longer match drop out at re-verify; matching ones proceed. |
| W3 | P's resolution/format/folder edited | Items 5–200 download with the NEW settings — the freshly read profile object is what reaches yt-dlp. |
| W4 | Profile Q enabled mid-sweep | Items 5–200 pick it up at re-verify. Items 1–4 pick it up in sweep 2, via the pair key (decision 4). |
| W5 | Profile P deleted mid-sweep | Not in `get_trailerprofiles()`, so it drops out. Attempt rows are pruned at the next run's start, as today. |
| W6 | Media monitored, or added by an Arr sync, at hour 2 | Sweep 2 picks it up in the SAME run. This is the case the cursor approach loses. |
| W7 | Media unmonitored at hour 2, still in the list | Re-verify drops it. No download. |
| W8 | Media deleted at hour 2, still in the list | `media_manager.read(id)` returns None → skip, no exception. |
| W9 | A manual download from Media Details satisfies an item still in the list | Re-verify sees it satisfied and skips. The core invariant (never two downloads for one profile) holds. |
| W10 | A download fails | An attempt row is recorded; backoff drops the pair in sweep 2. The pair is in `attempted` regardless, so a failure to record cannot cause a re-attempt loop. |
| W11 | An item is SKIPPED without recording an attempt row (storage unreachable, waiting for the media file) | The pair is already in `attempted`, so sweep 2 does not return it. It retries on the next scheduled run, as documented. |
| W12 | Stop event set mid-sweep | Returns promptly — checked before each sweep and before each download, as today. |
| W13 | The scan proposes `(X, P)`, and re-verify skips it every time | The pair is consumed on the sweep that visits X, so no later scan can re-propose it. Without the unconditional consume (decision 5) this spins forever with zero downloads and no log line that makes it obvious. Needs a direct test. |
| W14 | Sweep 2 legitimately finds hundreds of newly eligible items on a busy library | It processes them. Nothing caps a productive sweep. |
| W15 | Downloads disabled | `_run_preview_pass()` still returns before any of this. Unchanged. |
| W16 | Empty library / no enabled profiles | Guards return before the scan; zero generators built. |

## Pitfalls

- **Do not carry a `TrailerProfileRead` across the `await`.** A stale profile object means
  downloading with settings the user just changed — and the resulting file then reads as
  satisfied, so nothing retries it. This is the failure mode decision 2 exists to prevent.
- **Consume every proposed pair, not just the eligible ones, and consume before the
  re-verify.** This is the entire termination argument (decision 5). Consuming only what
  survived re-verify — or consuming in a `finally` that an early `continue` skips —
  reintroduces the spin, and it spins with zero downloads, so nothing in the logs looks
  wrong. The paths that skip without recording an attempt row (W11) are exactly the ones
  this covers.
- **The proposed profile ids are bookkeeping, and nothing else.** The moment they are
  passed to `_process_single_media_item` as a shortcut for "what to download", decision 3
  is dead and W1–W3 regress silently — the tests would still pass, because the scan and
  the re-verify agree in every fixture small enough to write by hand.
- **The scan generator must be closed before any download starts.** Holding a streaming
  cursor across a 2-minute sleep plus a yt-dlp run pins a SQLite connection. This is why
  the original code restarted at all; the scan/download split is what makes it safe, not
  an accident of the loop shape.
- **`joinedload` will not work here.** Collections and `yield_per` are incompatible; use
  `selectinload`.
- **The log line must follow the house rule** — a whole sentence, active voice, naming
  Trailarr as the actor, ending in a period. The current line is not one, and it renders
  `Processed: 5 Successful downloads: 2` with no separator. Do not put a bracketed number
  that is not a media id in any message (`tests/test_log_message_safety.py` enforces it).
- **A green suite is not evidence.** Read `plans/README.md` → "A green suite does not mean
  the code runs". The re-verify block and the sweep-cap branch are error-adjacent paths
  that no ordinary test run will walk. Drive them in a real app run or inspect them with a
  test that reads the code.
- **Do not pin private call shapes in tests.** PR #666's assertions on
  `call_args_list[0].kwargs` froze an implementation detail — including a wasted call — so
  that cleaning it up required editing the tests. Assert on behaviour: each item processed
  once, the task terminates, the right items are skipped.
- **Phase 7 conflict.** `feat/phase7-backend-reorg` moves every file this fix touches. This
  ships first, as a patch off `dev`; the reorg branch must rebase the change across the
  move map in `phase-07-backend-reorg.md`. Keep the diff small and in as few files as
  possible for that reason.

## Verification

1. `PYTHONPATH=backend uv run python -m pytest tests/` green.
2. **Restore the termination test.** PR #666 rewrote
   `test_download_missing_trailers_prevents_infinite_loop` so that its fake generator
   enforces the cursor itself, which means the scenario the test was written for is no
   longer exercised anywhere. Keep a case whose fake ignores any cursor and yields the
   same item forever, and assert the task still terminates with each item processed once.
   Under this design it passes because of `attempted`, so the test is meaningful again.
3. **Test the drain directly (W13).** Force a persistent scan/re-verify disagreement — a
   scan that keeps proposing `(X, P)` while the re-verify always skips it — and assert
   the task ends. This is the one failure mode with no cap behind it, and it produces
   zero downloads and no suspicious log line, so nothing else would catch it.
4. **Add `pytest-timeout`** to `backend/pyproject.toml` with a per-test cap in `addopts`.
   There is none today, so a termination regression hangs CI indefinitely instead of
   failing it. Worth doing on its own merits.
5. **Cover `monitored_only=True` together with the eager load** in
   `tests/core/base/database/manager/test_media_read.py` — `monitored_only` routes through
   `_apply_filter`, and no existing test combines it with the new execution options.
6. **Measure.** Seed a library of ~20,000 media rows with ~500 matching an enabled
   profile. Record wall-clock and query count for one full scan, and for a run that
   downloads 10 items, before and after. Put the numbers in the PR description.
7. **Drive the running app** per CLAUDE.md: `python3 scripts/launch.py`, trigger the task
   from the Tasks page, then edit a profile mid-run and confirm W1 and W3 from the logs.
8. **No release fixture is needed.** This changes no schema and no row shape, so
   `plans/README.md` upgrade-safety rule 4 does not apply. Run the existing gauntlet.
9. `graphify update .` after the code changes.

## Docs to update

- `docs/user-guide/tasks/index.md` → **Download Missing Trailers**: add a note, with
  `{{ version_badge("upd", "0.11.5") }}`, stating that the task scans the library in
  sweeps, that a profile change during a run applies to downloads that have not started
  yet, and that trailers already downloaded keep the profile settings they were
  downloaded with. Single-line paragraphs — never hard-wrap prose in `docs/`.
- `docs/release-notes/2026.md` → one sentence under v0.11.5, linking to the tasks page for
  the detail. One sentence per bullet is the house rule; PR #666's two-sentence entry with
  inline background is not the format.
- No OpenAPI change — this touches no endpoint.

## Exit criteria

- A full run over a 20,000-item library performs 2 media scans, not one per download, and
  the measured numbers are in the PR.
- `read_all_generator` issues a bounded number of queries per batch, not one per row.
- Every W1–W16 row has a test or a deliberate, recorded answer.
- The termination test passes with a fake generator that ignores ordering entirely, the
  W13 drain test passes with a scan that re-proposes a pair the re-verify always skips,
  and `pytest-timeout` is configured so that a future regression fails instead of hanging.
- No sweep cap and no inter-sweep timer appear anywhere in the implementation.
- The summary log line follows the house rule and reports `scanned`, `attempted`,
  `downloaded` and `skipped` separately.
- Tasks page and release note shipped in the same release as the behaviour change.
- A hygiene item exists for the shared-scan extraction (decision 9).
