#!/bin/bash

# Install yt-dlp and ffmpeg within Trailarr installation folder
# This ensures the app uses its own versions rather than system versions

set -e

# Source the common functions - first try baremetal logging, fallback to box_echo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/logging.sh" ]; then
    source "$SCRIPT_DIR/logging.sh"
    # If we're in a sub-script, we need to reuse the existing log file
    if [ -z "$INSTALL_LOG_FILE" ]; then
        INSTALL_LOG_FILE="/tmp/trailarr_install.log"
        export INSTALL_LOG_FILE
    fi
else
    source "$SCRIPT_DIR/../box_echo.sh"
    # Define print_message and start_message/end_message for compatibility
    print_message() { echo -e "$1$2\033[0m"; }
    start_message() { echo -e "$1$2\033[0m"; }
    end_message() { echo -e "$1$2\033[0m"; }
    log_to_file() { echo "$1"; }
    run_logged_command() { eval "$2"; }
    update_env_var() { 
        local var_name="$1"
        local var_value="$2"
        local env_file="$3"
        touch "$env_file"
        grep -v "^${var_name}=" "$env_file" > "${env_file}.tmp" 2>/dev/null || touch "${env_file}.tmp"
        echo "${var_name}=${var_value}" >> "${env_file}.tmp"
        mv "${env_file}.tmp" "$env_file"
    }
fi

# Installation directory
INSTALL_DIR="/opt/trailarr"
BIN_DIR="$INSTALL_DIR/bin"

# Function to install ffmpeg locally (adapted from container script)
install_ffmpeg_local() {
    start_message "$BLUE" "Installing ffmpeg..."
    log_to_file "Starting ffmpeg installation to $BIN_DIR"
    
    # Create bin directory
    mkdir -p "$BIN_DIR"
    
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
    log_to_file "Detected architecture: $ARCH"
    
    if [ "$ARCH" == "amd64" ] || [ "$ARCH" == "x86_64" ]; then
        # Download the latest ffmpeg build for amd64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [ "$ARCH" == "arm64" ] || [ "$ARCH" == "aarch64" ]; then
        # Download the latest ffmpeg build for arm64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    else
        # If the architecture is not supported, try to use system ffmpeg as fallback
        print_message "$YELLOW" "Unsupported architecture: $ARCH"
        log_to_file "Unsupported architecture $ARCH, attempting system ffmpeg fallback"
        
        if command -v ffmpeg &> /dev/null; then
            if run_logged_command "Copy system ffmpeg" "cp \"$(which ffmpeg)\" \"$BIN_DIR/\" && cp \"$(which ffprobe)\" \"$BIN_DIR/\""; then
                end_message "$GREEN" "✓ Copied system ffmpeg to app directory"
                return 0
            fi
        else
            print_message "$BLUE" "Installing system ffmpeg..."
            if run_logged_command "Install system ffmpeg" "apt-get update && apt-get install -y ffmpeg"; then
                if run_logged_command "Copy installed ffmpeg" "cp \"$(which ffmpeg)\" \"$BIN_DIR/\" && cp \"$(which ffprobe)\" \"$BIN_DIR/\""; then
                    end_message "$GREEN" "✓ Installed and copied system ffmpeg"
                    return 0
                fi
            fi
        fi
        end_message "$RED" "✗ Failed to install ffmpeg for unsupported architecture"
        return 1
    fi
    
    log_to_file "Using ffmpeg URL: $FFMPEG_URL"
    
    # Download and install ffmpeg
    cd /tmp
    if ! run_logged_command "Download ffmpeg" "curl -L -o ffmpeg.tar.xz \"$FFMPEG_URL\""; then
        end_message "$RED" "✗ Failed to download ffmpeg"
        return 1
    fi
    
    if [ ! -f ffmpeg.tar.xz ]; then
        end_message "$RED" "✗ ffmpeg download file not found"
        return 1
    fi
    
    mkdir -p ffmpeg_extract
    if ! run_logged_command "Extract ffmpeg" "tar -xf ffmpeg.tar.xz -C ffmpeg_extract --strip-components=1"; then
        end_message "$RED" "✗ Failed to extract ffmpeg"
        return 1
    fi
    
    # Copy binaries to app bin directory
    if ! run_logged_command "Install ffmpeg binaries" "cp ffmpeg_extract/bin/* \"$BIN_DIR/\""; then
        end_message "$RED" "✗ Failed to copy ffmpeg binaries"
        return 1
    fi
    
    # Clean up
    rm -rf ffmpeg.tar.xz ffmpeg_extract
    
    # Verify ffmpeg installation
    if [ -f "$BIN_DIR/ffmpeg" ]; then
        FFMPEG_VERSION=$("$BIN_DIR/ffmpeg" -version 2>&1 | head -n 1 | cut -d' ' -f3)
        log_to_file "ffmpeg installation verified: version $FFMPEG_VERSION"
        end_message "$GREEN" "✓ Successfully installed ffmpeg $FFMPEG_VERSION"
    else
        end_message "$RED" "✗ ffmpeg installation verification failed"
        return 1
    fi
}

