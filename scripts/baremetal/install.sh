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
TRAILARR_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
    show_message $GREEN "Trailarr Version: $TRAILARR_VERSION"
    show_message $BLUE "Installing Trailarr directly on your system for maximum performance"
    show_message $BLUE "with native GPU hardware acceleration support"
    echo ""
}

# Function to check if running as root or not with sudo
check_root() {
    # Block direct root execution (not via sudo)
    if [[ $EUID -eq 0 && -z "$SUDO_USER" ]]; then
        show_message $RED "Do NOT run this script directly as root."
        show_message $YELLOW "Please run as a regular user with sudo:"
        show_message $YELLOW ">>>    sudo bash install.sh"
        exit 1
    fi
    # Block non-sudo runs (must be run with sudo)
    if [[ $EUID -ne 0 || -z "$SUDO_USER" ]]; then
        show_message $RED "This script must be run with sudo."
        show_message $YELLOW "Please run as a regular user with sudo:"
        show_message $YELLOW ">>>    sudo bash install.sh"
        exit 1
    fi
    show_message $GREEN "Running with sudo as user: $SUDO_USER"
}

# Function to check if distribution is supported
check_distribution() {
    if [ ! -f /etc/debian_version ]; then
        show_message $RED "This installation script only supports Debian-based distributions."
        show_message $YELLOW "Please use Docker installation for other distributions."
        exit 1
    fi
    
    show_message $GREEN "Debian-based distribution detected"
}

# Function to install system dependencies
install_system_deps() {
    # Update package list with detailed logging
    show_temp_message "Updating package list"
    if run_logged_command "Update package list" "apt-get update"; then
        show_message $GREEN "Package list updated successfully"
    else
        show_message $RED "Failed to update package list"
        end_message $RED "Failed to update package list"
        exit 1
    fi

    # Install system dependencies with logging
    local packages="curl wget xz-utils unzip tar git pciutils usbutils ca-certificates build-essential libffi-dev libssl-dev systemd sudo"
    show_temp_message "Installing system dependencies"
    if run_logged_command "Install system dependencies" "apt-get install -y $packages"; then
        show_message $GREEN "System dependencies installed successfully"
    else
        show_message $RED "Failed to install system dependencies"
        end_message $RED "Failed to install system dependencies"
        exit 1
    fi
}

# Function to create trailarr user and directories
create_user_and_dirs() {
    show_temp_message "Creating trailarr user and directories"

    # Create trailarr user if it doesn't exist
    show_temp_message "Checking for trailarr user"
    if ! id "trailarr" &>/dev/null; then
        show_temp_message "Creating trailarr user"
        useradd -r -d "$INSTALL_DIR" -s /bin/bash -m trailarr
        show_message $GREEN "Created 'trailarr' user"
    else
        show_message $YELLOW "'trailarr' user already exists"
    fi
    
    show_temp_message "Creating required directories"
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

    show_message "Directories created and configured"
}

# Function to copy application files
copy_application_files() {
    show_temp_message "Copying application files"

    # Check if source directories exist before copying
    show_temp_message "Verifying source directories"
    for dir in backend frontend-build assets scripts; do
        if [ ! -d "${TRAILARR_DIR}/$dir" ]; then
            show_message $RED "Source directory ${TRAILARR_DIR}/$dir does not exist"
            show_message $RED "Try running the install script again from project root!"
            end_message $RED "Source directories missing"
            exit 1
        fi
    done

    # Copy source code
    show_temp_message "Copying backend files"
    cp -r "${TRAILARR_DIR}/backend" "$INSTALL_DIR/"
    show_temp_message "Copying frontend files"
    cp -r "${TRAILARR_DIR}/frontend-build" "$INSTALL_DIR/"
    show_temp_message "Copying assets"
    cp -r "${TRAILARR_DIR}/assets" "$INSTALL_DIR/"
    show_temp_message "Copying scripts"
    cp -r "${TRAILARR_DIR}/scripts" "$INSTALL_DIR/"

    # Set ownership
    show_temp_message "Setting file ownership"
    chown -R trailarr:trailarr "$INSTALL_DIR"

    show_message "Application files copied"
}

