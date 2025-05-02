# Contributing to Trailarr

First off, thank you for considering contributing to Trailarr. It's people like you that make Trailarr such a great tool.

## Getting Started
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/nandyalu/trailarr)

- Fork the repository on GitHub.
- Clone the project to your own machine.
- Open the project in Visual Studio Code.
- Open `.devcontainer > devcontainer.json` and change the `mounts` to your desired folders.
```json
"mounts": [
		"source=/var/appdata/trailarr-dev,target=/config,type=bind,consistency=cached",
		"source=/media/all/Media,target=/media,type=bind,consistency=cached"
	],
```
> Note: Below steps are optional, if you don't want to test any changes that would require connecting to `Radarr` and/or `Sonarr`, you can simply remove the `mounts` section from the `devcontainer.json` file.
> 1. `source` is the path on your host machine.
> 2. `target` is the path inside the devcontainer.
> 3. Change the `mount` for `/data` to a folder where you want to store the data. Do not use the same folder as your production data.
> 4. Change the `mount` for `/media` to the your media folder mapping as set in `Radarr` and/or `Sonarr`.


- VS Code will automatically detect the devcontainer configuration. Click on `Reopen in Container`. This will start the build of the Docker container and place you inside it.
- Make your changes inside the devcontainer. The devcontainer is a fully configured development environment with all the tools you need.
- Commit changes to your own branch.
- Push your work back up to your fork.
- Submit a Pull Request so that we can review your changes.


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

## Commit Message Guidelines

The commit message:

- is written in the imperative (e.g., "Fix ...", "Add ...")
- is kept short, while concisely explaining what the commit does.
- is clear about what part of the code is affected -- often by prefixing with the name of the subsystem and a colon, like "express: ..." or "docs: ...".
- is a complete sentence, ending with a period.

## License

By contributing, you agree that your contributions will be licensed under its [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file).
