# Contributing to Trailarr

First off, thank you for considering contributing to Trailarr. It's people like you that make Trailarr such a great tool.

**The full contributing guide lives in the documentation:**
👉 **<https://nandyalu.github.io/trailarr/references/contributing/>**

It covers how to set up a development environment (devcontainer or your own machine), the code style, how to run the tests, what a good pull request looks like, and how to use AI tools on this project.

If you are stuck or unsure about something, ask on our [Discord Server](https://discord.gg/KKPr5kQEzQ). We are happy to help.

## The short version

- Fork the repository, create a branch, and open your pull request against the `dev` branch.
- All features and bug fixes **must have tests**. Run `pytest` for the backend and `npm run test` plus `npm run build` for the frontend before you ask for a review.
- Format Python with Black, using the project's settings — **not** Black's defaults:
  `black --preview --enable-unstable-feature string_processing --line-length=79 <files>`
  Format only the lines you change. A whole-file reformat hides your change and causes conflicts.
- Format the frontend with Prettier, using `frontend/.prettierrc`.
- Add a release-notes entry and update the documentation pages your change affects, in the same pull request.
- Do not change version numbers. A GitHub action does that when the release pull request opens.
- Using an AI assistant is fine. Read and test everything you submit, keep the diff to your actual change, and say in the pull request that you used one. See [Using AI tools](https://nandyalu.github.io/trailarr/references/contributing/#using-ai-tools).

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](https://github.com/nandyalu/trailarr?tab=coc-ov-file). By participating, you are expected to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under its [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file).