# Function to install Python and dependencies with uv
install_python_and_deps() {
    show_temp_message "Installing uv package manager and Python dependencies"
    
    # Define the uv installation path
    UV_INSTALL_PATH="$INSTALL_DIR/.local/bin"

    # Install uv for trailarr user
    show_temp_message "Installing uv package manager"
    if ! run_logged_command "Install uv for trailarr user" "sudo -u trailarr bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'"; then
        show_message $RED "Failed to install uv"
        end_message $RED "uv installation failed"
        exit 1
    fi
    
    # Add uv to PATH for trailarr user
    # Note: Use double quotes to expand INSTALL_DIR, but escape the dollar in $PATH
    run_logged_command "Add uv to trailarr PATH" "sudo -u trailarr bash -c 'echo \"export PATH=\\\"\$HOME/.local/bin:\\\$PATH\\\"\" >> \$HOME/.bashrc'" || true
    
    # Navigate to backend directory and run uv sync
    show_temp_message "Creating Python venv and installing dependencies with uv sync"
    cmd="source ~/.bashrc && cd \"$INSTALL_DIR/backend\" && uv sync --no-cache-dir"
    if ! run_logged_command "Create venv and install Python dependencies with uv sync" "sudo -u trailarr bash -c '$cmd'"; then
        show_message $RED "Failed to create venv and install Python dependencies with uv"
        end_message $RED "Failed to install Python dependencies"
        exit 1
    fi
    
    # Get the Python executable from the created venv
    PYTHON_EXECUTABLE="$INSTALL_DIR/backend/.venv/bin/python"
    
    if [ ! -f "$PYTHON_EXECUTABLE" ]; then
        show_message $RED "Python executable not found in created venv"
        end_message $RED "Python executable not found"
        exit 1
    fi
    
    # Save Python executable and related paths to .env file
    show_temp_message "Configuring environment variables"
    update_env_var "PYTHON_EXECUTABLE" "$PYTHON_EXECUTABLE" "$DATA_DIR/.env"
    update_env_var "PYTHON_VENV" "$INSTALL_DIR/backend/.venv" "$DATA_DIR/.env"
    update_env_var "PYTHONPATH" "$INSTALL_DIR/backend" "$DATA_DIR/.env"

    show_message "Python dependencies installed with uv"
}

# Function to add trailarr user to GPU groups for hardware access
configure_gpu_user_permissions() {
    show_temp_message "Configuring GPU permissions for trailarr user"

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
        show_temp_message "Checking groups for detected Intel/AMD GPU devices"

        # Check Intel GPU device group if detected
        if [ -n "$GPU_DEVICE_INTEL" ] && [ -e "$GPU_DEVICE_INTEL" ]; then
            intel_gid=$(stat -c '%g' "$GPU_DEVICE_INTEL" 2>/dev/null)
            if [[ -n "$intel_gid" ]]; then
                if getent group "$intel_gid" > /dev/null 2>&1; then
                    intel_group_name=$(getent group "$intel_gid" | cut -d: -f1)
                else
                    intel_group_name="gpuintel"
                    show_temp_message "Creating group '$intel_group_name' with GID '$intel_gid'"
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
                    show_temp_message "Creating group '$amd_group_name' with GID '$amd_gid'"
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
        show_temp_message "GPU groups identified for trailarr user:$groups_found"

        for group in "${gpu_groups[@]}"; do
            group_entry=$(getent group "$group")
            if [ -n "$group_entry" ]; then
                group_name=$(echo "$group_entry" | cut -d: -f1)
                show_temp_message "Adding user 'trailarr' to group '$group_name'"
                usermod -aG "$group_name" trailarr
            fi
        done
        
        show_message $GREEN "trailarr user added to GPU groups for hardware acceleration access"
    else
        show_message $YELLOW "No GPU groups found for hardware acceleration"
    fi
}

# Function to detect GPU hardware
setup_gpu_hardware() {
    show_temp_message "Detecting GPU hardware for Trailarr"
    sleep 3
    if [ -f "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh" ]; then
        # Run GPU detection only
        show_temp_message "Running GPU detection script"
        sleep 3
        source "$BAREMETAL_SCRIPTS_DIR/gpu_setup.sh"
        show_temp_message "GPU detection script completed"
        sleep 3
        # Save results for interactive config
        echo "export DETECTED_GPUS=(${DETECTED_GPUS[*]})" > /tmp/gpu_detection_results
        echo "export AVAILABLE_GPUS=(${AVAILABLE_GPUS[*]})" >> /tmp/gpu_detection_results
        
        # Configure GPU user permissions after detection
        show_temp_message "Configuring GPU user permissions"
        sleep 3
        configure_gpu_user_permissions
        show_temp_message "GPU user permissions configured"

        show_message $GREEN "GPU hardware detection and setup complete"
    else
        sleep 3
        show_message $YELLOW "GPU setup script not found, skipping GPU configuration"
    fi
}

# Function to install media tools (ffmpeg, yt-dlp)
install_media_tools() {
    if [ -f "$BAREMETAL_SCRIPTS_DIR/install_media_tools.sh" ]; then
        sudo -u trailarr bash "$BAREMETAL_SCRIPTS_DIR/install_media_tools.sh"
        show_message $GREEN "Media tools installed"
    else
        end_message $RED "Media tools installation script not found"
        exit 1
    fi
}

# Function to run interactive configuration
run_interactive_config() {
    if [ -f "$BAREMETAL_SCRIPTS_DIR/interactive_config.sh" ]; then
        bash "$BAREMETAL_SCRIPTS_DIR/interactive_config.sh"
    else
        show_temp_message "Setting up default configuration"
        show_message $YELLOW "Interactive config script not found, using defaults"
        # Create basic .env file with proper variable handling
        show_temp_message "Creating default configuration"
        update_env_var "APP_PORT" "7889" "$DATA_DIR/.env"
        update_env_var "APP_DATA_DIR" "$DATA_DIR" "$DATA_DIR/.env"
        update_env_var "MONITOR_INTERVAL" "60" "$DATA_DIR/.env"
        update_env_var "WAIT_FOR_MEDIA" "true" "$DATA_DIR/.env"
        update_env_var "INSTALLATION_MODE" "baremetal" "$DATA_DIR/.env"
        update_env_var "PYTHONPATH" "$INSTALL_DIR/backend" "$DATA_DIR/.env"
        
        chown trailarr:trailarr "$DATA_DIR/.env"
        show_message "Default configuration applied"
    fi
}

