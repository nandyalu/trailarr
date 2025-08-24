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
    echo "               Trailarr Version: ${APP_VERSION}"
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

# Update yt-dlp using uv sync 
update_ytdlp() {
    echo "Checking yt-dlp version and updates"
    
    # Check if UPDATE_YTDLP is enabled
    UPDATE_YTDLP=${UPDATE_YTDLP:-false}
    update_ytdlp_lower=$(echo "$UPDATE_YTDLP" | tr '[:upper:]' '[:lower:]')
    
    if [ "$update_ytdlp_lower" = "true" ] || [ "$update_ytdlp_lower" = "1" ] || [ "$update_ytdlp_lower" = "yes" ]; then
        echo "UPDATE_YTDLP is set to true. Updating yt-dlp with uv sync..."
        
        # Navigate to backend directory and run uv sync to update dependencies
        cd "$INSTALL_DIR/backend"
        if [ -f "$INSTALL_DIR/.local/bin/uv" ]; then
            UV_CMD="$INSTALL_DIR/.local/bin/uv"
        else
            UV_CMD="uv"  # Fallback to system uv
        fi
        
        # Run uv sync to update all dependencies including yt-dlp
        if $UV_CMD sync --no-cache-dir; then
            echo "✓ Dependencies updated with uv sync"
            if [ -f "$INSTALL_DIR/backend/.venv/bin/yt-dlp" ]; then
                YTDLP_VERSION=$("$INSTALL_DIR/backend/.venv/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
                echo "✓ yt-dlp updated to version: $YTDLP_VERSION"
                
                # Save updated version to environment
                if [ -f "$DATA_DIR/.env" ]; then
                    sed -i '/^YTDLP_VERSION=/d' "$DATA_DIR/.env" 2>/dev/null || true
                    echo "YTDLP_VERSION=$YTDLP_VERSION" >> "$DATA_DIR/.env"
                fi
            fi
        else
            echo "⚠ Failed to update dependencies with uv sync"
        fi
    else
        # Just check current version
        if [ -f "$INSTALL_DIR/backend/.venv/bin/yt-dlp" ]; then
            YTDLP_VERSION=$("$INSTALL_DIR/backend/.venv/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
            echo "✓ Current yt-dlp version: $YTDLP_VERSION"
        else
            echo "⚠ yt-dlp not found in virtual environment"
        fi
    fi
    
    echo "yt-dlp check complete"
    echo "--------------------------------------------------------------------------"
}

# Check and report NVIDIA GPU status
check_nvidia_gpu() {
    echo "Checking for NVIDIA GPU availability..."
    # Check for NVIDIA GPU using nvidia-smi
    if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
        # Get NVIDIA GPU information
        GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            export GPU_AVAILABLE_NVIDIA="true"
            echo "NVIDIA GPU detected: $GPU_INFO"
            echo "NVIDIA hardware acceleration (CUDA) is available."
            if [ -n "$GPU_DEVICE_NVIDIA" ]; then
                echo "NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
            fi
        else
            echo "NVIDIA GPU not detected - no device information available."
            export GPU_AVAILABLE_NVIDIA="false"
        fi
    else
        if command -v nvidia-smi &> /dev/null; then
            echo "NVIDIA GPU not detected - nvidia-smi failed or no GPU found."
        else
            echo "nvidia-smi command not found. NVIDIA GPU not detected."
        fi
    fi
}

# Check and report Intel GPU status
check_intel_gpu() {
    echo "Checking for Intel GPU availability and group access..."
    if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
        # Check for Intel GPU using lspci
        INTEL_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' Intel| ARC')
        if [ -n "$INTEL_GPU" ]; then
            echo "Intel GPU detected: $INTEL_GPU"
            echo "Intel GPU device: $GPU_DEVICE_INTEL"

            # Dynamically get the group that owns the render node
            if [ -e "$GPU_DEVICE_INTEL" ]; then
                group_owner=$(stat -c '%g' "$GPU_DEVICE_INTEL" 2>/dev/null)
                echo "Intel render device owned by group: $group_owner"
                
                if id -nG "trailarr" | grep -qw "$group_owner"; then
                    echo "trailarr user already in group '$group_owner'."
                else
                    echo "Adding trailarr user to group '$group_owner' for GPU access."
                    usermod -aG "$group_owner" trailarr
                fi
                
                # Now that permissions are set, check for VAAPI capabilities
                echo "Intel hardware acceleration (VAAPI) is available."
                if command -v vainfo &> /dev/null; then
                    VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_INTEL" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|VP8|VP9|AV1")
                    if [ -n "$VAAPI_INFO" ]; then
                        echo "VAAPI capabilities detected (H.264, HEVC, VP8, VP9, AV1):"
                        echo "$VAAPI_INFO" | while read -r line; do echo "   $line"; done
                    fi
                fi
            else
                echo "ERROR: Could not find render device for Intel GPU at '$GPU_DEVICE_INTEL'."
            fi
        else
            echo "Intel GPU device detected but not found in PCI devices."
        fi
    fi
}

