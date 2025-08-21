#!/bin/bash

# Install yt-dlp and ffmpeg within Trailarr installation folder
# This ensures the app uses its own versions rather than system versions

set -e

# Source the common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logging.sh"

# If we're in a sub-script, we need to reuse the existing log file
if [ -z "$INSTALL_LOG_FILE" ]; then
    INSTALL_LOG_FILE="/tmp/trailarr_install.log"
    export INSTALL_LOG_FILE
fi

# Installation directory
INSTALL_DIR="/opt/trailarr"
BIN_DIR="$INSTALL_DIR/bin"

# Function to install ffmpeg locally (adapted from container script)
install_ffmpeg_local() {
    log_to_file "Starting ffmpeg installation to $BIN_DIR"
    
    # Create bin directory
    show_temp_message "Creating binary directory"
    mkdir -p "$BIN_DIR"
    
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
    log_to_file "Detected architecture: $ARCH"
    show_temp_message "Detected architecture: $ARCH"
    
    if [ "$ARCH" == "amd64" ] || [ "$ARCH" == "x86_64" ]; then
        # Download the latest ffmpeg build for amd64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [ "$ARCH" == "arm64" ] || [ "$ARCH" == "aarch64" ]; then
        # Download the latest ffmpeg build for arm64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    else
        # If the architecture is not supported, try to use system ffmpeg as fallback
        show_message $YELLOW "Unsupported architecture: $ARCH"
        log_to_file "Unsupported architecture $ARCH, attempting system ffmpeg fallback"
        
        if command -v ffmpeg &> /dev/null; then
            show_temp_message "Copying system ffmpeg"
            if run_logged_command "Copy system ffmpeg" "cp \"$(which ffmpeg)\" \"$BIN_DIR/\" && cp \"$(which ffprobe)\" \"$BIN_DIR/\""; then
                show_message $GREEN "Copied system ffmpeg to app directory"
                return 0
            fi
        else
            show_temp_message "Installing system ffmpeg"
            if run_logged_command "Install system ffmpeg" "apt-get update && apt-get install -y ffmpeg"; then
                show_temp_message "Copying installed ffmpeg"
                if run_logged_command "Copy installed ffmpeg" "cp \"$(which ffmpeg)\" \"$BIN_DIR/\" && cp \"$(which ffprobe)\" \"$BIN_DIR/\""; then
                    show_message $GREEN "Installed and copied system ffmpeg"
                    return 0
                fi
            fi
        fi
        show_message $RED "Failed to install ffmpeg for unsupported architecture"
        return 1
    fi
    
    log_to_file "Using ffmpeg URL: $FFMPEG_URL"
    
    # Download and install ffmpeg
    cd /tmp
    show_temp_message "Downloading ffmpeg"
    if ! run_logged_command "Download ffmpeg" "curl -L -o ffmpeg.tar.xz \"$FFMPEG_URL\""; then
        show_message $RED "Failed to download ffmpeg"
        return 1
    fi
    
    if [ ! -f ffmpeg.tar.xz ]; then
        show_message $RED "Downloaded ffmpeg file not found"
        return 1
    fi
    
    show_temp_message "Extracting ffmpeg"
    mkdir -p ffmpeg_extract
    if ! run_logged_command "Extract ffmpeg" "tar -xf ffmpeg.tar.xz -C ffmpeg_extract --strip-components=1"; then
        show_message $RED "Failed to extract ffmpeg"
        return 1
    fi
    
    # Copy binaries to app bin directory
    show_temp_message "Installing ffmpeg binaries"
    if ! run_logged_command "Install ffmpeg binaries" "cp ffmpeg_extract/bin/* \"$BIN_DIR/\""; then
        show_message $RED "Failed to copy ffmpeg binaries"
        return 1
    fi
    
    # Clean up
    rm -rf ffmpeg.tar.xz ffmpeg_extract
    
    # Verify ffmpeg installation
    if [ -f "$BIN_DIR/ffmpeg" ]; then
        FFMPEG_VERSION=$("$BIN_DIR/ffmpeg" -version 2>&1 | head -n 1 | cut -d' ' -f3)
        log_to_file "ffmpeg installation verified: version $FFMPEG_VERSION"
        show_message $GREEN "Successfully installed ffmpeg $FFMPEG_VERSION"
    else
        show_message $RED "ERROR: ffmpeg installation verification failed"
        return 1
    fi
}

