#!/bin/bash

# Trailarr Bare Metal Pre-Start Script
# This script runs before the main application starts using modular components

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
SCRIPTS_DIR="$INSTALL_DIR/scripts"
DATA_DIR="/var/lib/trailarr"

# Source the logging functions

# Initialize logging for runtime
INSTALL_LOG_FILE="/var/log/trailarr/prestart.log"
mkdir -p "$(dirname "$INSTALL_LOG_FILE")"
touch "$INSTALL_LOG_FILE"
export INSTALL_LOG_FILE


# Source environment variables
if [ -f "$DATA_DIR/.env" ]; then
    source "$DATA_DIR/.env"
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
    echo ""
    echo "               App Version: ${APP_VERSION}"
    echo ""
    echo "--------------------------------------------------------------------------"
    echo "Starting Trailarr (Bare Metal) with the following configuration:"
    echo "APP_DATA_DIR: ${APP_DATA_DIR}"
    echo "APP_PORT: ${APP_PORT}"
    echo "USER: $(whoami)"
    echo "INSTALLATION_MODE: ${INSTALLATION_MODE}"
    echo "--------------------------------------------------------------------------"
}

# Setup directories (adapted from container scripts)
setup_directories() {
    echo "Creating required directories"
    
    # Create data directories
    echo "Creating data directories"
    mkdir -p "${APP_DATA_DIR}/logs"
    mkdir -p "${APP_DATA_DIR}/backups"
    mkdir -p "${APP_DATA_DIR}/web/images"
    mkdir -p "${APP_DATA_DIR}/config"
    mkdir -p "${INSTALL_DIR}/tmp"
    
    # Set proper permissions
    echo "Setting directory permissions"
    chown trailarr:trailarr "${APP_DATA_DIR}"
    chown trailarr:trailarr "${INSTALL_DIR}"
    chmod -R 755 "${APP_DATA_DIR}" 2>/dev/null || true
    chmod -R 755 "${INSTALL_DIR}/assets" 2>/dev/null || true
    chmod -R 755 "${INSTALL_DIR}/tmp" 2>/dev/null || true
    
    echo "Directory setup complete"
    echo "--------------------------------------------------------------------------"
}

# Load environment configuration
load_environment() {
    echo "Loading environment configuration"
    
    # Load environment from .env file
    if [ -f "$DATA_DIR/.env" ]; then
        source "$DATA_DIR/.env"
        echo "✓ Environment loaded from $DATA_DIR/.env"
    else
        echo "⚠ No .env file found, using defaults"
    fi
    
    # Export Python path
    export PYTHONPATH="${DATA_DIR}/backend"
    
    # Update PATH for local binaries
    if [ -d "$DATA_DIR/bin" ]; then
        export PATH="$DATA_DIR/bin:$PATH"
        echo "✓ Local binaries added to PATH"
    fi
    
    echo "Environment configuration loaded"
    echo "--------------------------------------------------------------------------"
}

# Update yt-dlp if update script exists
update_ytdlp() {
    echo "Checking yt-dlp version and updates"
    
    if [ -f "$INSTALL_DIR/scripts/update_ytdlp_local.sh" ]; then
        echo "Running yt-dlp update script"
        if bash "$INSTALL_DIR/scripts/update_ytdlp_local.sh"; then
            echo "✓ yt-dlp update completed"
        else
            echo "⚠ yt-dlp update failed"
        fi
    elif [ -f "$INSTALL_DIR/backend/.venv/bin/yt-dlp" ]; then
        YTDLP_VERSION=$("$INSTALL_DIR/backend/.venv/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
        echo "✓ yt-dlp version: $YTDLP_VERSION"
    else
        echo "⚠ yt-dlp not found in virtual environment"
    fi
    
    echo "yt-dlp check complete"
    echo "--------------------------------------------------------------------------"
}

# Load GPU status from environment file (already set by gpu_setup.sh during installation)
load_gpu_status() {
    echo "Loading GPU hardware acceleration status"
    
    # GPU availability is already set in .env file by gpu_setup.sh during installation
    # We just need to export them for the application
    export GPU_AVAILABLE_NVIDIA="${GPU_AVAILABLE_NVIDIA:-false}"
    export GPU_AVAILABLE_INTEL="${GPU_AVAILABLE_INTEL:-false}"
    export GPU_AVAILABLE_AMD="${GPU_AVAILABLE_AMD:-false}"
    
    if [ "$ENABLE_HWACCEL" = "true" ] && [ "$HWACCEL_TYPE" != "none" ]; then
        case "$HWACCEL_TYPE" in
            "nvidia")
                if [ "$GPU_AVAILABLE_NVIDIA" = "true" ] && command -v nvidia-smi &> /dev/null; then
                    echo "✓ NVIDIA GPU acceleration enabled and available"
                else
                    echo "⚠ NVIDIA GPU acceleration enabled but may not be available"
                fi
                ;;
            "intel")
                if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
                    echo "✓ Intel GPU acceleration enabled and available"
                else
                    echo "⚠ Intel GPU acceleration enabled but may not be available"
                fi
                ;;
            "amd")
                if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
                    echo "✓ AMD GPU acceleration enabled and available"
                else
                    echo "⚠ AMD GPU acceleration enabled but may not be available"
                fi
                ;;
        esac
    else
        echo "GPU hardware acceleration disabled"
    fi
    
    echo "GPU status loaded"
    echo "--------------------------------------------------------------------------"
}

# Main pre-start function
main() {
    echo "=========================================================================="
    display_startup_banner
    setup_directories
    load_environment
    update_ytdlp
    load_gpu_status
    
    echo "Pre-start checks complete - ready to start application"
    echo "=========================================================================="
}

# Run main function
main "$@"