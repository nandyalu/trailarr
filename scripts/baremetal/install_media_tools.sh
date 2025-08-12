#!/bin/bash

# Install yt-dlp and ffmpeg within Trailarr installation folder
# This ensures the app uses its own versions rather than system versions

set -e

# Source the common functions
source "$(dirname "$0")/../box_echo.sh"

# Installation directory
INSTALL_DIR="/opt/trailarr"
BIN_DIR="$INSTALL_DIR/bin"

# Function to install ffmpeg locally (adapted from container script)
install_ffmpeg_local() {
    box_echo "Installing ffmpeg in application directory..."
    
    # Create bin directory
    mkdir -p "$BIN_DIR"
    
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
    
    if [ "$ARCH" == "amd64" ] || [ "$ARCH" == "x86_64" ]; then
        # Download the latest ffmpeg build for amd64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [ "$ARCH" == "arm64" ] || [ "$ARCH" == "aarch64" ]; then
        # Download the latest ffmpeg build for arm64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    else
        # If the architecture is not supported, try to use system ffmpeg as fallback
        box_echo "Unsupported architecture: $ARCH"
        box_echo "Attempting to install system ffmpeg and copy to app directory..."
        
        if command -v ffmpeg &> /dev/null; then
            cp "$(which ffmpeg)" "$BIN_DIR/"
            cp "$(which ffprobe)" "$BIN_DIR/"
            box_echo "✓ Copied system ffmpeg to app directory"
            return 0
        else
            box_echo "Installing system ffmpeg..."
            sudo apt-get update && sudo apt-get install -y ffmpeg
            cp "$(which ffmpeg)" "$BIN_DIR/"
            cp "$(which ffprobe)" "$BIN_DIR/"
            box_echo "✓ Installed and copied system ffmpeg to app directory"
            return 0
        fi
    fi
    
    # Download and install ffmpeg
    box_echo "Downloading ffmpeg for $ARCH..."
    cd /tmp
    curl -L -o ffmpeg.tar.xz "$FFMPEG_URL"
    
    if [ ! -f ffmpeg.tar.xz ]; then
        box_echo "Failed to download ffmpeg, falling back to system installation"
        return 1
    fi
    
    mkdir -p ffmpeg_extract
    tar -xf ffmpeg.tar.xz -C ffmpeg_extract --strip-components=1
    
    # Copy binaries to app bin directory
    cp ffmpeg_extract/bin/* "$BIN_DIR/"
    
    # Clean up
    rm -rf ffmpeg.tar.xz ffmpeg_extract
    
    # Verify ffmpeg installation
    if [ -f "$BIN_DIR/ffmpeg" ]; then
        FFMPEG_VERSION=$("$BIN_DIR/ffmpeg" -version 2>&1 | head -n 1 | cut -d' ' -f3)
        box_echo "✓ Successfully installed ffmpeg $FFMPEG_VERSION in $BIN_DIR"
    else
        box_echo "Failed to install ffmpeg"
        return 1
    fi
}

# Function to verify yt-dlp installation (installed via pip)
verify_ytdlp_pip() {
    box_echo "Verifying yt-dlp installation via pip..."
    
    # yt-dlp is installed via pip in the virtual environment during Python dependencies installation
    # We just need to get the path and verify it's working
    VENV_YTDLP="$INSTALL_DIR/venv/bin/yt-dlp"
    
    if [ -f "$VENV_YTDLP" ]; then
        if "$VENV_YTDLP" --version &> /dev/null; then
            YTDLP_VERSION=$("$VENV_YTDLP" --version)
            box_echo "✓ yt-dlp verified from virtual environment: version $YTDLP_VERSION"
            return 0
        fi
    fi
    
    box_echo "yt-dlp not found in virtual environment"
    return 1
}

# Function to set up environment variables
setup_environment() {
    box_echo "Setting up environment variables for local binaries..."
    
    # Create .env file in data directory, not install directory
    DATA_DIR="${APP_DATA_DIR:-/var/lib/trailarr}"
    ENV_FILE="$DATA_DIR/.env"
    
    # Ensure data directory exists
    mkdir -p "$DATA_DIR"
    touch "$ENV_FILE"
    
    # Function to update or add environment variable
    update_env_var() {
        local var_name="$1"
        local var_value="$2"
        local env_file="$3"
        
        # Remove existing entry if it exists
        grep -v "^${var_name}=" "$env_file" > "${env_file}.tmp" 2>/dev/null || touch "${env_file}.tmp"
        
        # Add new entry
        echo "${var_name}=${var_value}" >> "${env_file}.tmp"
        
        # Replace original file
        mv "${env_file}.tmp" "$env_file"
    }
    
    # Set specific paths for ffmpeg and yt-dlp
    update_env_var "FFMPEG_PATH" "$BIN_DIR/ffmpeg" "$ENV_FILE"
    update_env_var "FFPROBE_PATH" "$BIN_DIR/ffprobe" "$ENV_FILE"
    update_env_var "YTDLP_PATH" "$INSTALL_DIR/venv/bin/yt-dlp" "$ENV_FILE"
    
    box_echo "✓ Environment variables configured in $ENV_FILE"
    box_echo "The application will use local binaries instead of system versions"
}

# Function to create update script for yt-dlp (pip version)
create_update_script() {
    box_echo "Creating yt-dlp update script..."
    
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
    echo "Failed to update yt-dlp"
    exit 1
fi
EOF
    
    chmod +x "$INSTALL_DIR/scripts/update_ytdlp_local.sh"
    box_echo "✓ Created yt-dlp update script at $INSTALL_DIR/scripts/update_ytdlp_local.sh"
}

# Main function
main() {
    box_echo "Installing ffmpeg locally and verifying yt-dlp"
    box_echo "=========================================================================="
    
    # Install ffmpeg locally
    if ! install_ffmpeg_local; then
        box_echo "Warning: ffmpeg installation failed"
    fi
    
    # Verify yt-dlp installation (installed via pip)
    if ! verify_ytdlp_pip; then
        box_echo "Warning: yt-dlp not properly installed via pip"
    fi
    
    # Set up environment variables
    setup_environment
    
    # Create update script
    create_update_script
    
    box_echo "✓ Local binary installation complete"
    box_echo "Installed binaries:"
    box_echo "  ffmpeg: $BIN_DIR/ffmpeg"
    box_echo "  ffprobe: $BIN_DIR/ffprobe"
    box_echo "  yt-dlp: $INSTALL_DIR/venv/bin/yt-dlp (via pip)"
    box_echo "=========================================================================="
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi