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

1. Backend deps: `cd backend && uv sync --upgrade`. An exact pin (`==`) in `backend/pyproject.toml` is deliberate, and `uv sync --upgrade` respects it. Do not loosen a pin during a release. Example: `quiv==0.10.0` stays, because quiv 1.0.1 has breaking changes.
2. Frontend deps: `cd frontend && npm update`. If `npm audit` flags a vulnerability in a transitive dep pinned to an exact version by its parent (so a normal update can't reach the patched version), check whether an `overrides` entry in `package.json` can force just that leaf package to the patched version without downgrading the parent top-level package — verify with `npm ls <pkg>`, `npm audit`, tests, and build afterward. Don't run `npm audit fix --force` if it would force a breaking downgrade of an unrelated top-level package (e.g. `@angular/cli`).
3. **Prune stale `overrides`**: for every entry already in `package.json`'s `overrides`, check whether the parent dependency now natively ships a version that satisfies it (`npm view <parent>@latest dependencies`, or just remove the override and re-run `npm install` + `npm audit`). Drop any override that's no longer needed.
4. **Move the `allowScripts` pins.** The `allowScripts` block in `frontend/package.json` names exact versions (`esbuild@0.28.2`, `lmdb@3.5.6`, ...). When `npm update` moves one of those packages, npm blocks its install script and prints only a warning (`install-scripts ... blocked because they are not covered by allowScripts`). Get the installed versions with `npm ls <pkg> --all`. Change each entry to the installed version, and remove an entry whose package left the tree. Then run `npm ci`, which is the clean install that Docker does. It must show no blocked scripts.
5. Backend tests: `PYTHONPATH=$(pwd) uv run python -m pytest tests/ -v` from `backend/` — all must pass.
6. Frontend tests: `npm run test` from `frontend/`.
7. Frontend production build: `npm run build` from `frontend/` — confirms the dependency bump didn't break the real build, not just unit tests.
8. Confirm `backend/pyproject.toml` and `frontend/package.json` already carry the target version (the `bump-version.yml` GitHub Action sets these when a PR titled `vX.Y.Z - ...` is opened/edited).
9. Update `docs/index.md`: sync the FastAPI and Angular version numbers in the shields.io badge URLs near the top (`img.shields.io/badge/FastAPI-...`, `img.shields.io/badge/angular-...`) to whatever step 1–2 actually landed on. Edit `docs/index.md` only. A workflow copies it to `README.md`, and pushes that change to `dev` as a `github-actions[bot]` commit.

## 2. Release notes (`docs/release-notes/2026.md`)

- Replace the version's `_TBD_` date with the real release date: `## **vX.Y.Z** - _Month D, YYYY_`. The date changes the heading anchor (`#v0130-tbd` becomes `#v0130-september-24-2026`), and every `{{ version_badge(..., "X.Y.Z") }}` links to that anchor. `docs/hooks.py` builds the new links, but the local render cache in `.cache/` keeps the old ones, because the cache does not notice a change in another file. Before you check the badge links, clear the cache: `find .cache -mindepth 1 -not -name .gitignore -delete && rm -rf site && uv run --project backend zensical build`. With an RTK hook, write `rtk proxy find ...`, because RTK refuses `-not` and `-delete` and then clears nothing. Then confirm the links: `grep -rhoE 'release-notes/2026/#vXYZ[^"]*' site/ | sort | uniq -c`. CI builds with `--clean` from a new checkout, so the live site is correct. The trap is only a local check that passes incorrectly.
- Sections, in order, only if non-empty: `**What's New:** ✨`, `**Bug Fixes:** 🐛`, `**Other Changes:** ⚙️`.
- Bullet shape: `- **Bold hook, present tense, states the user-facing win** — explanation sentence(s).` Optional trailing `see [Label](relative/path.md#anchor)`, and blockquote warnings `> ⚠️ **Heading.** explanation.` for breaking changes/deprecations.
- **Link what the entry closes.** If a change or a bug fix closes an issue, put the reference at the end of that bullet: `...does not run ([#653](https://github.com/nandyalu/trailarr/issues/653)).` Use `/pull/N` when a pull request delivered the change, and `/discussions/N` for a discussion. Write the markdown link only. Do not write `Fixes`, `Closes`, or `{_target="_blank"}` in a new entry — those forms are from older versions in the same file. A `Closes #N` line goes in the PR body only (sections 4 and 7), so the entry itself must carry the link. To find the references:
    1. Read every subject **and body**: `git log origin/main..dev --format='%h %s%n%b' | grep -oE '#[0-9]{3,4}' | sort -u`. A `Closes #N` line is in the body, not the subject. If an RTK hook rewrites `git` in this shell, put `rtk proxy` in front of `git log`. RTK's compressed log drops the bodies, so without it the command finds almost nothing (v0.13.0: it found 1 reference of 4).
    2. Run `gh pr list --state merged --search "merged:>=<date of the last release>" --json number,author,title,url` and open each result with `gh pr view <n>`.
    3. **Search the open issues for the headline features.** A release can close a request that no commit names. v0.13.0 closed [#511](https://github.com/nandyalu/trailarr/issues/511) ("Use trailers from TMDB"), and no commit or PR mentioned it. Run `gh issue list --state open --search "<feature words>"` for each What's New entry. Read a match before you link it: it must ask for what shipped.
    4. **Drop a change that already shipped.** A merge commit on `dev` (for example, a feature branch that merged an earlier `dev`) brings in old copies of commits that already reached `main` through an earlier release. They appear in `origin/main..dev`, but they are not new. `git cherry origin/main dev` does not find them after a rebase, because the rebase changed the patch. Compare the files instead: `git diff origin/main dev -- <each file the commit touched>` shows no change for a commit that already shipped. v0.13.0 carried the Safari fix (#653) and H22 this way. Both shipped in earlier releases, so neither goes in the new notes.
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
- **The PR can already exist.** A `dev → main` PR is sometimes opened during development (v0.13.0: [#682](https://github.com/nandyalu/trailarr/pull/682)). Look first with `gh pr list --state open --base main --head dev`. If it exists, update it with `gh pr edit <n> --title ... --body-file ...`. Do not open a second PR.
- **Check that GitHub read the closing lines:** `gh pr view <n> --json closingIssuesReferences`. The list can take about 20 seconds to update after an edit. Check it again before you decide that a line is wrong.
- **A title edit starts workflows again.** Opening or editing the PR runs `bump-version.yml` and the README sync. The README sync can push a `github-actions[bot]` commit to `dev` (for example, when step 1.9 changed a badge). That commit is then the PR head, and its checks are the ones that control the merge. Its runs can show `action_required` for a short time before they start.

## 5. Merge

Prefer **"Rebase and merge"**. Fall back to **"Create a merge commit"** only if GitHub blocks the rebase — `dev` has occasionally picked up a `Merge branch 'main' into dev` commit from a prior sync, or a feature-branch merge (v0.13.0: `Merge feat/phase8-tmdb`), and GitHub's rebase-and-merge button refuses to rebase a branch containing merge commits ("this branch can't be rebased" error). Find out in advance with `git log --merges --oneline origin/main..dev`. If that lists anything, tell the user that the merge will probably be a merge commit when you ask them to confirm. Never fall back to squash for this reason, and never force a clean rebase by rewriting `dev` locally and force-pushing — it's shared branch history. Confirm the actual merge with the user before executing it (shared-state, hard to reverse).

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

The push can print `Heads up! The branch 'dev' that you pushed to was renamed to 'trailer-status'`. GitHub keeps an old rename record, and the message is harmless. Confirm with `git ls-remote --heads origin dev main`: both must show the merge commit.

## 7. Create the GitHub release (required — nothing else mints the tag)

No workflow on a `main` push creates the tag or release. Creating the GitHub release is what mints the `vX.Y.Z` tag, and the tag push then triggers `release.yml` (builds the direct-install asset `trailarr-vX.Y.Z-release.tar.gz` + `.sha256`), `docker-publish.yml` (versioned Docker image), and the Discord release notification.

```
gh release create vX.Y.Z --target main --latest \
  --title "vX.Y.Z - Same short title as the PR" \
  --notes-file <file>
```

- **Notes file**: the same release-notes section used for the PR body (heading line included), but **without** any `Closes #N` lines — those are PR-only.
- Verify afterward:
    - The `Release`, `Docker Publish` and `Discord Release Notifications (Stable)` runs succeed (`gh run list` / `gh run watch <id> --exit-status`). Docker Publish takes about 8 minutes.
    - The release shows both asset files: `gh release view vX.Y.Z --json assets`.
    - The image is on **Docker Hub**, not GHCR. The GHCR package lookup returns 404. Check the tags: `curl -s "https://hub.docker.com/v2/repositories/nandyalu/trailarr/tags/?page_size=5&ordering=last_updated"`. Expect `X.Y.Z`, `X.Y` and `latest`, each for `amd64` and `arm64`.
    - Every issue from the `Closes` lines is closed: `gh issue view <n> --json state`. The state can take a few seconds to change after the merge.

## 8. After the release

Record the release in the plans, in the same session, as a `docs(plans)` commit on the new `dev`:

- `plans/README.md`: the release-ladder row for the version (✅ shipped + the date), and the file-index line for the phase.
- The phase file's `**Status:**` line.
- Any parallel-track milestone that shipped in the release (`track-*.md`).
- `docs/references/roadmap.md`, if a date or the content changed.