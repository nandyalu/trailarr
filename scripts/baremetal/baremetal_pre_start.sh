#!/bin/bash

# Trailarr Bare Metal Pre-Start Script
# This script runs before the main application starts using modular components

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
SCRIPTS_DIR="$INSTALL_DIR/scripts"

# Source the logging functions
source "$SCRIPTS_DIR/baremetal/logging.sh"

# Initialize logging for runtime
INSTALL_LOG_FILE="/var/log/trailarr/prestart.log"
mkdir -p "$(dirname "$INSTALL_LOG_FILE")"
touch "$INSTALL_LOG_FILE"
export INSTALL_LOG_FILE

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
    show_message ""
    show_message "               App Version: ${APP_VERSION}"
    show_message ""
    show_message "--------------------------------------------------------------------------"
    show_message "Starting Trailarr (Bare Metal) with the following configuration:"
    show_message "APP_DATA_DIR: ${APP_DATA_DIR}"
    show_message "APP_PORT: ${APP_PORT}"
    show_message "TZ: ${TZ}"
    show_message "USER: $(whoami)"
    show_message "INSTALLATION_MODE: ${INSTALLATION_MODE}"
    show_message "--------------------------------------------------------------------------"
}

# Setup directories (adapted from container scripts)
setup_directories() {
    start_message "Creating required directories"
    
    # Create data directories
    show_temp_message "Creating data directories"
    mkdir -p "${APP_DATA_DIR}/logs"
    mkdir -p "${APP_DATA_DIR}/backups"
    mkdir -p "${APP_DATA_DIR}/web/images"
    mkdir -p "${APP_DATA_DIR}/config"
    mkdir -p "${INSTALL_DIR}/tmp"
    
    # Set proper permissions
    show_temp_message "Setting directory permissions"
    chmod -R 755 "${APP_DATA_DIR}" 2>/dev/null || true
    chmod -R 755 "${INSTALL_DIR}/assets" 2>/dev/null || true
    chmod -R 755 "${INSTALL_DIR}/tmp" 2>/dev/null || true
    
    end_message "Directory setup complete"
}

# Load environment configuration
load_environment() {
    start_message "Loading environment configuration"
    
    # Load environment from .env file
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
        show_message $GREEN "✓ Environment loaded from $INSTALL_DIR/.env"
    else
        show_message $YELLOW "⚠ No .env file found, using defaults"
    fi
    
    # Export Python path
    export PYTHONPATH="${INSTALL_DIR}/backend"
    
    # Update PATH for local binaries
    if [ -d "$INSTALL_DIR/bin" ]; then
        export PATH="$INSTALL_DIR/bin:$PATH"
        show_message $GREEN "✓ Local binaries added to PATH"
    fi
    
    end_message "Environment configuration loaded"
}

# Update yt-dlp if update script exists
update_ytdlp() {
    start_message "Checking yt-dlp version and updates"
    
    if [ -f "$INSTALL_DIR/scripts/update_ytdlp_local.sh" ]; then
        show_temp_message "Running yt-dlp update script"
        if bash "$INSTALL_DIR/scripts/update_ytdlp_local.sh"; then
            show_message $GREEN "✓ yt-dlp update completed"
        else
            show_message $YELLOW "⚠ yt-dlp update failed"
        fi
    elif [ -f "$INSTALL_DIR/backend/.venv/bin/yt-dlp" ]; then
        YTDLP_VERSION=$("$INSTALL_DIR/backend/.venv/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
        show_message $GREEN "✓ yt-dlp version: $YTDLP_VERSION"
    else
        show_message $YELLOW "⚠ yt-dlp not found in virtual environment"
    fi
    
    end_message "yt-dlp check complete"
}

# Load GPU status from environment file (already set by gpu_setup.sh during installation)
load_gpu_status() {
    start_message "Loading GPU hardware acceleration status"
    
    # GPU availability is already set in .env file by gpu_setup.sh during installation
    # We just need to export them for the application
    export GPU_AVAILABLE_NVIDIA="${GPU_AVAILABLE_NVIDIA:-false}"
    export GPU_AVAILABLE_INTEL="${GPU_AVAILABLE_INTEL:-false}"
    export GPU_AVAILABLE_AMD="${GPU_AVAILABLE_AMD:-false}"
    
    if [ "$ENABLE_HWACCEL" = "true" ] && [ "$HWACCEL_TYPE" != "none" ]; then
        case "$HWACCEL_TYPE" in
            "nvidia")
                if [ "$GPU_AVAILABLE_NVIDIA" = "true" ] && command -v nvidia-smi &> /dev/null; then
                    show_message $GREEN "✓ NVIDIA GPU acceleration enabled and available"
                else
                    show_message $YELLOW "⚠ NVIDIA GPU acceleration enabled but may not be available"
                fi
                ;;
            "intel")
                if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
                    show_message $GREEN "✓ Intel GPU acceleration enabled and available"
                else
                    show_message $YELLOW "⚠ Intel GPU acceleration enabled but may not be available"
                fi
                ;;
            "amd")
                if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
                    show_message $GREEN "✓ AMD GPU acceleration enabled and available"
                else
                    show_message $YELLOW "⚠ AMD GPU acceleration enabled but may not be available"
                fi
                ;;
        esac
    else
        show_message "GPU hardware acceleration disabled"
    fi
    
    end_message "GPU status loaded"
}

# Main pre-start function
main() {
    display_startup_banner
    setup_directories
    load_environment
    update_ytdlp
    load_gpu_status
    
    show_message $GREEN "Pre-start checks complete - ready to start application"
    show_message "=========================================================================="
}

# Run main function
main "$@"