# Check and report AMD GPU status
check_amd_gpu() {
    echo "Checking for AMD GPU availability and group access..."
    if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
        # Check for AMD GPU using lspci
        AMD_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' AMD| ATI| Radeon')
        if [ -n "$AMD_GPU" ]; then
            echo "AMD GPU detected: $AMD_GPU"
            echo "AMD GPU device: $GPU_DEVICE_AMD"

            # Dynamically get the group that owns the render node
            if [ -e "$GPU_DEVICE_AMD" ]; then
                group_owner=$(stat -c '%G' "$GPU_DEVICE_AMD")
                echo "AMD render device owned by group: $group_owner"

                if id -nG "trailarr" | grep -qw "$group_owner"; then
                    echo "trailarr user already in group '$group_owner'."
                else
                    echo "Adding trailarr user to group '$group_owner' for GPU access."
                    usermod -aG "$group_owner" trailarr
                fi
                
                # Now that permissions are set, check for VAAPI capabilities
                echo "AMD hardware acceleration (VAAPI) is available."
                if command -v vainfo &> /dev/null; then
                    VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_AMD" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|AV1")
                    if [ -n "$VAAPI_INFO" ]; then
                        echo "VAAPI capabilities detected (H.264, HEVC, AV1):"
                        echo "$VAAPI_INFO" | while read -r line; do echo "   $line"; done
                    fi
                fi
            else
                echo "ERROR: Could not find render device for AMD GPU at '$GPU_DEVICE_AMD'."
            fi
        else
            echo "AMD GPU device detected but not found in PCI devices."
        fi
    fi
}

# Load GPU status from environment file (already set by gpu_setup.sh during installation)
load_gpu_status() {
    echo "Detecting available GPUs"
    
    # Initialize device mappings
    export GPU_DEVICE_NVIDIA=""
    export GPU_DEVICE_INTEL=""
    export GPU_DEVICE_AMD=""
    
    # Initialize availability flags
    export GPU_AVAILABLE_NVIDIA="false"
    export GPU_AVAILABLE_INTEL="false"
    export GPU_AVAILABLE_AMD="false"

    # Check for DRI devices and map them to specific GPUs
    if [ -d /dev/dri ]; then
        for device in /dev/dri/renderD*; do
            if [ -e "$device" ]; then
                # Get sysfs path
                syspath=$(udevadm info --query=path --name="$device")
                fullpath="/sys$syspath/device"

                # Check if the device has a vendor file
                if [ -f "$fullpath/vendor" ]; then
                    vendor=$(cat "$fullpath/vendor")
                    # NVIDIA: 10de, Intel: 8086, AMD: 1002
                    # PCI Vendor IDS: https://pci-ids.ucw.cz/
                    case "$vendor" in
                        0x10de)
                            [ -z "$GPU_DEVICE_NVIDIA" ] && export GPU_DEVICE_NVIDIA="$device"
                            export GPU_AVAILABLE_NVIDIA="true"
                            check_nvidia_gpu
                            ;;
                        0x8086)
                            [ -z "$GPU_DEVICE_INTEL" ] && export GPU_DEVICE_INTEL="$device"
                            export GPU_AVAILABLE_INTEL="true"
                            check_intel_gpu
                            ;;
                        0x1002|0x1022)
                            [ -z "$GPU_DEVICE_AMD" ] && export GPU_DEVICE_AMD="$device"
                            export GPU_AVAILABLE_AMD="true"
                            check_amd_gpu
                            ;;
                    esac
                fi
            fi
        done
    else
        echo "No GPU devices detected!"
    fi

    # Update .env file with GPU detection results
    if [ -f "$DATA_DIR/.env" ]; then
        # Use a simple approach to update .env file
        sed -i '/^GPU_AVAILABLE_NVIDIA=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_AVAILABLE_INTEL=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_AVAILABLE_AMD=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_DEVICE_NVIDIA=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_DEVICE_INTEL=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_DEVICE_AMD=/d' "$DATA_DIR/.env" 2>/dev/null || true
        
        echo "GPU_AVAILABLE_NVIDIA=$GPU_AVAILABLE_NVIDIA" >> "$DATA_DIR/.env"
        echo "GPU_AVAILABLE_INTEL=$GPU_AVAILABLE_INTEL" >> "$DATA_DIR/.env"
        echo "GPU_AVAILABLE_AMD=$GPU_AVAILABLE_AMD" >> "$DATA_DIR/.env"
        echo "GPU_DEVICE_NVIDIA=$GPU_DEVICE_NVIDIA" >> "$DATA_DIR/.env"
        echo "GPU_DEVICE_INTEL=$GPU_DEVICE_INTEL" >> "$DATA_DIR/.env"
        echo "GPU_DEVICE_AMD=$GPU_DEVICE_AMD" >> "$DATA_DIR/.env"
    fi
    
    echo "✓ GPU detection completed"
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