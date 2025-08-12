#!/bin/bash

# Trailarr Bare Metal Pre-Start Script
# This script runs before the main application starts using modular components

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
SCRIPTS_DIR="$INSTALL_DIR/scripts"

# Source the box_echo function
source "$SCRIPTS_DIR/box_echo.sh"

# Source environment variables
if [ -f "$INSTALL_DIR/.env" ]; then
    source "$INSTALL_DIR/.env"
fi

# Set default environment variables if not set
export APP_NAME=${APP_NAME:-"Trailarr"}
export APP_PORT=${APP_PORT:-7889}
export APP_DATA_DIR=${APP_DATA_DIR:-"/var/lib/trailarr"}
export APP_VERSION=${APP_VERSION:-"0.5.0"}
export TZ=${TZ:-"UTC"}
export INSTALLATION_MODE=${INSTALLATION_MODE:-"baremetal"}

# Use modular banner display (adapted from container scripts)
display_startup_banner() {
    box_echo ""
    box_echo "               App Version: ${APP_VERSION}"
    box_echo ""
    box_echo "--------------------------------------------------------------------------"
    box_echo "Starting Trailarr (Bare Metal) with the following configuration:"
    box_echo "APP_DATA_DIR: ${APP_DATA_DIR}"
    box_echo "APP_PORT: ${APP_PORT}"
    box_echo "TZ: ${TZ}"
    box_echo "USER: $(whoami)"
    box_echo "INSTALLATION_MODE: ${INSTALLATION_MODE}"
    box_echo "--------------------------------------------------------------------------"
}

# Configure timezone (adapted from container scripts)
configure_timezone() {
    box_echo "Current date time: $(date)"
    box_echo "Setting TimeZone to ${TZ}"
    
    # Try to set timezone (may not work without sudo)
    if command -v timedatectl &> /dev/null; then
        timedatectl set-timezone "${TZ}" 2>/dev/null || box_echo "Warning: Could not set timezone (may require root privileges)"
    else
        box_echo "Warning: timedatectl not available, timezone not changed"
    fi
    
    box_echo "Current date time after update: $(date)"
    box_echo "--------------------------------------------------------------------------"
}

# Setup directories (adapted from container scripts)
setup_directories() {
    box_echo "Creating required directories"
    
    # Create data directories
    mkdir -p "${APP_DATA_DIR}/logs"
    mkdir -p "${APP_DATA_DIR}/backups"
    mkdir -p "${APP_DATA_DIR}/web/images"
    mkdir -p "${APP_DATA_DIR}/config"
    mkdir -p "${INSTALL_DIR}/tmp"
    
    # Set proper permissions
    chmod -R 755 "${APP_DATA_DIR}" 2>/dev/null || true
    chmod -R 755 "${INSTALL_DIR}/assets" 2>/dev/null || true
    chmod -R 755 "${INSTALL_DIR}/tmp" 2>/dev/null || true
    
    box_echo "✓ Directory setup complete"
    box_echo "--------------------------------------------------------------------------"
}

# Load environment configuration
load_environment() {
    box_echo "Loading environment configuration"
    
    # Load environment from .env file
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
        box_echo "✓ Environment loaded from $INSTALL_DIR/.env"
    else
        box_echo "⚠ No .env file found, using defaults"
    fi
    
    # Export Python path
    export PYTHONPATH="${INSTALL_DIR}/backend"
    
    # Update PATH for local binaries
    if [ -d "$INSTALL_DIR/bin" ]; then
        export PATH="$INSTALL_DIR/bin:$PATH"
        box_echo "✓ Local binaries added to PATH"
    fi
    
    box_echo "--------------------------------------------------------------------------"
}

# Update yt-dlp if update script exists
update_ytdlp() {
    box_echo "Checking yt-dlp version and updates..."
    
    if [ -f "$INSTALL_DIR/scripts/update_ytdlp_local.sh" ]; then
        bash "$INSTALL_DIR/scripts/update_ytdlp_local.sh" || box_echo "Warning: yt-dlp update failed"
    elif [ -f "$INSTALL_DIR/venv/bin/yt-dlp" ]; then
        YTDLP_VERSION=$("$INSTALL_DIR/venv/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
        box_echo "✓ yt-dlp version: $YTDLP_VERSION"
    else
        box_echo "⚠ yt-dlp not found in virtual environment"
    fi
    
    box_echo "--------------------------------------------------------------------------"
}

# Load GPU status from environment file (already set by gpu_setup.sh during installation)
load_gpu_status() {
    box_echo "Loading GPU hardware acceleration status"
    
    # GPU availability is already set in .env file by gpu_setup.sh during installation
    # We just need to export them for the application
    export GPU_AVAILABLE_NVIDIA="${GPU_AVAILABLE_NVIDIA:-false}"
    export GPU_AVAILABLE_INTEL="${GPU_AVAILABLE_INTEL:-false}"
    export GPU_AVAILABLE_AMD="${GPU_AVAILABLE_AMD:-false}"
    
    if [ "$ENABLE_HWACCEL" = "true" ] && [ "$HWACCEL_TYPE" != "none" ]; then
        case "$HWACCEL_TYPE" in
            "nvidia")
                if [ "$GPU_AVAILABLE_NVIDIA" = "true" ] && command -v nvidia-smi &> /dev/null; then
                    box_echo "✓ NVIDIA GPU acceleration enabled and available"
                else
                    box_echo "⚠ NVIDIA GPU acceleration enabled but may not be available"
                fi
                ;;
            "intel")
                if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
                    box_echo "✓ Intel GPU acceleration enabled and available"
                else
                    box_echo "⚠ Intel GPU acceleration enabled but may not be available"
                fi
                ;;
            "amd")
                if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
                    box_echo "✓ AMD GPU acceleration enabled and available"
                else
                    box_echo "⚠ AMD GPU acceleration enabled but may not be available"
                fi
                ;;
        esac
    else
        box_echo "GPU hardware acceleration disabled"
    fi
    
    box_echo "--------------------------------------------------------------------------"
}

# Main pre-start function
main() {
    display_startup_banner
    configure_timezone
    setup_directories
    load_environment
    update_ytdlp
    load_gpu_status
    
    box_echo "Pre-start checks complete - ready to start application"
    box_echo "=========================================================================="
}

# Run main function
main "$@"