# Contributing to Trailarr

First off, thank you for considering contributing to Trailarr. It's people like you that make Trailarr such a great tool.

> **Note:** If you want to contribute, but are stuck or unsure about something, please reach out on our [Discord Server](https://discord.gg/KKPr5kQEzQ){:target="_blank"}. We are happy to help! Don't hesitate to ask for help and don't stress yourself out! We can work out things as long as you are friendly and respectful.

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](https://github.com/nandyalu/trailarr?tab=coc-ov-file). By participating, you are expected to uphold this code.

## Issues

Issues are very valuable to this project.

- Ideas are a valuable source of contributions others can make
- Problems show where this project is lacking
- With a question, you show where contributors can improve the user experience

Thank you for creating them.

---

## Set up your development environment

{{ version_badge("upd", "0.11.3") }}

You can use the devcontainer, or install the tools on your own machine. Both give you the same result.

### Option 1: Devcontainer (recommended)

[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/nandyalu/trailarr)

1. Fork the repository on GitHub, then clone your fork.
2. Open the project in Visual Studio Code.
3. Open `.devcontainer/devcontainer.json` and change the options as needed, especially the `mounts` section. See [devcontainer.json](https://code.visualstudio.com/docs/devcontainers/devcontainerjson-reference) for a reference.
4. Click **Reopen in Container** when VS Code asks. If it does not ask, open the command palette (++ctrl+shift+p++) and select **Dev Containers: Reopen in Container**.
5. Wait for the container to build. This takes a few minutes. All dependencies and the editor settings are installed for you.

### Option 2: Local machine

You need [uv](https://docs.astral.sh/uv/) for the backend and [Node.js](https://nodejs.org/) 22 or later for the frontend.

```bash
# Backend dependencies (from the repository root)
cd backend && uv sync

# Frontend dependencies
cd ../frontend && npm install
```

Trailarr needs `APP_DATA_DIR` for every backend command. It holds the database, the logs, and the config file.

```bash
# One-time: create a data folder and the database
mkdir -p /tmp/trailarr-config/logs /tmp/trailarr-config/web
cd backend && APP_DATA_DIR=/tmp/trailarr-config uv run alembic upgrade head

# Run the backend (http://localhost:7888)
PYTHONPATH=$(pwd) APP_DATA_DIR=/tmp/trailarr-config uv run uvicorn main:trailarr_api --host 0.0.0.0 --port 7888

# Run the frontend in another terminal (http://localhost:4200)
cd frontend && npm run start
```

!!! tip "Test your change in the real app"
    `npm run build` and the unit tests do not prove that a change works. To see the app as a user does, build the frontend and start the app with `python3 scripts/launch.py` from the repository root. This serves the API and the built frontend together on port 7890, which is the same path a real install uses.

---

## Code style

All features and bug fixes **must have tests**.

### Python (backend)

Trailarr formats Python with [Black](https://github.com/psf/black), but **not with Black's default settings**. The project uses a 79-column limit. The devcontainer applies this for you. If you work on your own machine, use exactly these options:

```bash
black --preview --enable-unstable-feature string_processing --line-length=79 <files>
```

!!! warning "Format only the lines you change"
    Black's default width is 88 columns. If you format a whole file with the defaults, it rewraps code that has nothing to do with your change. The diff then becomes hard to review, and the next person to touch the file gets a conflict. Keep your pull request to the lines you actually changed.

More Python rules:

- Follow [PEP-8](https://www.python.org/dev/peps/pep-0008/).
- Set `type checking` to `standard`.
- Do not raise generic exceptions. Use a specific exception. If none fits, ask a maintainer before you add one.
- Always give an exception a message that describes the error.
- Log the error where you catch it, not where you raise it.
- Put the media item id in square brackets in log messages about a media item, for example `'Some Movie' [123]`. The web interface turns this into a link.
- Use f-strings. Use `str.format()` only to fill values from a dictionary.
- Use relative imports inside a package, and absolute imports everywhere else.

### TypeScript and Angular (frontend)

- Follow the [Angular Style Guide](https://angular.dev/style-guide).
- Format with [Prettier](https://prettier.io/). The settings live in `frontend/.prettierrc` (140 columns, single quotes, no bracket spacing).
- Write standalone components and use Angular Signals. The app runs zoneless.
- Use the Material Design 3 CSS custom properties for colors and shadows. Never hardcode a color.

### Documentation

- Write each paragraph on ONE line. Do not wrap prose across lines: the docs build renders continuous lines correctly, but a paragraph split over several lines can break the formatting.
- Write in [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/): short sentences, one idea per sentence, active voice, simple words, present tense. This applies to documentation, log messages, and comments that you add or change.
- Mark new or changed sections with a version badge, for example `{{ "{{ version_badge(\"add\", \"0.11.3\") }}" }}`.
- Build the docs with `uv run --project backend zensical build` from the repository root.

---

## Tests

Run both suites before you open a pull request.

```bash
# Backend — about 900 tests, ~45 seconds
cd backend && PYTHONPATH=$(pwd) uv run python -m pytest tests/ -v

# Frontend — Vitest
cd frontend && npm run test

# Frontend production build
npm run build
```

If you change anything in `backend/api/`, regenerate the API client:

```bash
cd backend && uv run python ./export_openapi.py
```

---

## Pull requests

- Create a branch for your change. Open the pull request against the `dev` branch.
- Keep the pull request to one subject. A small, focused diff is reviewed and merged faster.
- Add a release-notes entry in `docs/release-notes/2026.md`, under a heading for the next version. A maintainer sets the release date.
- Update the documentation pages that your change affects, in the same pull request.
- **Do not change the version numbers.** A GitHub action sets the version in `pyproject.toml`, `package.json`, and the OpenAPI spec when the release pull request opens.
- Merge the latest `dev` into your branch before you ask for a review.

### About the checks

Some checks do not pass for a pull request from a fork, because a fork cannot read the repository secrets. `Push Docker image (nightly) to Docker Hub` fails with `Username and password required` for every fork pull request. This is expected, and a maintainer will not hold your pull request for it.

---

## Using AI tools

{{ version_badge("add", "0.11.3") }}

AI assistants are welcome here. Many good contributions to this project were written with one. There is one rule behind everything below: **you are the author, so you answer for the code.**

**Before you open the pull request:**

- Read and understand every line you submit. If you cannot explain why a line is there, do not submit it.
- Run the tests and the build on your machine. Do not trust a summary that says the tests pass.
- Test the behavior in the real app when your change affects behavior. AI tools are good at code that looks correct and does the wrong thing.
- Check the diff for changes you did not intend. AI tools often reformat a whole file, rename variables, or "improve" code that has nothing to do with your change. Remove them: they hide your real change and cause conflicts.
- Use the project's formatter settings, not the tool's defaults. See [Code style](#code-style).

**In the pull request:**

- Tell us that you used an AI tool, and which one. This is not a problem, and it helps a reviewer know where to look closely.
- Write the description yourself, in your own words. Explain the problem, and how you tested the fix. A description that lists what an AI did is not useful to a reviewer.
- Do not paste an AI report of a test run as evidence. Give the numbers you saw.
- The [License](#license) confirmation applies to code that an AI tool wrote for you. You submit the code, so you confirm that you hold the rights to license it under the GPL-3.0.

**What we do not accept:**

- Issues or pull requests generated in bulk, without a real problem behind them.
- Large refactors that no human reviewed.
- Changes to code that you cannot test.

If an AI tool tells you something about this project that this documentation does not say, trust the documentation. The tools are confident and often wrong about project-specific rules, for example the formatting width above.

---

## Commit messages

The commit message:

- is written in the imperative (e.g., "Fix ...", "Add ...")
- is kept short, while concisely explaining what the commit does.
- is clear about what part of the code is affected -- often by prefixing with the name of the subsystem and a colon, like "express: ..." or "docs: ...".
- is a complete sentence, ending with a period.

### Commit Signing Error

If you get an error like `gpg: signing failed: Inappropriate ioctl for device` while committing, you can test signing by running the following command:

```bash
echo "This is a test message for GPG signing." | gpg --clearsign
```

Commit signing is not required, but it is recommended for security purposes. If you are not familiar with GPG signing, you can find more information on how to set it up [here](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

It took me a while to figure out how to set it up inside devcontainer, so I thought it would be helpful to include it here.

- My development machine is an Ubuntu server, so I installed `gnupg2`, `gpg-agent`, and `pinentry-curses` using the following command:
	```bash
	sudo apt-get install gnupg2 gpg-agent pinentry-curses
	```
- I followed the prompts to create a new key, and then I added the key to my GitHub account, and follow the steps to enable commit signing in vscode. See [this](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key) for more information. Here are the commands to generate and set it in `git` and `Github`:
	
	1. Created a new GPG key using the following command:
		```bash
		gpg --full-generate-key
		# You can use any kind of key, recommended is ECC (sign only is enough)
		# Use `Curve 25519` for elliptic curve
		# How long key should be valid is upto you (you need to regenerate a new one when expired)
		# Real name: <Use the display name in your Github account, it will be displayed on signed commit signatures>
		# Email address: <You could use either your email you use for Github OR Github noreply account>
		# If asked for Comment, you can leave it empty
		```

	1. Now, get the long format of the generated key
		```bash
		gpg --list-secret-keys --keyid-format=long
		# You will get output like below, we need `D38DD074ABF2FB6B` for our next step
		# ---------------------------
		# sec   ed25519/D38DD074ABF2FB6B 2026-04-27 [SC]
		#       42ED8106CBFBEB34FA7DDC57D38DD074ABF2FB6B
		# uid                 [ultimate] Uma Nandyala <18457369+nandyalu@users.noreply.github.com>
		# ssb   cv25519/D571BBA1971C36E7 2026-04-27 [E]
		```
	
	1. Get the Public key to add to Github.

		!!! tip ""
			Copy everything from the output, including the `-----BEGIN PGP PUBLIC KEY BLOCK-----` and `-----END PGP PUBLIC KEY BLOCK-----`.
		
		```bash
		gpg --armor --export D38DD074ABF2FB6B
		```
	1. Go to Githib Account Settings and add it under `SSH and GPG Keys` > `New GPG Key` and paste the Public key from last step, give it a name to identify this key (useful if you want to delete it later). More info on [Github](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account).

	1. One last step is to tell local git to use this key for signing commits. 
		```bash
		git config --global user.signingkey D38DD074ABF2FB6B
		git config --global commit.gpgsign true
		git config --global tag.gpgsign true
		```

		!!! note ""
			Note that we are setting `--global` so this works for all commits from that machine, remove that to only use that for this repo.

- I then added the following lines to my `~/.bashrc` file:
	```bash
	export GPG_TTY=$(tty)
	gpg-connect-agent updatestartuptty /bye >/dev/null
	```
- Set the following configuration:
	- `gpg.conf` file which is located in `~/.gnupg/gpg.conf`:
	```bash
	pinentry-mode loopback
	```
	- `gpg-agent.conf` file which is located in `~/.gnupg/gpg-agent.conf`:
	```bash
	default-cache-ttl 360000
	max-cache-ttl 720000
	default-cache-ttl-ssh 60480000
	max-cache-ttl-ssh 60480000
	allow-loopback-pinentry
	pinentry-program /usr/bin/pinentry-curses
	```
	!!! tip ""
		I guess the cache values are not necessary if you don't want your passphrase to be cached!
- I then restarted the `gpg-agent` using the following command:
	```bash
	gpgconf --kill gpg-agent
	```
- devcontainer will automatically forward your GPG agent to the container, however it does not forward your GPG configuration files. So you need to mount your `~/.gnupg` folder to the container, by adding / uncommenting the following line in your `devcontainer.json` file:
	```json
	"mounts": [
		"source=${localEnv:HOME}/.gnupg,target=/root/.gnupg,type=bind,consistency=cached"
	]
	```
- Restart the devcontainer and you should be able to sign your commits now.
- If you are using a different operating system, you can find more information on how to set up GPG signing [here](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).
- If you are using a different terminal, you may need to set the `pinentry-program` to the appropriate program for your terminal. For example, if you are using `zsh`, you can set it to `pinentry-mac` or `pinentry-gtk-2` depending on your setup.
- Hope this helps!


## License

By submitting a pull request, you agree to license your contribution under the [GNU General Public License v3.0 (GPL-3.0)](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file). You confirm that you hold the necessary rights to grant this license.