# Function to verify yt-dlp installation (installed via pip)
verify_ytdlp_pip() {
    start_message "$BLUE" "Verifying yt-dlp installation..."
    log_to_file "Checking yt-dlp in virtual environment"
    
    # yt-dlp is installed via pip in the virtual environment during Python dependencies installation
    # We just need to get the path and verify it's working
    VENV_YTDLP="$INSTALL_DIR/venv/bin/yt-dlp"
    
    if [ -f "$VENV_YTDLP" ]; then
        if "$VENV_YTDLP" --version &> /dev/null; then
            YTDLP_VERSION=$("$VENV_YTDLP" --version)
            log_to_file "yt-dlp verified: version $YTDLP_VERSION"
            end_message "$GREEN" "✓ yt-dlp verified (version $YTDLP_VERSION)"
            return 0
        fi
    fi
    
    end_message "$RED" "✗ yt-dlp not found in virtual environment"
    log_to_file "ERROR: yt-dlp not found at $VENV_YTDLP"
    return 1
}

# Function to set up environment variables
setup_environment() {
    start_message "$BLUE" "Setting up environment variables..."
    log_to_file "Configuring environment variables for media tools"
    
    # Create .env file in data directory, not install directory
    DATA_DIR="${APP_DATA_DIR:-/var/lib/trailarr}"
    ENV_FILE="$DATA_DIR/.env"
    
    # Ensure data directory exists
    mkdir -p "$DATA_DIR"
    touch "$ENV_FILE"
    
    # Set specific paths for ffmpeg and yt-dlp using the new update function
    update_env_var "FFMPEG_PATH" "$BIN_DIR/ffmpeg" "$ENV_FILE"
    update_env_var "FFPROBE_PATH" "$BIN_DIR/ffprobe" "$ENV_FILE"
    update_env_var "YTDLP_PATH" "$INSTALL_DIR/venv/bin/yt-dlp" "$ENV_FILE"
    
    log_to_file "Environment variables configured in $ENV_FILE"
    end_message "$GREEN" "✓ Environment variables configured"
}

# Function to create update script for yt-dlp (pip version)
create_update_script() {
    start_message "$BLUE" "Creating yt-dlp update script..."
    log_to_file "Creating update script for yt-dlp"
    
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
    log_to_file "Created yt-dlp update script at $INSTALL_DIR/scripts/update_ytdlp_local.sh"
    end_message "$GREEN" "✓ Created yt-dlp update script"
}

# Main function
main() {
    print_message "$BLUE" "Installing media processing tools..."
    log_to_file "========== Media Tools Installation Started =========="
    
    # Install ffmpeg locally
    if ! install_ffmpeg_local; then
        print_message "$YELLOW" "Warning: ffmpeg installation failed"
        log_to_file "WARNING: ffmpeg installation failed but continuing"
    fi
    
    # Verify yt-dlp installation (installed via pip)
    if ! verify_ytdlp_pip; then
        print_message "$YELLOW" "Warning: yt-dlp not properly installed via pip"
        log_to_file "WARNING: yt-dlp verification failed"
    fi
    
    # Set up environment variables
    setup_environment
    
    # Create update script
    create_update_script
    
    print_message "$GREEN" "✓ Media tools installation complete"
    print_message "$BLUE" "Installed tools:"
    print_message "$BLUE" "  → ffmpeg: $BIN_DIR/ffmpeg"
    print_message "$BLUE" "  → ffprobe: $BIN_DIR/ffprobe"
    print_message "$BLUE" "  → yt-dlp: $INSTALL_DIR/venv/bin/yt-dlp (via pip)"
    
    log_to_file "Media tools installation completed successfully"
    log_to_file "ffmpeg: $BIN_DIR/ffmpeg"
    log_to_file "ffprobe: $BIN_DIR/ffprobe"
    log_to_file "yt-dlp: $INSTALL_DIR/venv/bin/yt-dlp"
    log_to_file "========== Media Tools Installation Completed =========="
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi