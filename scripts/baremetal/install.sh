#!/bin/bash

# Trailarr Bare Metal Installation Script for Debian-based systems
# Modular installation with GPU support, Python 3.13.5, and interactive configuration

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
DATA_DIR="/var/lib/trailarr"
LOG_DIR="/var/log/trailarr"

# Script directory (current directory where install.sh is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAREMETAL_SCRIPTS_DIR="$SCRIPT_DIR"

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

# Source the box_echo function if available
if [ -f "$SCRIPT_DIR/../box_echo.sh" ]; then
    source "$SCRIPT_DIR/../box_echo.sh"
elif [ -f "$SCRIPT_DIR/box_echo.sh" ]; then
    source "$SCRIPT_DIR/box_echo.sh"
else
    # Fallback if box_echo not available
    box_echo() {
        echo "==> $1"
    }
fi

# Function to display installation banner
display_banner() {
    clear
    cat << 'EOF'
 _______           _ _                     
|__   __|         (_) |                    
   | |_ __ __ _ ___ _| | __ _ _ __ _ __      
   | | '__/ _` |/ __| | |/ _` | '__| '__|     
   | | | | (_| | (__| | | (_| | |  | |        
   |_|_|  \__,_|\___|_|_|\__,_|_|  |_|        
                                             
       Bare Metal Installation Script       
                                             
EOF
    print_message $BLUE "Installing Trailarr directly on your system for maximum performance"
    print_message $BLUE "with native GPU hardware acceleration support"
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
    box_echo "Installing system dependencies..."
    
    sudo apt-get update
    sudo apt-get install -y \
        curl \
        wget \
        xz-utils \
        git \
        sqlite3 \
        pciutils \
        usbutils \
        tzdata \
        ca-certificates \
        build-essential \
        libffi-dev \
        libssl-dev \
        systemd \
        sudo
    
    print_message $GREEN "✓ System dependencies installed"
}

# Function to create trailarr user and directories
create_user_and_dirs() {
    box_echo "Creating trailarr user and directories..."
    
    # Create trailarr user if it doesn't exist
    if ! id "trailarr" &>/dev/null; then
        sudo useradd -r -d "$INSTALL_DIR" -s /bin/bash -m trailarr
        print_message $GREEN "✓ Created trailarr user"
    else
        print_message $YELLOW "! trailarr user already exists"
    fi
    
    # Create necessary directories
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$DATA_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo mkdir -p "$INSTALL_DIR/tmp"
    sudo mkdir -p "$INSTALL_DIR/scripts"
    sudo mkdir -p "$INSTALL_DIR/bin"
    
    # Set ownership
    sudo chown -R trailarr:trailarr "$INSTALL_DIR"
    sudo chown -R trailarr:trailarr "$DATA_DIR"
    sudo chown -R trailarr:trailarr "$LOG_DIR"
    
    print_message $GREEN "✓ Directories created and configured"
}

# Function to copy application files
copy_application_files() {
    box_echo "Copying application files..."
    
    # Copy source code
    sudo cp -r "$SCRIPT_DIR/../backend" "$INSTALL_DIR/"
    sudo cp -r "$SCRIPT_DIR/../frontend-build" "$INSTALL_DIR/"
    sudo cp -r "$SCRIPT_DIR/../assets" "$INSTALL_DIR/"
    sudo cp -r "$SCRIPT_DIR/../scripts" "$INSTALL_DIR/"
    
    # Copy configuration files
    sudo cp "$SCRIPT_DIR/../mkdocs.yml" "$INSTALL_DIR/" 2>/dev/null || true
    sudo cp "$SCRIPT_DIR/../requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Set ownership
    sudo chown -R trailarr:trailarr "$INSTALL_DIR"
    
    print_message $GREEN "✓ Application files copied"
}

# Function to run Python installation
install_python() {
    box_echo "Setting up Python 3.13.5..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/install_python.sh" ]; then
        sudo -u trailarr bash "$BAREMETAL_SCRIPTS_DIR/install_python.sh"
    else
        print_message $RED "Python installation script not found"
        exit 1
    fi
    
    print_message $GREEN "✓ Python 3.13.5 setup complete"
}

# Function to install Python dependencies
install_python_deps() {
    box_echo "Installing Python dependencies..."
    
    # Source the Python executable from .env
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi
    
    if [ -z "$PYTHON_EXECUTABLE" ]; then
        print_message $RED "Python executable not found in environment"
        exit 1
    fi
    
    # Create virtual environment
    sudo -u trailarr "$PYTHON_EXECUTABLE" -m venv "$INSTALL_DIR/venv"
    
    # Install dependencies
    sudo -u trailarr "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    
    if [ -f "$INSTALL_DIR/backend/requirements.txt" ]; then
        sudo -u trailarr "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt"
    else
        # Install basic dependencies if requirements.txt not found
        sudo -u trailarr "$INSTALL_DIR/venv/bin/pip" install \
            fastapi \
            uvicorn \
            sqlmodel \
            alembic \
            sqlite \
            httpx \
            python-multipart
    fi
    
    print_message $GREEN "✓ Python dependencies installed"
}

# Function to detect and setup GPUs
setup_gpu_hardware() {
    box_echo "Detecting and setting up GPU hardware..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh" ]; then
        # Run GPU detection
        source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
        
        # Save results for interactive config
        echo "export DETECTED_GPUS=(${DETECTED_GPUS[*]})" > /tmp/gpu_detection_results
        echo "export AVAILABLE_GPUS=(${AVAILABLE_GPUS[*]})" >> /tmp/gpu_detection_results
        
        # Setup GPU groups for the trailarr user
        setup_gpu_groups "trailarr"
    else
        print_message $YELLOW "GPU setup script not found, skipping GPU configuration"
    fi
    
    print_message $GREEN "✓ GPU hardware detection complete"
}

# Function to install media tools (ffmpeg, yt-dlp)
install_media_tools() {
    box_echo "Installing media processing tools..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/install_media_tools.sh" ]; then
        sudo -u trailarr bash "$BAREMETAL_SCRIPTS_DIR/install_media_tools.sh"
    else
        print_message $RED "Media tools installation script not found"
        exit 1
    fi
    
    print_message $GREEN "✓ Media tools installed"
}

