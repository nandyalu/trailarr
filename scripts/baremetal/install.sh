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

# Source logging functions
source "$SCRIPT_DIR/logging.sh"

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

# Function to check if running as root or not with sudo
check_root() {
    # Block direct root execution (not via sudo)
    if [[ $EUID -eq 0 && -z "$SUDO_USER" ]]; then
        print_message $RED "Do NOT run this script directly as root."
        print_message $YELLOW "Please run as a regular user with sudo: sudo bash install.sh"
        exit 1
    fi
    # Block non-sudo runs (must be run with sudo)
    if [[ $EUID -ne 0 || -z "$SUDO_USER" ]]; then
        print_message $RED "This script must be run with sudo."
        print_message $YELLOW "Please run as a regular user with sudo: sudo bash install.sh"
        exit 1
    fi
    print_message $GREEN "✓ Running with sudo as user: $SUDO_USER"
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
    start_message "$BLUE" "Installing system dependencies..."

    # Update package list with detailed logging
    if run_logged_command "Update package list" "apt-get update"; then
        log_to_file "Package list updated successfully"
    else
        end_message $RED "✗ Failed to update package list"
        exit 1
    fi

    # Install system dependencies with logging
    local packages="curl wget xz-utils unzip tar git pciutils usbutils ca-certificates build-essential libffi-dev libssl-dev systemd sudo"
    if run_logged_command "Install system packages" "apt-get install -y $packages"; then
        log_to_file "System dependencies installed successfully"
    else
        end_message $RED "✗ Failed to install system dependencies"
        exit 1
    fi

    end_message $GREEN "✓ System dependencies installed"
}

# Function to create trailarr user and directories
create_user_and_dirs() {
    start_message "$BLUE" "Creating trailarr user"

    # Create trailarr user if it doesn't exist
    if ! id "trailarr" &>/dev/null; then
        useradd -r -d "$INSTALL_DIR" -s /bin/bash -m trailarr
        end_message $GREEN "✓ Created 'trailarr' user"
    else
        end_message $YELLOW "! 'trailarr' user already exists"
    fi
    start_message "$BLUE" "Creating required directories"
    # Create necessary directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$INSTALL_DIR/tmp"
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/bin"
    
    # Set ownership
    chown -R trailarr:trailarr "$INSTALL_DIR"
    chown -R trailarr:trailarr "$DATA_DIR"
    chown -R trailarr:trailarr "$LOG_DIR"

    end_message $GREEN "✓ Directories created and configured"
}

download_latest_release() {
    if [ ! -d "$INSTALL_DIR/trailarr" ]; then
        print_message "$BLUE" "Trailarr source code not found."
        start_message "$BLUE" "Downloading latest release"

        # Get the latest release info from GitHub API with logging
        log_to_file "Fetching latest release information from GitHub API"
        local release_json
        if ! release_json=$(curl -s https://api.github.com/repos/nandyalu/trailarr/releases/latest); then
            end_message $RED "✗ Failed to fetch release information from GitHub"
            exit 1
        fi

        # Extract tag_name for version
        APP_VERSION=$(echo "$release_json" | grep '"tag_name":' | head -n1 | cut -d '"' -f4)
        export APP_VERSION
        log_to_file "Latest version detected: $APP_VERSION"

        # Initialize .env file
        touch "$INSTALL_DIR/.env"
        update_env_var "APP_VERSION" "$APP_VERSION" "$INSTALL_DIR/.env"

        # Extract the source code zip URL
        src_archive_url=$(echo "$release_json" | grep "zipball_url" | grep "zip" | head -n1 | cut -d '"' -f4)

        # Fallback to tar.gz if zip not found
        if [ -z "$src_archive_url" ]; then
            src_archive_url=$(echo "$release_json" | grep "tarball_url" | grep "tar.gz" | head -n1 | cut -d '"' -f4)
            archive_type="tar.gz"
            unpacker="tar -xzf"
        else
            archive_type="zip"
            unpacker="unzip -o"
        fi

        log_to_file "Downloading source archive: $src_archive_url"

        # Download and extract with proper logging
        if ! run_logged_command "Download Trailarr source" "curl -L -o \"$INSTALL_DIR/trailarr-source.$archive_type\" \"$src_archive_url\""; then
            end_message $RED "✗ Failed to download Trailarr source code"
            exit 1
        fi

        # Extract the downloaded archive with logging
        if ! run_logged_command "Extract Trailarr source" "$unpacker \"$INSTALL_DIR/trailarr-source.$archive_type\" -d \"$INSTALL_DIR/tmp-unpack\""; then
            end_message $RED "✗ Failed to extract Trailarr source code archive"
            exit 1
        fi

        # Find the extracted folder (should be the only directory inside tmp-unpack)
        extracted_dir=$(find "$INSTALL_DIR/tmp-unpack" -mindepth 1 -maxdepth 1 -type d | head -n1)
        log_to_file "Extracted directory: $extracted_dir"

        # Remove any existing target directory
        rm -rf "$INSTALL_DIR/trailarr"

        # Move/rename the extracted folder
        mv "$extracted_dir" "$INSTALL_DIR/trailarr"

        # Clean up temp files
        rm -rf "$INSTALL_DIR/tmp-unpack"
        rm "$INSTALL_DIR/trailarr-source.$archive_type"
        
        print_message $BLUE "→ Version: $APP_VERSION"
        SCRIPT_DIR="$INSTALL_DIR/trailarr/scripts/"
        end_message $GREEN "✓ Trailarr source code downloaded and extracted"
    fi
}

# Function to copy application files
copy_application_files() {
    start_message "$BLUE" "Copying application files..."

    # Copy source code
    cp -r "$SCRIPT_DIR/../../backend" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/../../frontend-build" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/../../assets" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/../../scripts" "$INSTALL_DIR/"

    # Copy configuration files
    cp "$SCRIPT_DIR/../../backend/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true

    # Set ownership
    chown -R trailarr:trailarr "$INSTALL_DIR"

    end_message $GREEN "✓ Application files copied"
}

# Function to run Python installation
install_python() {
    start_message "$BLUE" "Setting up Python 3.13.5..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/install_python.sh" ]; then
        sudo -u trailarr bash "$BAREMETAL_SCRIPTS_DIR/install_python.sh"
    else
        end_message $RED "✗ Python installation script not found"
        exit 1
    fi

    end_message $GREEN "✓ Python 3.13.5 setup complete"
}

