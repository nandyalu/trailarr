---
name: release
description: "Ship a Trailarr release from dev to main: update and prune dependencies, sync version badges, write release notes in ASD-STE100 style, open the release PR with the house title/body convention, merge it, and reset dev from main afterward. Trigger: /release"
trigger: /release
---

# /release

Runs the full dev → main release cycle for this repo, or a single step of it if asked (e.g. "just update the release notes", "just merge it").

No step in this skill includes a Claude Code / `Co-Authored-By` footer in any commit message or PR body — never add one, in this repo.

## Usage

```
/release                 # full cycle: deps -> tests -> notes -> commit/push -> PR
/release deps            # just the dependency-update + prune-overrides step
/release notes            # just the release-notes step (date + ASD-STE100 rewrite)
/release pr               # just open the PR (assumes dev is already ready)
/release merge            # merge the open release PR, then reset dev from main
```

## 1. Pre-release checklist (deps, tests, docs)

1. Backend deps: `cd backend && uv sync --upgrade`.
2. Frontend deps: `cd frontend && npm update`. If `npm audit` flags a vulnerability in a transitive dep pinned to an exact version by its parent (so a normal update can't reach the patched version), check whether an `overrides` entry in `package.json` can force just that leaf package to the patched version without downgrading the parent top-level package — verify with `npm ls <pkg>`, `npm audit`, tests, and build afterward. Don't run `npm audit fix --force` if it would force a breaking downgrade of an unrelated top-level package (e.g. `@angular/cli`).
3. **Prune stale `overrides`**: for every entry already in `package.json`'s `overrides`, check whether the parent dependency now natively ships a version that satisfies it (`npm view <parent>@latest dependencies`, or just remove the override and re-run `npm install` + `npm audit`). Drop any override that's no longer needed.
4. Backend tests: `PYTHONPATH=$(pwd) uv run python -m pytest tests/ -v` from `backend/` — all must pass.
5. Frontend tests: `npm run test` from `frontend/`.
6. Frontend production build: `npm run build` from `frontend/` — confirms the dependency bump didn't break the real build, not just unit tests.
7. Confirm `backend/pyproject.toml` and `frontend/package.json` already carry the target version (the `bump-version.yml` GitHub Action sets these when a PR titled `vX.Y.Z - ...` is opened/edited).
8. Update `docs/index.md`: sync the FastAPI and Angular version numbers in the shields.io badge URLs near the top (`img.shields.io/badge/FastAPI-...`, `img.shields.io/badge/angular-...`) to whatever step 1–2 actually landed on.

## 2. Release notes (`docs/release-notes/2026.md`)

- Replace the version's `_TBD_` date with the real release date: `## **vX.Y.Z** - _Month D, YYYY_`.
- Sections, in order, only if non-empty: `**What's New:** ✨`, `**Bug Fixes:** 🐛`, `**Other Changes:** 🔧`.
- Bullet shape: `- **Bold hook, present tense, states the user-facing win** — explanation sentence(s).` Optional trailing `see [Label](relative/path.md#anchor)`, issue refs `([#123](https://github.com/.../issues/123))`, and blockquote warnings `> ⚠️ **Heading.** explanation.` for breaking changes/deprecations.
- Write and rewrite entries per the project's ASD-STE100 Simplified Technical English convention (see `CLAUDE.md`): short sentences, one idea per sentence, active voice, simple vocabulary.
- Versions are separated by a `---` line.

## 3. Commit and push

Commit the dependency/version/badge/notes changes on `dev` with a plain message (no footer), then `git push origin dev`.

## 4. Open the release PR

- **Title**: `vA.B.C - Short title for release` (e.g. `v0.10.1 - Reject live videos download & tmp folder cleanup`).
- **Body**: the *entire* release-notes section for that version, verbatim, **including** the `## **vX.Y.Z** - _date_` heading line, excluding the trailing `---` separator. No "Summary"/"Test plan" scaffolding, no footer — this is not the generic `gh pr create` template.
- Base `main`, head `dev`.

## 5. Merge

Prefer **"Rebase and merge"**. Fall back to **"Create a merge commit"** only if GitHub blocks the rebase — `dev` has occasionally picked up a `Merge branch 'main' into dev` commit from a prior sync, and GitHub's rebase-and-merge button refuses to rebase a branch containing merge commits ("this branch cannot be rebased" error). Never fall back to squash for this reason, and never force a clean rebase by rewriting `dev` locally and force-pushing — it's shared branch history. Confirm the actual merge with the user before executing it (shared-state, hard to reverse).

## 6. Post-merge cleanup

Merging deletes `dev` on GitHub. Locally:

```
git checkout main
git pull origin main
git branch -D dev
git checkout -b dev main
git push -u origin dev
```