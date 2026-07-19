#!/bin/sh
# Trailarr installer bootstrap — Linux and macOS
#
# Usage:
#   curl -LsSf https://raw.githubusercontent.com/nandyalu/trailarr/main/install.sh | sudo sh
#
# Prerequisites: uv  (https://docs.astral.sh/uv/)
#   curl -LsSf https://astral.sh/uv/install.sh | sh

set -e

GITHUB_REPO="nandyalu/trailarr"
PYTHON_VERSION="3.13"

# --------------------------------------------------------------------------
# Terminal colours (safe subset — no tput dependency)
# --------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; RESET='\033[0m'

info()    { printf "${CYAN}  →  %s${RESET}\n" "$*"; }
success() { printf "${GREEN}  ✓  %s${RESET}\n" "$*"; }
warning() { printf "${YELLOW}  ⚠  %s${RESET}\n" "$*"; }
error()   { printf "${RED}  ✗  %s${RESET}\n" "$*" >&2; }
banner()  {
    printf "${BLUE}"
    cat <<'EOF'
 _____ ____      _    ___ _        _    ____  ____
|_   _|  _ \    / \  |_ _| |      / \  |  _ \|  _ \
  | | | |_) |  / _ \  | || |     / _ \ | |_) | |_) |
  | | |  _ <  / ___ \ | || |___ / ___ \|  _ <|  _ <
  |_| |_| \_\/_/   \_\___|_____/_/   \_\_| \_\_| \_\

EOF
    printf "${RESET}"
    printf "${CYAN}  Bootstrap Installer — Linux & macOS${RESET}\n\n"
}

# --------------------------------------------------------------------------
# Cleanup on exit
# --------------------------------------------------------------------------
TEMP_DIR=""
cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT INT TERM

# --------------------------------------------------------------------------
# Check prerequisites
# --------------------------------------------------------------------------
check_uv() {
    if command -v uv >/dev/null 2>&1; then
        success "uv found: $(uv --version)"
        return
    fi

    # Under `curl | sudo sh`, root's PATH usually lacks the per-user uv that
    # the standard uv install script puts in ~/.local/bin. Probe the invoking
    # user's install locations and prepend to PATH (also needed later by the
    # Python installer, which looks uv up in PATH).
    SUDO_HOME=""
    if [ -n "${SUDO_USER:-}" ]; then
        SUDO_HOME=$(eval echo "~$SUDO_USER" 2>/dev/null || true)
    fi
    for candidate in \
        "${SUDO_HOME:+$SUDO_HOME/.local/bin}" \
        "$HOME/.local/bin" \
        /opt/homebrew/bin \
        /usr/local/bin; do
        if [ -n "$candidate" ] && [ -x "$candidate/uv" ]; then
            PATH="$candidate:$PATH"
            export PATH
            success "uv found: $("$candidate/uv" --version) (from $candidate)"
            return
        fi
    done

    error "uv is not installed (or not in root's PATH)."
    printf "\n  Install uv first (one command):\n"
    printf "    ${YELLOW}curl -LsSf https://astral.sh/uv/install.sh | sh${RESET}\n\n"
    printf "  Then re-run this installer.\n\n"
    exit 1
}

check_curl() {
    if ! command -v curl >/dev/null 2>&1; then
        error "curl is required. Install it and re-run."
        exit 1
    fi
}

# --------------------------------------------------------------------------
# Download latest release asset
# --------------------------------------------------------------------------
download_release() {
    # Pin a specific release with: TRAILARR_VERSION=v0.9.9 (defaults to latest)
    if [ -n "${TRAILARR_VERSION:-}" ]; then
        info "Fetching release information for ${TRAILARR_VERSION}..."
        RELEASE_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/tags/${TRAILARR_VERSION}"
    else
        info "Fetching latest release information..."
        RELEASE_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
    fi
    RELEASE_JSON=$(curl -fsSL \
        -H "Accept: application/vnd.github+json" \
        "$RELEASE_URL") || {
        error "Failed to fetch release info from GitHub API"
        printf "  If this repeats, you may be rate-limited (60 requests/hour per IP)\n"
        printf "  or the requested version tag may not exist.\n"
        exit 1
    }

    APP_VERSION=$(printf '%s' "$RELEASE_JSON" | grep '"tag_name"' | head -n1 | cut -d'"' -f4)
    success "Installing version: ${APP_VERSION}"

    # Prefer the pre-built release asset (includes frontend-build).
    # Match the URL end exactly so the .sha256 sibling asset is not picked up.
    ASSET_URL=$(printf '%s' "$RELEASE_JSON" | grep '"browser_download_url"' | grep 'release\.tar\.gz"' | head -n1 | cut -d'"' -f4)

    if [ -z "$ASSET_URL" ]; then
        error "No release asset found for version ${APP_VERSION}."
        printf "  The release asset 'trailarr-*-release.tar.gz' is missing.\n"
        printf "  Check https://github.com/${GITHUB_REPO}/releases for details.\n"
        exit 1
    fi

    TEMP_DIR=$(mktemp -d)
    ARCHIVE="${TEMP_DIR}/trailarr-release.tar.gz"

    info "Downloading ${APP_VERSION}..."
    curl -fL --progress-bar -o "$ARCHIVE" "$ASSET_URL" || {
        error "Download failed"
        exit 1
    }
    printf '\r\033[K'
    success "Download complete"

    # Verify checksum when the release publishes one (older releases don't)
    SHA_URL=$(printf '%s' "$RELEASE_JSON" | grep '"browser_download_url"' | grep 'release\.tar\.gz\.sha256"' | head -n1 | cut -d'"' -f4)
    if [ -n "$SHA_URL" ]; then
        EXPECTED=$(curl -fsSL "$SHA_URL" | cut -d' ' -f1)
        if command -v sha256sum >/dev/null 2>&1; then
            ACTUAL=$(sha256sum "$ARCHIVE" | cut -d' ' -f1)
        else
            ACTUAL=$(shasum -a 256 "$ARCHIVE" | cut -d' ' -f1)
        fi
        if [ -n "$EXPECTED" ] && [ "$EXPECTED" != "$ACTUAL" ]; then
            error "Checksum mismatch for downloaded archive."
            printf "  expected: %s\n  actual:   %s\n" "$EXPECTED" "$ACTUAL"
            exit 1
        fi
        success "Checksum verified"
    fi

    info "Extracting archive..."
    tar -xzf "$ARCHIVE" -C "$TEMP_DIR"
    SOURCE_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n1)

    if [ -z "$SOURCE_DIR" ]; then
        error "Could not find extracted release directory"
        exit 1
    fi
    success "Archive extracted"
}

# --------------------------------------------------------------------------
# Run the Python installer
# --------------------------------------------------------------------------
run_installer() {
    INSTALLER="${SOURCE_DIR}/scripts/install/install.py"

    if [ ! -f "$INSTALLER" ]; then
        error "Installer script not found at: ${INSTALLER}"
        exit 1
    fi

    info "Launching Trailarr Python installer..."
    printf "\n"

    uv run \
        --python "${PYTHON_VERSION}" \
        --with rich \
        --with tzlocal \
        "$INSTALLER" \
        --source-dir "$SOURCE_DIR" \
        --version "$APP_VERSION"
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
banner
check_curl
check_uv
download_release
run_installer