# Function to install Python dependencies
install_python_deps() {
    start_message "$BLUE" "Installing Python dependencies..."

    # Source the Python executable from .env
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi
    
    if [ -z "$PYTHON_EXECUTABLE" ]; then
        end_message $RED "✗ Python executable not found in environment"
        exit 1
    fi
    
    log_to_file "Using Python executable: $PYTHON_EXECUTABLE"
    
    # Create virtual environment with logging
    if ! run_logged_command "Create Python virtual environment" "sudo -u trailarr \"$PYTHON_EXECUTABLE\" -m venv \"$INSTALL_DIR/venv\""; then
        end_message $RED "✗ Failed to create Python virtual environment"
        exit 1
    fi

    # Install/upgrade pip with logging
    if ! run_logged_command "Upgrade pip" "sudo -u trailarr \"$INSTALL_DIR/venv/bin/pip\" install --upgrade pip"; then
        end_message $RED "✗ Failed to install/upgrade pip"
        exit 1
    fi

    # Install dependencies
    if [ -f "$INSTALL_DIR/backend/requirements.txt" ]; then
        log_to_file "Installing dependencies from requirements.txt"
        if ! run_logged_command "Install Python dependencies from requirements.txt" "sudo -u trailarr \"$INSTALL_DIR/venv/bin/pip\" install -r \"$INSTALL_DIR/backend/requirements.txt\""; then
            end_message $RED "✗ Failed to install Python dependencies"
            exit 1
        fi
    else
        # Install basic dependencies if requirements.txt not found
        log_to_file "requirements.txt not found, installing basic dependencies"
        local basic_deps="aiohttp aiofiles aiosqlite alembic apscheduler async-lru bcrypt fastapi[standard-no-fastapi-cloud-cli] pillow sqlmodel yt-dlp[default,curl-cffi]"
        if ! run_logged_command "Install basic Python dependencies" "sudo -u trailarr \"$INSTALL_DIR/venv/bin/pip\" install $basic_deps"; then
            end_message $RED "✗ Failed to install basic Python dependencies"
            exit 1
        fi
    fi

    # Save Python executable and related paths to .env file
    update_env_var "PYTHON_EXECUTABLE" "$PYTHON_EXECUTABLE" "$DATA_DIR/.env"
    update_env_var "PYTHON_VENV" "$INSTALL_DIR/venv" "$DATA_DIR/.env"
    update_env_var "PYTHONPATH" "$INSTALL_DIR/backend" "$DATA_DIR/.env"

    end_message $GREEN "✓ Python dependencies installed"
}

