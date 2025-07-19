#!/bin/bash

# Trailarr Bare Metal Installation Script for Debian-based systems
# This script installs Trailarr directly on the host system without Docker

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

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_message $RED "This script should not be run as root for security reasons."
        print_message $YELLOW "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to check if distribution is supported
check_distribution() {
    if [ ! -f /etc/debian_version ]; then
        print_message $RED "This installation script only supports Debian-based distributions."
        print_message $YELLOW "Please use Docker installation for other distributions."
        exit 1
    fi
    
    print_message $GREEN "✓ Debian-based distribution detected"
}

# Function to install system dependencies
install_system_deps() {
    print_message $BLUE "Installing system dependencies..."
    
    sudo apt-get update
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        wget \
        xz-utils \
        git \
        sqlite3 \
        pciutils \
        tzdata \
        ca-certificates
    
    print_message $GREEN "✓ System dependencies installed"
}

# Function to install ffmpeg
install_ffmpeg() {
    print_message $BLUE "Installing ffmpeg..."
    
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture)
    if [ "$ARCH" == "amd64" ]; then
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [ "$ARCH" == "arm64" ] || [ "$ARCH" == "aarch64" ]; then
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    else
        print_message $YELLOW "Unsupported architecture: $ARCH, installing ffmpeg from apt"
        sudo apt-get install -y ffmpeg
        print_message $GREEN "✓ ffmpeg installed from apt"
        return
    fi

    # Download and install ffmpeg
    print_message $BLUE "Downloading ffmpeg for $ARCH..."
    curl -L -o /tmp/ffmpeg.tar.xz "$FFMPEG_URL"
    mkdir -p /tmp/ffmpeg
    tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
    sudo cp /tmp/ffmpeg/bin/* /usr/local/bin/
    rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg
    
    print_message $GREEN "✓ ffmpeg installed to /usr/local/bin/"
}

# Function to create trailarr user and directories
create_user_and_dirs() {
    print_message $BLUE "Creating trailarr user and directories..."
    
    # Create trailarr user if it doesn't exist
    if ! id "trailarr" &>/dev/null; then
        sudo useradd -r -d /opt/trailarr -s /bin/bash -m trailarr
        print_message $GREEN "✓ Created trailarr user"
    else
        print_message $YELLOW "! trailarr user already exists"
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