# Function to verify yt-dlp installation (installed via pip)
verify_ytdlp_pip() {
    log_to_file "Checking yt-dlp in virtual environment"
    
    # yt-dlp is installed via uv sync in the virtual environment during Python dependencies installation
    # We just need to get the path and verify it's working
    VENV_YTDLP="$INSTALL_DIR/.venv/bin/yt-dlp"
    
    show_temp_message "Verifying yt-dlp installation"
    if [ -f "$VENV_YTDLP" ]; then
        if "$VENV_YTDLP" --version &> /dev/null; then
            YTDLP_VERSION=$("$VENV_YTDLP" --version)
            show_message $GREEN "yt-dlp verified (version $YTDLP_VERSION)"
            return 0
        fi
    fi
    show_message $RED "ERROR: yt-dlp not found at $VENV_YTDLP"
    return 1
}

# Function to set up environment variables
setup_environment() {
    log_to_file "Configuring environment variables for media tools"
    
    # Create .env file in data directory, not install directory
    DATA_DIR="${APP_DATA_DIR:-/var/lib/trailarr}"
    ENV_FILE="$DATA_DIR/.env"
    
    # Ensure data directory exists
    show_temp_message "Ensuring data directory exists"
    mkdir -p "$DATA_DIR"
    touch "$ENV_FILE"
    
    # Set specific paths for ffmpeg and yt-dlp using the new update function
    show_temp_message "Configuring environment variables"
    update_env_var "FFMPEG_PATH" "$BIN_DIR/ffmpeg" "$ENV_FILE"
    update_env_var "FFPROBE_PATH" "$BIN_DIR/ffprobe" "$ENV_FILE"
    update_env_var "YTDLP_PATH" "$INSTALL_DIR/venv/bin/yt-dlp" "$ENV_FILE"
    
    show_message $GREEN "Environment variables configured in $ENV_FILE"
}

# Function to create update script for yt-dlp (pip version)
create_update_script() {    
    show_temp_message "Creating yt-dlp update script"
    mkdir -p "$INSTALL_DIR/scripts"
    
    cat > "$INSTALL_DIR/scripts/update_ytdlp_local.sh" << 'EOF'
#!/bin/bash

# Update yt-dlp in Trailarr virtual environment using pip
set -e

INSTALL_DIR="/opt/trailarr"
VENV_DIR="$INSTALL_DIR/venv"

echo "Updating yt-dlp via pip..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Check current version
if [ -f "$VENV_DIR/bin/yt-dlp" ]; then
    CURRENT_VERSION=$("$VENV_DIR/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
    echo "Current yt-dlp version: $CURRENT_VERSION"
fi

# Update yt-dlp using pip
"$VENV_DIR/bin/pip" install --upgrade yt-dlp[default,curl-cffi]

if [ $? -eq 0 ]; then
    NEW_VERSION=$("$VENV_DIR/bin/yt-dlp" --version 2>/dev/null || echo "unknown")
    echo "✓ yt-dlp updated to version $NEW_VERSION"
else
    echo " Failed to update yt-dlp"
    exit 1
fi
EOF
    
    chmod +x "$INSTALL_DIR/scripts/update_ytdlp_local.sh"
    log_to_file "Created yt-dlp update script at $INSTALL_DIR/scripts/update_ytdlp_local.sh"
    show_message $GREEN "Created yt-dlp update script"
}

# Main function
main() {
    log_to_file "========== Media Tools Installation Started =========="
    
    show_temp_message "Installing media processing tools"
    
    # Install ffmpeg locally
    show_temp_message "Installing ffmpeg"
    if ! install_ffmpeg_local; then
        log_to_file "WARNING: ffmpeg installation failed but continuing"
        show_message $RED "ffmpeg installation failed"
        end_message $RED "Media tools installation failed"
        exit 1
    fi
    
    # Verify yt-dlp installation (installed via pip)
    if ! verify_ytdlp_pip; then
        log_to_file "WARNING: yt-dlp verification failed"
        show_message $RED "yt-dlp verification failed"
        end_message $RED "Media tools installation failed"
        exit 1
    fi
    
    # Set up environment variables
    setup_environment
    
    # Create update script
    create_update_script
    
    # Final summary for display
    show_message ""
    show_message "Media tools installation completed successfully"
    show_message "Installed tools:"
    show_message "    ffmpeg: $BIN_DIR/ffmpeg"
    show_message "    ffprobe: $BIN_DIR/ffprobe"
    show_message "    yt-dlp: $INSTALL_DIR/.venv/bin/yt-dlp (via uv sync)"
    
    show_message "Media tools installation complete"
    log_to_file "========== Media Tools Installation Completed =========="
}

# Run main function
main "$@"