# Function to create and start systemd service
create_systemd_service() {
    show_temp_message "Creating systemd service"

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
    show_temp_message "Enabling systemd service"
    systemctl daemon-reload
    systemctl enable trailarr
    
    show_message $GREEN "Systemd service created and enabled"
    
    # Start the service
    show_temp_message "Starting Trailarr service"
    if systemctl start trailarr; then
        show_message $GREEN "Trailarr service started successfully"
        
        # Wait a moment and check status
        sleep 3
        if systemctl is-active --quiet trailarr; then
            show_message $GREEN "Trailarr service is running"
        else
            show_message $YELLOW "Service started but may need time to initialize"
            show_message $YELLOW "Check status with: "
            show_message $YELLOW ">>>    sudo systemctl status trailarr"
        fi
    else
        show_message $YELLOW "Failed to start service automatically"
        show_message $YELLOW "You can start it manually with: "
        show_message $YELLOW ">>>    sudo systemctl start trailarr"
    fi
    
    show_message "Systemd service configured"
}

# Function to install Trailarr CLI
install_trailarr_cli() {
    show_temp_message "Installing Trailarr CLI command"
    
    # Copy the CLI script to system path
    if [ -f "$INSTALL_DIR/scripts/baremetal/trailarr_cli.sh" ]; then
        cp "$INSTALL_DIR/scripts/baremetal/trailarr_cli.sh" /usr/local/bin/trailarr
        chmod +x /usr/local/bin/trailarr
        show_message $GREEN "Trailarr CLI installed successfully"
        show_message $BLUE "You can now use commands like:"
        show_message $BLUE "  trailarr run       - Start Trailarr"
        show_message $BLUE "  trailarr stop      - Stop Trailarr"
        show_message $BLUE "  trailarr restart   - Restart Trailarr"
        show_message $BLUE "  trailarr status    - Check status"
        show_message $BLUE "  trailarr logs      - View logs"
        show_message $BLUE "  trailarr update    - Update to latest version"
        show_message $BLUE "  trailarr uninstall - Uninstall Trailarr"
    else
        show_message $YELLOW "CLI script not found, skipping CLI installation"
    fi
}

# Function to display completion message
display_completion() {
    show_message ""
    show_message $GREEN "🎉 Trailarr installation completed successfully!"
    show_message ""
    
    # Source configuration for summary
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi
    
    show_message "Installation Summary:"
    show_message "  - Installation Directory: $INSTALL_DIR"
    show_message "  - Data Directory: $DATA_DIR"
    show_message "  - Web Interface: http://localhost:${APP_PORT:-7889}"
    show_message "  - Service User: trailarr"
    show_message ""
    show_message "Next Steps:"
    show_message "  1. Check service status:"
    show_message ">>>    sudo systemctl status trailarr"
    show_message "  2. View logs:"
    show_message ">>>    sudo journalctl -u trailarr -f"
    show_message "  3. Access web interface: "
    show_message ">>>    http://localhost:${APP_PORT:-7889}"
    show_message ""

    show_message "For support and documentation, visit:"
    show_message "  https://github.com/nandyalu/trailarr"
    show_message ""
}

# Main installation function
main() {
    # Initialize logging first
    init_logging
    
    display_banner
    
    # Pre-installation checks
    start_message "Pre-installation checks"
    check_root
    check_distribution
    end_message "Pre-installation checks complete"
    
    # Installation steps
    start_message "Installing Dependencies"
    install_system_deps
    end_message "System dependencies installed successfully"

    # Setup User and Directories
    start_message "Creating user and setting up directories"
    create_user_and_dirs
    copy_application_files
    end_message "User created and directories set up"

    # Install Python and dependencies
    start_message "Setting up Python environment"
    install_python_and_deps
    end_message "Python environment ready"
    
    # GPU Detection
    start_message "GPU hardware detection and setup"
    setup_gpu_hardware
    end_message "GPU hardware detection and setup complete"
    
    start_message "Installing media processing tools"
    install_media_tools
    end_message "Media processing tools installed"
    
    show_message "Configuring Trailarr"
    run_interactive_config
    show_message "Trailarr configuration complete"
    
    # Create systemd service
    start_message "Setting up systemd service"
    create_systemd_service
    end_message "Systemd service created and enabled"
    
    # Install Trailarr CLI
    start_message "Installing Trailarr CLI"
    install_trailarr_cli
    end_message "Trailarr CLI installed"
    
    # Clean up temporary files
    rm -f /tmp/gpu_detection_results
    
    display_completion
    
    # Show log file location
    show_log_location
}

# Run main installation
main "$@"
