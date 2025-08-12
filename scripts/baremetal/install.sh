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
######## ########     ###    #### ##          ###    ########  ######## 
   ##    ##     ##   ## ##    ##  ##         ## ##   ##     ## ##     ##
   ##    ##     ##  ##   ##   ##  ##        ##   ##  ##     ## ##     ##
   ##    ########  ##     ##  ##  ##       ##     ## ########  ######## 
   ##    ##   ##   #########  ##  ##       ######### ##   ##   ##   ##  
   ##    ##    ##  ##     ##  ##  ##       ##     ## ##    ##  ##    ## 
   ##    ##     ## ##     ## #### ######## ##     ## ##     ## ##     ##

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
            aiohttp \
            aiofiles \
            aiosqlite \
            alembic \
            apscheduler \
            async-lru \
            bcrypt \
            fastapi[standard-no-fastapi-cloud-cli] \
            pillow \
            sqlmodel \
            yt-dlp[default,curl-cffi]
    fi
    
    print_message $GREEN "✓ Python dependencies installed"
}

# Function to add trailarr user to GPU groups for hardware access
configure_gpu_user_permissions() {
    box_echo "Configuring GPU permissions for trailarr user..."
    
    # Initialize array of GPU groups to add user to
    local gpu_groups=()
    local groups_found=""
    
    # Function to check if group exists in array
    group_exists() {
        local group_to_check="$1"
        local group
        for group in "${gpu_groups[@]}"; do
            if [ "$group" = "$group_to_check" ]; then
                return 0
            fi
        done
        return 1
    }
    
    # Check for render group (for GPU access)
    if getent group render > /dev/null 2>&1; then
        gpu_groups+=("render")
        groups_found="$groups_found render"
    fi
    
    # Check for video group (for video device access)  
    if getent group video > /dev/null 2>&1; then
        gpu_groups+=("video")
        groups_found="$groups_found video"
    fi
    
    # Load GPU device information if available
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi
    
    # Check for specific DRI device groups for detected Intel/AMD GPUs
    if [ -n "$GPU_DEVICE_INTEL" ] || [ -n "$GPU_DEVICE_AMD" ]; then
        box_echo "Checking groups for detected Intel/AMD GPU devices..."
        
        # Check Intel GPU device group if detected
        if [ -n "$GPU_DEVICE_INTEL" ] && [ -e "$GPU_DEVICE_INTEL" ]; then
            intel_gid=$(stat -c '%g' "$GPU_DEVICE_INTEL" 2>/dev/null)
            if [[ -n "$intel_gid" ]]; then
                if getent group "$intel_gid" > /dev/null 2>&1; then
                    intel_group_name=$(getent group "$intel_gid" | cut -d: -f1)
                else
                    intel_group_name="gpuintel"
                    box_echo "Creating group '$intel_group_name' with GID '$intel_gid'"
                    sudo groupadd -g "$intel_gid" "$intel_group_name"
                fi
                
                if ! group_exists "$intel_group_name"; then
                    gpu_groups+=("$intel_group_name")
                    groups_found="$groups_found $intel_group_name($intel_gid)"
                fi
            fi
        fi
        
        # Check AMD GPU device group if detected
        if [ -n "$GPU_DEVICE_AMD" ] && [ -e "$GPU_DEVICE_AMD" ]; then
            amd_gid=$(stat -c '%g' "$GPU_DEVICE_AMD" 2>/dev/null)
            if [[ -n "$amd_gid" ]]; then
                if getent group "$amd_gid" > /dev/null 2>&1; then
                    amd_group_name=$(getent group "$amd_gid" | cut -d: -f1)
                else
                    amd_group_name="gpuamd"
                    box_echo "Creating group '$amd_group_name' with GID '$amd_gid'"
                    sudo groupadd -g "$amd_gid" "$amd_group_name"
                fi
                
                if ! group_exists "$amd_group_name"; then
                    gpu_groups+=("$amd_group_name")
                    groups_found="$groups_found $amd_group_name($amd_gid)"
                fi
            fi
        fi
    fi
    
    # Check for common GPU device group IDs (226, 128, 129) if they exist
    for gid in 226 128 129; do
        if getent group "$gid" > /dev/null 2>&1; then
            group_name=$(getent group "$gid" | cut -d: -f1)
            if ! group_exists "$group_name"; then
                gpu_groups+=("$group_name")
                groups_found="$groups_found $group_name($gid)"
            fi
        fi
    done
    
    # Add trailarr user to identified GPU groups
    if [ ${#gpu_groups[@]} -gt 0 ]; then
        box_echo "GPU groups identified for trailarr user:$groups_found"
        
        for group in "${gpu_groups[@]}"; do
            group_entry=$(getent group "$group")
            if [ -n "$group_entry" ]; then
                group_name=$(echo "$group_entry" | cut -d: -f1)
                box_echo "Adding user 'trailarr' to group '$group_name'"
                sudo usermod -aG "$group_name" trailarr
            fi
        done
        
        print_message $GREEN "✓ trailarr user added to GPU groups for hardware acceleration access"
    else
        box_echo "No GPU groups found for hardware acceleration"
        print_message $YELLOW "! trailarr user will not have GPU hardware acceleration access"
    fi
}

# Function to detect GPU hardware
setup_gpu_hardware() {
    box_echo "Detecting GPU hardware..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh" ]; then
        # Run GPU detection only
        source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
        
        # Save results for interactive config
        echo "export DETECTED_GPUS=(${DETECTED_GPUS[*]})" > /tmp/gpu_detection_results
        echo "export AVAILABLE_GPUS=(${AVAILABLE_GPUS[*]})" >> /tmp/gpu_detection_results
        
        # Configure GPU user permissions after detection
        configure_gpu_user_permissions
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
        sudo tee "$DATA_DIR/.env" > /dev/null << EOF
APP_PORT=7889
APP_DATA_DIR=$DATA_DIR
MONITOR_INTERVAL=60
WAIT_FOR_MEDIA=true
ENABLE_HWACCEL=false
HWACCEL_TYPE=none
INSTALLATION_MODE=baremetal
PYTHONPATH=$INSTALL_DIR/backend
EOF
        sudo chown trailarr:trailarr "$INSTALL_DIR/.env"
    fi
    
    print_message $GREEN "✓ Configuration complete"
}

# Function to create and start systemd service
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
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable trailarr
    
    print_message $GREEN "✓ Systemd service created and enabled"
    
    # Start the service
    box_echo "Starting Trailarr service..."
    if sudo systemctl start trailarr; then
        print_message $GREEN "✓ Trailarr service started successfully"
        
        # Wait a moment and check status
        sleep 3
        if sudo systemctl is-active --quiet trailarr; then
            print_message $GREEN "✓ Trailarr service is running"
        else
            print_message $YELLOW "⚠ Service started but may need time to initialize"
            print_message $YELLOW "Check status with: sudo systemctl status trailarr"
        fi
    else
        print_message $YELLOW "⚠ Failed to start service automatically"
        print_message $YELLOW "You can start it manually with: sudo systemctl start trailarr"
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
    echo "  1. Check service status: sudo systemctl status trailarr"
    echo "  2. View logs:           sudo journalctl -u trailarr -f"
    echo "  3. Access web interface: http://localhost:${APP_PORT:-7889}"
    echo ""
    
    if [ "$ENABLE_HWACCEL" = "true" ] && [ "$HWACCEL_TYPE" != "none" ]; then
        print_message $YELLOW "Note: GPU hardware acceleration is enabled for $HWACCEL_TYPE."
        print_message $YELLOW "Ensure required drivers are installed for optimal performance."
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
    create_systemd_service
    
    # Clean up temporary files
    rm -f /tmp/gpu_detection_results
    
    display_completion
}

# Run main installation
main "$@"