# Function to add trailarr user to GPU groups for hardware access
configure_gpu_user_permissions() {
    print_message $BLUE "→ Configuring GPU permissions for trailarr user"

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
        print_message $BLUE "→ Checking groups for detected Intel/AMD GPU devices"

        # Check Intel GPU device group if detected
        if [ -n "$GPU_DEVICE_INTEL" ] && [ -e "$GPU_DEVICE_INTEL" ]; then
            intel_gid=$(stat -c '%g' "$GPU_DEVICE_INTEL" 2>/dev/null)
            if [[ -n "$intel_gid" ]]; then
                if getent group "$intel_gid" > /dev/null 2>&1; then
                    intel_group_name=$(getent group "$intel_gid" | cut -d: -f1)
                else
                    intel_group_name="gpuintel"
                    print_message $BLUE "→ Creating group '$intel_group_name' with GID '$intel_gid'"
                    groupadd -g "$intel_gid" "$intel_group_name"
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
                    print_message $BLUE "→ Creating group '$amd_group_name' with GID '$amd_gid'"
                    groupadd -g "$amd_gid" "$amd_group_name"
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
        print_message $BLUE "→ GPU groups identified for trailarr user:$groups_found"

        for group in "${gpu_groups[@]}"; do
            group_entry=$(getent group "$group")
            if [ -n "$group_entry" ]; then
                group_name=$(echo "$group_entry" | cut -d: -f1)
                print_message $BLUE "→ Adding user 'trailarr' to group '$group_name'"
                usermod -aG "$group_name" trailarr
            fi
        done
        
        end_message $GREEN "✓ trailarr user added to GPU groups for hardware acceleration access"
    else
        print_message $YELLOW "→ No GPU groups found for hardware acceleration"
        end_message $YELLOW "! trailarr user will not have GPU hardware acceleration access"
    fi
}

# Function to detect GPU hardware
setup_gpu_hardware() {
    start_message $BLUE "Detecting GPU hardware..."

    if [ -f "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh" ]; then
        # Run GPU detection only
        source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
        
        # Save results for interactive config
        echo "export DETECTED_GPUS=(${DETECTED_GPUS[*]})" > /tmp/gpu_detection_results
        echo "export AVAILABLE_GPUS=(${AVAILABLE_GPUS[*]})" >> /tmp/gpu_detection_results
        
        # Configure GPU user permissions after detection
        configure_gpu_user_permissions
    else
        end_message $YELLOW "→ GPU setup script not found, skipping GPU configuration"
    fi

    end_message $GREEN "✓ GPU hardware detection complete"
}

# Function to install media tools (ffmpeg, yt-dlp)
install_media_tools() {
    start_message $BLUE "Installing media processing tools..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/install_media_tools.sh" ]; then
        sudo -u trailarr bash "$BAREMETAL_SCRIPTS_DIR/install_media_tools.sh"
    else
        end_message $RED "✗ Media tools installation script not found"
        exit 1
    fi

    end_message $GREEN "✓ Media tools installed"
}

# Function to run interactive configuration
run_interactive_config() {
    print_message $BLUE "Starting interactive configuration..."
    
    if [ -f "$BAREMETAL_SCRIPTS_DIR/interactive_config.sh" ]; then
        bash "$BAREMETAL_SCRIPTS_DIR/interactive_config.sh"
    else
        print_message $YELLOW "→ Interactive config script not found, using defaults"
        # Create basic .env file with proper variable handling
        update_env_var "APP_PORT" "7889" "$DATA_DIR/.env"
        update_env_var "APP_DATA_DIR" "$DATA_DIR" "$DATA_DIR/.env"
        update_env_var "MONITOR_INTERVAL" "60" "$DATA_DIR/.env"
        update_env_var "WAIT_FOR_MEDIA" "true" "$DATA_DIR/.env"
        update_env_var "ENABLE_HWACCEL" "false" "$DATA_DIR/.env"
        update_env_var "HWACCEL_TYPE" "none" "$DATA_DIR/.env"
        update_env_var "INSTALLATION_MODE" "baremetal" "$DATA_DIR/.env"
        update_env_var "PYTHONPATH" "$INSTALL_DIR/backend" "$DATA_DIR/.env"
        
        chown trailarr:trailarr "$DATA_DIR/.env"
    fi
    
    print_message $GREEN "✓ Configuration complete"
}

# Function to create and start systemd service
create_systemd_service() {
    start_message $BLUE "Creating systemd service..."

    tee /etc/systemd/system/trailarr.service > /dev/null << EOF
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
    systemctl daemon-reload
    systemctl enable trailarr
    
    end_message $GREEN "✓ Systemd service created and enabled"
    
    # Start the service
    start_message $BLUE "Starting Trailarr service..."
    if systemctl start trailarr; then
        end_message $GREEN "✓ Trailarr service started successfully"
        
        # Wait a moment and check status
        sleep 3
        if systemctl is-active --quiet trailarr; then
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
    # Initialize logging first
    init_logging
    
    display_banner
    
    # Pre-installation checks
    check_root
    check_distribution
    
    # Installation steps
    install_system_deps
    create_user_and_dirs
    download_latest_release
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
    
    # Show log file location
    show_log_location
}

# Run main installation
main "$@"
