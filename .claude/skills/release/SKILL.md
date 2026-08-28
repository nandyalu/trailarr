---
name: release
description: "Ship a Trailarr release from dev to main: update and prune dependencies, sync version badges, write release notes in ASD-STE100 style, open the release PR with the house title/body convention, merge it, reset dev from main, and create the GitHub release that mints the tag and triggers the release/Docker workflows. Trigger: /release"
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
/release publish          # just create the GitHub release (tag + workflows)
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
- Sections, in order, only if non-empty: `**What's New:** ✨`, `**Bug Fixes:** 🐛`, `**Other Changes:** ⚙️`.
- Bullet shape: `- **Bold hook, present tense, states the user-facing win** — explanation sentence(s).` Optional trailing `see [Label](relative/path.md#anchor)`, and blockquote warnings `> ⚠️ **Heading.** explanation.` for breaking changes/deprecations.
- **Link what the entry closes.** If a change or a bug fix closes an issue, put the reference at the end of that bullet: `...does not run ([#653](https://github.com/nandyalu/trailarr/issues/653)).` Use `/pull/N` when a pull request delivered the change, and `/discussions/N` for a discussion. Write the markdown link only. Do not write `Fixes`, `Closes`, or `{_target="_blank"}` in a new entry — those forms are from older versions in the same file. A `Closes #N` line goes in the PR body only (sections 4 and 7), so the entry itself must carry the link. To find the references: run `git log origin/main..dev --oneline` and read each subject and body for an issue number, then run `gh pr list --state merged --search "merged:>=<date of the last release>" --json number,author,title,url` and open each result with `gh pr view <n>`.
- **Credit every contributor who is not the owner.** List the candidates with `git log origin/main..dev --format='%an | %s'` and the `gh pr list` command above. Ignore `dependabot[bot]` and `github-actions[bot]`. Ignore the owner, who commits as both `nandyalu` and `Uma Nandyala`. Take the handle from the pull request `author.login` field, because `git log` gives a display name (`Luis Miranda`), not a handle. Do not filter the PR list by base branch: an outside contributor opens the pull request against `main` or against `dev` (compare [#620](https://github.com/nandyalu/trailarr/pull/620) with [#652](https://github.com/nandyalu/trailarr/pull/652)). Put the thanks at the end of that person's entry, in front of the reference:
    - Contributed the fix, and the reason is clear: `Thanks [@lems111](https://github.com/lems111) for finding the cause and the fix! ([#652](https://github.com/nandyalu/trailarr/pull/652))`
    - Contributed the fix, and the reason is not clear: `Thanks [@d4rk22](https://github.com/d4rk22)! ([#620](https://github.com/nandyalu/trailarr/pull/620))`
    - Only reported the problem: `Thanks [@kevin2xk](https://github.com/kevin2xk) for the detailed report! ([#626](https://github.com/nandyalu/trailarr/issues/626))` — get that name with `gh issue view <n> --json author`.

    Sections 4 and 7 copy the entry word for word, so one thanks reaches the release notes page, the pull request, and the GitHub release.
- Write and rewrite entries per the project's ASD-STE100 Simplified Technical English convention (see `CLAUDE.md`): short sentences, one idea per sentence, active voice, simple vocabulary.
- Versions are separated by a `---` line.

## 3. Commit and push

Commit the dependency/version/badge/notes changes on `dev` with a plain message (no footer), then `git push origin dev`.

## 4. Open the release PR

- **Title**: `vA.B.C - Short title for release` (e.g. `v0.10.1 - Reject live videos download & tmp folder cleanup`).
- **Body**: the *entire* release-notes section for that version, verbatim, **including** the `## **vX.Y.Z** - _date_` heading line, excluding the trailing `---` separator. No "Summary"/"Test plan" scaffolding, no footer — this is not the generic `gh pr create` template.
- **Closing lines**: append one `Closes #N` line for each issue the release closes, after the notes. GitHub closes those issues when the PR merges. Section 7 removes these lines again for the GitHub release.
- Base `main`, head `dev`.

## 5. Merge

Prefer **"Rebase and merge"**. Fall back to **"Create a merge commit"** only if GitHub blocks the rebase — `dev` has occasionally picked up a `Merge branch 'main' into dev` commit from a prior sync, and GitHub's rebase-and-merge button refuses to rebase a branch containing merge commits ("this branch cannot be rebased" error). Never fall back to squash for this reason, and never force a clean rebase by rewriting `dev` locally and force-pushing — it's shared branch history. Confirm the actual merge with the user before executing it (shared-state, hard to reverse).

Wait for the PR checks to pass first (`gh pr checks <n> --watch`). The repo ruleset reports `REVIEW_REQUIRED` because the owner authors the release PR and cannot self-review — merge with `gh pr merge <n> --rebase --admin` once all checks are green.

## 6. Post-merge cleanup

Merging deletes `dev` on GitHub. Locally:

```
git checkout main
git pull origin main
git branch -D dev
git checkout -b dev main
git push -u origin dev
```

## 7. Create the GitHub release (required — nothing else mints the tag)

No workflow on a `main` push creates the tag or release. Creating the GitHub release is what mints the `vX.Y.Z` tag, and the tag push then triggers `release.yml` (builds the direct-install asset `trailarr-vX.Y.Z-release.tar.gz` + `.sha256`), `docker-publish.yml` (versioned Docker image), and the Discord release notification.

```
gh release create vX.Y.Z --target main --latest \
  --title "vX.Y.Z - Same short title as the PR" \
  --notes-file <file>
```

- **Notes file**: the same release-notes section used for the PR body (heading line included), but **without** any `Closes #N` lines — those are PR-only.
- Verify afterward: the `Release` and `Docker Publish` workflow runs succeed (`gh run list` / `gh run watch`), and the release shows both asset files (`gh release view vX.Y.Z --json assets`).