# Function to run interactive configuration
run_interactive_config() {
    box_echo "Starting interactive configuration..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/interactive_config.sh" ]; then
        bash "$BAREMETAL_SCRIPTS_DIR/interactive_config.sh"
    else
        print_message $YELLOW "Interactive config script not found, using defaults"
        # Create basic .env file
        sudo tee "$INSTALL_DIR/.env" > /dev/null << EOF
APP_PORT=7889
APP_DATA_DIR=$DATA_DIR
MONITOR_INTERVAL=10800
WAIT_FOR_MEDIA=true
ENABLE_HWACCEL=false
HWACCEL_TYPE=none
INSTALLATION_MODE=baremetal
TZ=UTC
PYTHONPATH=$INSTALL_DIR/backend
EOF
        sudo chown trailarr:trailarr "$INSTALL_DIR/.env"
    fi
    
    print_message $GREEN "✓ Configuration complete"
}

# Function to create systemd service
create_systemd_service() {
    box_echo "Creating systemd service..."
    
    sudo tee /etc/systemd/system/trailarr.service > /dev/null << EOF
[Unit]
Description=Trailarr - Trailer downloader for Radarr and Sonarr
Documentation=https://github.com/nandyalu/trailarr
After=network.target

[Service]
Type=simple
User=trailarr
Group=trailarr
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR/backend
Environment=APP_DATA_DIR=$DATA_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStartPre=$INSTALL_DIR/scripts/baremetal/baremetal_pre_start.sh
ExecStart=$INSTALL_DIR/scripts/baremetal/baremetal_start.sh
Restart=always
RestartSec=10
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$DATA_DIR $LOG_DIR $INSTALL_DIR/tmp
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    print_message $GREEN "✓ Systemd service created"
}

# Function to install GPU drivers if requested
install_gpu_drivers() {
    # Source configuration
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi
    
    if [ "$ENABLE_HWACCEL" = "true" ] && [ "$HWACCEL_TYPE" != "none" ]; then
        box_echo "Installing GPU drivers for $HWACCEL_TYPE..."
        
        case "$HWACCEL_TYPE" in
            "nvidia")
                if command -v nvidia-smi &> /dev/null; then
                    print_message $GREEN "✓ NVIDIA drivers already installed"
                else
                    print_message $YELLOW "Installing NVIDIA drivers..."
                    source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
                    install_nvidia_drivers
                fi
                ;;
            "intel")
                source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
                install_intel_drivers
                ;;
            "amd")
                source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
                install_amd_drivers
                ;;
        esac
    fi
}

# Function to display completion message
display_completion() {
    print_message $GREEN ""
    print_message $GREEN "🎉 Trailarr installation completed successfully!"
    print_message $GREEN ""
    
    # Source configuration for summary
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi
    
    echo "Installation Summary:"
    echo "  - Installation Directory: $INSTALL_DIR"
    echo "  - Data Directory: $DATA_DIR"
    echo "  - Web Interface: http://localhost:${APP_PORT:-7889}"
    echo "  - Service User: trailarr"
    echo ""
    echo "Next Steps:"
    echo "  1. Enable the service:  sudo systemctl enable trailarr"
    echo "  2. Start the service:   sudo systemctl start trailarr"
    echo "  3. Check service status: sudo systemctl status trailarr"
    echo "  4. View logs:           sudo journalctl -u trailarr -f"
    echo ""
    
    if [ "$ENABLE_HWACCEL" = "true" ] && [ "$HWACCEL_TYPE" = "nvidia" ]; then
        print_message $YELLOW "Note: NVIDIA GPU acceleration is enabled. A reboot may be required"
        print_message $YELLOW "for driver changes to take effect."
    fi
    
    echo "For support and documentation, visit:"
    echo "  https://github.com/nandyalu/trailarr"
    echo ""
}

# Main installation function
main() {
    display_banner
    
    # Pre-installation checks
    check_root
    check_distribution
    
    # Installation steps
    install_system_deps
    create_user_and_dirs
    copy_application_files
    install_python
    install_python_deps
    setup_gpu_hardware
    install_media_tools
    run_interactive_config
    install_gpu_drivers
    create_systemd_service
    
    # Clean up temporary files
    rm -f /tmp/gpu_detection_results
    
    display_completion
}

# Run main installation
main "$@"