#!/bin/bash

# Trailarr Bare Metal Installation Bootstrap Script
# This script downloads the latest Trailarr release and runs the installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Configuration
REPO_URL="https://github.com/nandyalu/trailarr"
TEMP_DIR="/tmp/trailarr_install"
INSTALL_SCRIPT="scripts/baremetal/install.sh"

# Function to display banner
display_banner() {
    clear
    cat << 'EOF'
 _______           _ _                     
|__   __|         (_) |                    
   | |_ __ __ _ ___ _| | __ _ _ __ _ __      
   | | '__/ _` |/ __| | |/ _` | '__| '__|     
   | | | | (_| | (__| | | (_| | |  | |        
   |_|_|  \__,_|\___|_|_|\__,_|_|  |_|        
                                             
       Bare Metal Installation              
                                             
EOF
    print_message $BLUE "This script will download and install Trailarr directly on your system"
    echo ""
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_message $RED "This script should not be run as root for security reasons."
        print_message $YELLOW "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    print_message $BLUE "Checking required dependencies..."
    
    # Check for required commands
    MISSING_DEPS=()
    
    for cmd in curl wget git unzip; do
        if ! command -v "$cmd" &> /dev/null; then
            MISSING_DEPS+=("$cmd")
        fi
    done
    
    if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
        print_message $RED "Missing required dependencies: ${MISSING_DEPS[*]}"
        print_message $YELLOW "Please install them first:"
        print_message $YELLOW "  sudo apt update && sudo apt install -y ${MISSING_DEPS[*]}"
        exit 1
    fi
    
    print_message $GREEN "✓ All dependencies are available"
}

# Function to get latest release version
get_latest_version() {
    print_message $BLUE "Fetching latest release information..."
    
    # Try to get latest release from GitHub API
    if command -v curl &> /dev/null; then
        LATEST_VERSION=$(curl -s "https://api.github.com/repos/nandyalu/trailarr/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "")
    elif command -v wget &> /dev/null; then
        LATEST_VERSION=$(wget -qO- "https://api.github.com/repos/nandyalu/trailarr/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "")
    fi
    
    if [ -z "$LATEST_VERSION" ]; then
        print_message $YELLOW "Could not fetch latest version, using main branch"
        DOWNLOAD_URL="${REPO_URL}/archive/refs/heads/main.zip"
        EXTRACT_DIR="trailarr-main"
    else
        print_message $GREEN "✓ Latest version: $LATEST_VERSION"
        DOWNLOAD_URL="${REPO_URL}/archive/refs/tags/${LATEST_VERSION}.zip"
        EXTRACT_DIR="trailarr-${LATEST_VERSION#v}"
    fi
}

# Function to download and extract source
download_source() {
    print_message $BLUE "Downloading Trailarr source code..."
    
    # Clean up any existing temp directory
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # Download source
    if command -v curl &> /dev/null; then
        curl -L -o trailarr.zip "$DOWNLOAD_URL"
    elif command -v wget &> /dev/null; then
        wget -O trailarr.zip "$DOWNLOAD_URL"
    else
        print_message $RED "Neither curl nor wget available for download"
        exit 1
    fi
    
    # Extract archive
    unzip -q trailarr.zip
    
    if [ ! -d "$EXTRACT_DIR" ]; then
        print_message $RED "Failed to extract source code"
        exit 1
    fi
    
    print_message $GREEN "✓ Source code downloaded and extracted"
}

# Function to run installation
run_installation() {
    print_message $BLUE "Starting Trailarr installation..."
    
    cd "$TEMP_DIR/$EXTRACT_DIR"
    
    # Check if installation script exists
    if [ ! -f "$INSTALL_SCRIPT" ]; then
        print_message $RED "Installation script not found: $INSTALL_SCRIPT"
        exit 1
    fi
    
    # Make installation script executable
    chmod +x "$INSTALL_SCRIPT"
    
    # Run the installation
    bash "$INSTALL_SCRIPT"
}

# Function to cleanup
cleanup() {
    print_message $BLUE "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    print_message $GREEN "✓ Cleanup complete"
}

# Main function
main() {
    # Set up error handling
    trap cleanup EXIT
    
    display_banner
    check_root
    check_dependencies
    get_latest_version
    download_source
    run_installation
    
    print_message $GREEN ""
    print_message $GREEN "🎉 Trailarr installation bootstrap completed!"
    print_message $GREEN ""
    echo "The installation script has been downloaded and executed."
    echo "Please check the output above for any further instructions."
}

# Run main function
main "$@"
    fi
    
    # Create directories
    sudo mkdir -p /opt/trailarr
    sudo mkdir -p /var/lib/trailarr
    sudo mkdir -p /var/log/trailarr
    
    # Set ownership
    sudo chown -R trailarr:trailarr /opt/trailarr
    sudo chown -R trailarr:trailarr /var/lib/trailarr
    sudo chown -R trailarr:trailarr /var/log/trailarr
    
    print_message $GREEN "✓ Directories created with proper ownership"
}

# Function to install Trailarr application
install_trailarr() {
    print_message $BLUE "Installing Trailarr application..."
    
    # Copy application files
    sudo cp -r backend/ /opt/trailarr/
    sudo cp -r frontend-build/ /opt/trailarr/
    sudo cp -r scripts/ /opt/trailarr/
    sudo cp -r assets/ /opt/trailarr/
    
    # Create Python virtual environment
    sudo -u trailarr python3 -m venv /opt/trailarr/venv
    
    # Install Python dependencies
    sudo -u trailarr /opt/trailarr/venv/bin/pip install --upgrade pip
    sudo -u trailarr /opt/trailarr/venv/bin/pip install -r /opt/trailarr/backend/requirements.txt
    
    # Make scripts executable
    sudo chmod +x /opt/trailarr/scripts/*.sh
    
    # Set proper ownership
    sudo chown -R trailarr:trailarr /opt/trailarr
    
    print_message $GREEN "✓ Trailarr application installed to /opt/trailarr"
}

# Function to create configuration
create_config() {
    print_message $BLUE "Creating default configuration..."
    
    # Create default .env file
    sudo -u trailarr cat > /var/lib/trailarr/.env << 'EOF'
# Trailarr Configuration
APP_NAME="Trailarr"
APP_PORT=7889
APP_DATA_DIR="/var/lib/trailarr"
TZ="America/New_York"

# Application settings
LOG_LEVEL="INFO"
MONITOR_ENABLED=true
MONITOR_INTERVAL=60

# Trailer settings
TRAILER_RESOLUTION="1080"
TRAILER_AUDIO_FORMAT="aac"
TRAILER_VIDEO_FORMAT="h264"
TRAILER_FILE_FORMAT="mkv"
TRAILER_SUBTITLES_ENABLED=true
TRAILER_EMBED_METADATA=true
TRAILER_WEB_OPTIMIZED=true
TRAILER_HARDWARE_ACCELERATION=true

# Authentication (default: admin/trailarr)
WEBUI_USERNAME="admin"
WEBUI_PASSWORD="$2b$12$CU7h.sOkBp5RFRJIYEwXU.1LCUTD2pWE4p5nsW3k1iC9oZEGVWeum"
EOF

    print_message $GREEN "✓ Default configuration created in /var/lib/trailarr/.env"
    print_message $YELLOW "  Default WebUI credentials: admin/trailarr"
}

# Function to create systemd service
create_systemd_service() {
    print_message $BLUE "Creating systemd service..."
    
    sudo cat > /etc/systemd/system/trailarr.service << 'EOF'
[Unit]
Description=Trailarr - Trailer downloader for Radarr and Sonarr
After=network.target

[Service]
Type=simple
User=trailarr
Group=trailarr
WorkingDirectory=/opt/trailarr
Environment=PYTHONPATH=/opt/trailarr/backend
Environment=APP_DATA_DIR=/var/lib/trailarr
ExecStartPre=/opt/trailarr/scripts/baremetal_pre_start.sh
ExecStart=/opt/trailarr/scripts/baremetal_start.sh
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/trailarr /var/log/trailarr /opt/trailarr/tmp

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    print_message $GREEN "✓ Systemd service created"
}

# Main installation function
main() {
    print_message $GREEN "=== Trailarr Bare Metal Installation ==="
    print_message $BLUE "This will install Trailarr directly on your system without Docker"
    echo
    
    check_root
    check_distribution
    
    # Ask for confirmation
    read -p "Do you want to continue with the installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message $YELLOW "Installation cancelled"
        exit 0
    fi
    
    # Check if we're in the right directory
    if [ ! -f "backend/main.py" ] || [ ! -f "scripts/entrypoint.sh" ]; then
        print_message $RED "Error: Please run this script from the Trailarr source directory"
        exit 1
    fi
    
    install_system_deps
    install_ffmpeg
    create_user_and_dirs
    install_trailarr
    create_config
    create_systemd_service
    
    echo
    print_message $GREEN "=== Installation Complete! ==="
    print_message $BLUE "To start Trailarr:"
    print_message $YELLOW "  sudo systemctl enable trailarr"
    print_message $YELLOW "  sudo systemctl start trailarr"
    echo
    print_message $BLUE "To check status:"
    print_message $YELLOW "  sudo systemctl status trailarr"
    echo
    print_message $BLUE "Trailarr will be available at:"
    print_message $YELLOW "  http://localhost:7889"
    echo
    print_message $BLUE "Default credentials:"
    print_message $YELLOW "  Username: admin"
    print_message $YELLOW "  Password: trailarr"
    echo
    print_message $BLUE "Configuration file:"
    print_message $YELLOW "  /var/lib/trailarr/.env"
    echo
    print_message $BLUE "Logs location:"
    print_message $YELLOW "  /var/log/trailarr/"
    print_message $YELLOW "  journalctl -u trailarr -f"
}

# Run main function
main "$@"