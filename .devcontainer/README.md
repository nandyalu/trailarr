# Devcontainer Pre-build

This repository includes a GitHub Actions workflow that automatically builds and publishes devcontainer pre-builds to the GitHub Container Registry (GHCR).

## What is a Pre-build?

A devcontainer pre-build is a pre-built container image that contains all the development dependencies and tools needed for the project. This significantly reduces the time needed to start a development environment in GitHub Codespaces or other devcontainer-compatible environments.

## How it Works

The workflow (`.github/workflows/devcontainer-prebuild.yml`) automatically:

1. **Triggers** on changes to any files in the `.devcontainer/` directory
2. **Prepares** the configuration by temporarily using the prebuild config as `devcontainer.json`
3. **Builds** the devcontainer using the clean prebuild configuration
4. **Publishes** the pre-built image to `ghcr.io/nandyalu/trailarr/devcontainer`

## Pre-build Configuration

The pre-build uses a clean configuration (`.devcontainer/devcontainer-prebuild.json`) that:

- ✅ **Includes**: Development tools, extensions, features, environment variables
- ❌ **Omits**: Local-specific runArgs (port mappings) and mounts (local paths)

This ensures the pre-build works across different environments without local machine dependencies.

## Using the Pre-build

### In GitHub Codespaces

When you create a new Codespace, GitHub will automatically use the pre-built image if available, providing a much faster startup experience.

### In Local Development

To use the pre-build locally with the dev container CLI:

```bash
# Build and run using the pre-build configuration
devcontainer up --config .devcontainer/devcontainer-prebuild.json
```

For local development with the full configuration (including local mounts), continue using the original `devcontainer.json`.

## Manual Trigger

The workflow can also be triggered manually from the GitHub Actions tab using the "Build and Publish Devcontainer Pre-build" workflow.