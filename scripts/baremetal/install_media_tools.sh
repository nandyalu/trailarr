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

# Function to install yt-dlp locally
install_ytdlp_local() {
    box_echo "Installing yt-dlp in application directory..."
    
    # Create bin directory
    mkdir -p "$BIN_DIR"
    
    # Download latest yt-dlp
    box_echo "Downloading latest yt-dlp..."
    curl -L -o "$BIN_DIR/yt-dlp" "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    
    if [ ! -f "$BIN_DIR/yt-dlp" ]; then
        box_echo "Failed to download yt-dlp"
        return 1
    fi
    
    # Make it executable
    chmod +x "$BIN_DIR/yt-dlp"
    
    # Verify installation
    if "$BIN_DIR/yt-dlp" --version &> /dev/null; then
        YTDLP_VERSION=$("$BIN_DIR/yt-dlp" --version)
        box_echo "✓ Successfully installed yt-dlp version $YTDLP_VERSION in $BIN_DIR"
    else
        box_echo "Failed to install yt-dlp"
        return 1
    fi
}

# Function to set up environment variables
setup_environment() {
    box_echo "Setting up environment variables for local binaries..."
    
    # Create .env file if it doesn't exist
    ENV_FILE="$INSTALL_DIR/.env"
    touch "$ENV_FILE"
    
    # Remove any existing PATH entries for our bin directory
    grep -v "PATH.*$BIN_DIR" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || touch "$ENV_FILE.tmp"
    mv "$ENV_FILE.tmp" "$ENV_FILE"
    
    # Add our bin directory to PATH
    echo "# Trailarr local binaries" >> "$ENV_FILE"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$ENV_FILE"
    
    # Set specific paths for ffmpeg and yt-dlp
    echo "export FFMPEG_PATH=\"$BIN_DIR/ffmpeg\"" >> "$ENV_FILE"
    echo "export FFPROBE_PATH=\"$BIN_DIR/ffprobe\"" >> "$ENV_FILE"
    echo "export YTDLP_PATH=\"$BIN_DIR/yt-dlp\"" >> "$ENV_FILE"
    
    box_echo "✓ Environment variables configured in $ENV_FILE"
    box_echo "The application will use local binaries instead of system versions"
}

# Function to create update script for yt-dlp
create_update_script() {
    box_echo "Creating yt-dlp update script..."
    
    cat > "$INSTALL_DIR/scripts/update_ytdlp_local.sh" << 'EOF'
#!/bin/bash

# Update yt-dlp in Trailarr installation directory
set -e

INSTALL_DIR="/opt/trailarr"
BIN_DIR="$INSTALL_DIR/bin"

echo "Updating yt-dlp..."

# Backup current version
if [ -f "$BIN_DIR/yt-dlp" ]; then
    cp "$BIN_DIR/yt-dlp" "$BIN_DIR/yt-dlp.backup"
fi

# Download latest version
curl -L -o "$BIN_DIR/yt-dlp.new" "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"

if [ -f "$BIN_DIR/yt-dlp.new" ]; then
    chmod +x "$BIN_DIR/yt-dlp.new"
    
    # Test the new version
    if "$BIN_DIR/yt-dlp.new" --version &> /dev/null; then
        mv "$BIN_DIR/yt-dlp.new" "$BIN_DIR/yt-dlp"
        NEW_VERSION=$("$BIN_DIR/yt-dlp" --version)
        echo "✓ yt-dlp updated to version $NEW_VERSION"
        
        # Remove backup
        rm -f "$BIN_DIR/yt-dlp.backup"
    else
        echo "New yt-dlp version failed verification, restoring backup"
        rm -f "$BIN_DIR/yt-dlp.new"
        if [ -f "$BIN_DIR/yt-dlp.backup" ]; then
            mv "$BIN_DIR/yt-dlp.backup" "$BIN_DIR/yt-dlp"
        fi
        exit 1
    fi
else
    echo "Failed to download new yt-dlp version"
    exit 1
fi
EOF
    
    chmod +x "$INSTALL_DIR/scripts/update_ytdlp_local.sh"
    box_echo "✓ Created yt-dlp update script at $INSTALL_DIR/scripts/update_ytdlp_local.sh"
}

# Main function
main() {
    box_echo "Installing yt-dlp and ffmpeg locally"
    box_echo "=========================================================================="
    
    # Install ffmpeg locally
    if ! install_ffmpeg_local; then
        box_echo "Warning: ffmpeg installation failed"
    fi
    
    # Install yt-dlp locally
    if ! install_ytdlp_local; then
        box_echo "Error: yt-dlp installation failed"
        return 1
    fi
    
    # Set up environment variables
    setup_environment
    
    # Create update script
    create_update_script
    
    box_echo "✓ Local binary installation complete"
    box_echo "Installed binaries:"
    box_echo "  ffmpeg: $BIN_DIR/ffmpeg"
    box_echo "  ffprobe: $BIN_DIR/ffprobe"
    box_echo "  yt-dlp: $BIN_DIR/yt-dlp"
    box_echo "=========================================================================="
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi