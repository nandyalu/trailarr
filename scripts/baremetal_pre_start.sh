#!/bin/bash

# Trailarr Bare Metal Pre-Start Script
# This script runs before the main application starts (like Docker entrypoint but for bare metal)

set -e

# Source the box_echo function
source /opt/trailarr/scripts/box_echo.sh

# Set default environment variables if not set
export APP_NAME=${APP_NAME:-"Trailarr"}
export APP_PORT=${APP_PORT:-7889}
export APP_DATA_DIR=${APP_DATA_DIR:-"/var/lib/trailarr"}
export APP_VERSION=${APP_VERSION:-"0.0.0-dev"}
export TZ=${TZ:-"UTC"}

# Print startup banner
box_echo "";
box_echo "               App Version: ${APP_VERSION}";
box_echo "";
box_echo "--------------------------------------------------------------------------";
box_echo "Starting Trailarr (Bare Metal) with the following configuration:"
box_echo "APP_DATA_DIR: ${APP_DATA_DIR}"
box_echo "APP_PORT: ${APP_PORT}"
box_echo "TZ: ${TZ}"
box_echo "USER: $(whoami)"
box_echo "--------------------------------------------------------------------------";

# Set TimeZone
box_echo "Current date time: $(date)"
box_echo "Setting TimeZone to ${TZ}"
sudo timedatectl set-timezone ${TZ} 2>/dev/null || box_echo "Warning: Could not set timezone (non-root or timedatectl not available)"
box_echo "Current date time after update: $(date)"
box_echo "--------------------------------------------------------------------------";

# Create necessary directories
box_echo "Creating required directories"
mkdir -p "${APP_DATA_DIR}/logs"
mkdir -p "${APP_DATA_DIR}/backups"
mkdir -p "${APP_DATA_DIR}/web/images"
mkdir -p "/opt/trailarr/tmp"

# Set proper permissions
chmod -R 755 "${APP_DATA_DIR}"
chmod -R 755 "/opt/trailarr/assets"
chmod -R 755 "/opt/trailarr/tmp"
box_echo "--------------------------------------------------------------------------";

# Load environment variables from .env file
ENV_FILE="${APP_DATA_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    box_echo "Loading environment variables from ${ENV_FILE}"
    set -a
    source "$ENV_FILE"
    set +a
    box_echo "Environment variables loaded"
else
    box_echo "Warning: No .env file found at ${ENV_FILE}"
fi
box_echo "--------------------------------------------------------------------------";

# Check for yt-dlp updates
box_echo "Checking yt-dlp version and updates..."
/opt/trailarr/scripts/update_ytdlp.sh "${APP_DATA_DIR}"
box_echo "--------------------------------------------------------------------------";

# Check for GPU availability
box_echo "Checking for NVIDIA GPU availability..."
export NVIDIA_GPU_AVAILABLE="false"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        box_echo "NVIDIA GPU is available."
        export NVIDIA_GPU_AVAILABLE="true"
    else
        box_echo "NVIDIA GPU is not available."
    fi
else
    box_echo "nvidia-smi command not found. NVIDIA GPU not detected."
fi
box_echo "--------------------------------------------------------------------------";

# Check for Intel GPU availability (QSV)
box_echo "Checking for Intel GPU availability..."
export QSV_GPU_AVAILABLE="false"
if [ -d /dev/dri ]; then
    if ls /dev/dri | grep -q "renderD"; then
        if lspci | grep -iE 'Display|VGA' | grep -i 'Intel' > /dev/null 2>&1; then
            export QSV_GPU_AVAILABLE="true"
            box_echo "Intel GPU detected. Intel QSV is likely available."
        else
            box_echo "No Intel GPU detected. Intel QSV is not available."
        fi
    else
        box_echo "Intel QSV not detected. No renderD devices found in /dev/dri."
    fi
else
    box_echo "Intel QSV is not available. /dev/dri does not exist."
fi
box_echo "--------------------------------------------------------------------------";

box_echo "Pre-start setup completed successfully"