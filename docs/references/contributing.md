# Contributing to Trailarr

First off, thank you for considering contributing to Trailarr. It's people like you that make Trailarr such a great tool.

> **Note:** If you want to contribute, but are stuck or unsure about something, please reach out on our [Discord Server](https://discord.gg/KKPr5kQEzQ){:target="_blank"}. We are happy to help! Don't hesitate to ask for help and don't stress yourself out! We can work out things as long as you are friendly and respectful.

## Getting Started
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/nandyalu/trailarr)

- Fork the repository on GitHub.
- Clone the project to your own machine.
- Open the project in Visual Studio Code.
- Open `.devcontainer > devcontainer.json` and uncomment / change the options as needed (especially the `mounts` section).
	> See [devcontainer.json](https://code.visualstudio.com/docs/devcontainers/devcontainerjson-reference) for more information on how to set up the devcontainer.

- VS Code will automatically detect the devcontainer configuration. Click on `Reopen in Container`. If not, open the command palette (Ctrl+Shift+P) and select `Remote-Containers: Reopen in Container`.
- Wait for the container to build. This may take a few minutes.
- Once the container is built, you will be inside the devcontainer. It should already have all the dependencies installed.
- Commit changes to your own branch.
- Push your work back up to your fork.
- Submit a Pull Request so that we can review your changes.
- If you are working on a new feature, please create a new branch for your changes. This will make it easier for us to review your changes and merge them into the main branch.
> NOTE: Be sure to merge the latest from "upstream" before making a pull request!

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](https://github.com/nandyalu/trailarr?tab=coc-ov-file). By participating, you are expected to uphold this code.

## Issue Process

Issues are very valuable to this project.

- Ideas are a valuable source of contributions others can make
- Problems show where this project is lacking
- With a question, you show where contributors can improve the user experience

Thank you for creating them.

## Pull Request Process

- Ensure any install or build dependencies are removed before the end of the layer when doing a build.
- Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
- Increase the version numbers in any examples files and the README.md to the new version that this Pull Request would represent. The versioning scheme we use is SemVer.
- You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Code Style

To ensure consistency throughout the source code, keep these rules in mind as you are working:

- All features or bug fixes **must be tested** by one or more specs (unit tests).
- Your code should follow the syntax style of the existing code (PEP-8 for Python code, formatted using black formatter, and the Angular Style Guide for Angular code).

### Python / Backend Code Style

Python code should follow the below guidelines:

- Use [black formatter](https://github.com/psf/black) for formatting the code. Formatting styles are already set up in the devcontainer.
- Follow [PEP-8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
- Set `type checking` to `standard`.
- Do not raise generice exceptions. Use specific exceptions instead. If an appropriate exception is not already available, contact a dev and create a new one after discussing.
- When raising an exception, always include a message that describes the error. This is important for debugging and understanding what went wrong.
- Log the error message where it's caught, NOT at the source when raising the exception.
- When logging a message related to a media item, include the media item ID in square brackets. Frontend will detect this and add a link to the media details page.
- Use `f-strings` for string formatting, use `str.format()` only when you want to replace from a dictionary.

### Docs Preview

There is a Github action that builds docs preview and adds a comment in the PR with a link to the preview build of docs.

## Commit Message Guidelines

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
- I then created a new GPG key using the following command:
	```bash
	gpg --full-generate-key
	```
- I followed the prompts to create a new key, and then I added the key to my GitHub account, and follow the steps to enable commit signing in vscode. See [this](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key) for more information.
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
	> I guess the cache values are not necessary if you don't want your passphrase to be cached!
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

By contributing, you agree that your contributions will be licensed under its [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file).
