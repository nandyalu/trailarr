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
    local packages="curl wget xz-utils unzip tar git pciutils udev usbutils ca-certificates build-essential libffi-dev libssl-dev systemd sudo"
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

    show_temp_message "Cleaning up existing install directories"
    if [[ -n "$INSTALL_DIR" && "$INSTALL_DIR" != "/" && -d "$INSTALL_DIR" ]]; then
        rm -rf "${INSTALL_DIR:?}"
        show_message $GREEN "Deleted $INSTALL_DIR"
    else
        show_message $YELLOW "Existing installation not found. Skipping..."
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

    show_message "$GREEN" "Directories created and configured"
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

    show_message "$GREEN" "Application files copied"
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
    show_message $GREEN "uv installed successfully"
    
    # Add uv to PATH for trailarr user
    show_temp_message "Adding uv to trailarr PATH"
    sudo -u trailarr bash -c 'echo export PATH="\$HOME/.local/bin:\$PATH" >> $HOME/.bashrc'
    show_message $GREEN "uv added to PATH for trailarr user"

    # Navigate to backend directory and run uv sync
    show_temp_message "Creating Python venv and installing dependencies with uv sync"
    cmd="cd \"$INSTALL_DIR/backend\" && \"$INSTALL_DIR/.local/bin/uv\" sync --no-cache-dir"
    if ! run_logged_command "Create venv and install Python dependencies with uv sync" "sudo -u trailarr bash -c '$cmd'"; then
        show_message $RED "Failed to create venv and install Python dependencies with uv"
        end_message $RED "Failed to install Python dependencies"
        exit 1
    fi
    show_message $GREEN "Python dependencies installed successfully with uv"
    
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
    show_message $GREEN "Python environment configured in $DATA_DIR/.env"

    show_message $GREEN "Python dependencies installed with uv"
}

# Function to install media tools (ffmpeg, yt-dlp)
install_media_tools() {
    show_temp_message "Installing media processing tools (ffmpeg, yt-dlp)"
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
    show_message ""
    show_message "Setting up Trailarr configuration..."
    show_message ""
    
    # Ask for port number only
    local default_port=7889
    local port
    
    while true; do
        echo -n "Web interface port [$default_port]: "
        read -r port
        port=${port:-$default_port}
        
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt 1023 ] && [ "$port" -lt 65536 ]; then
            break
        else
            show_message $RED "Invalid port: '$port'"
            show_message $YELLOW "Please enter a valid port number (1024-65535)"
        fi
    done
    
    show_message $GREEN "Web interface port set to: $port"
    
    # Set all other values to defaults without asking
    show_temp_message "Setting up default configuration"
    
    # Create .env file with configuration
    update_env_var "APP_VERSION" "${APP_VERSION:-0.0.0}" "$DATA_DIR/.env"
    update_env_var "APP_DATA_DIR" "$DATA_DIR" "$DATA_DIR/.env"
    update_env_var "APP_PORT" "$port" "$DATA_DIR/.env"
    update_env_var "INSTALLATION_MODE" "baremetal" "$DATA_DIR/.env"
    update_env_var "MONITOR_INTERVAL" "60" "$DATA_DIR/.env"  # 1 hour default
    update_env_var "PYTHONPATH" "/opt/trailarr/backend" "$DATA_DIR/.env"
    update_env_var "WAIT_FOR_MEDIA" "true" "$DATA_DIR/.env"  # Default to wait for media
    
    # Set timezone
    TZ=$(timedatectl | grep "Time zone" | awk '{print $3}' 2>/dev/null || echo "UTC")
    update_env_var "TZ" "$TZ" "$DATA_DIR/.env"
    
    # Set ownership
    chown trailarr:trailarr "$DATA_DIR/.env"
    
    show_message $GREEN "Configuration saved to '$DATA_DIR/.env'"
    show_message $BLUE "Default settings applied:"
    show_message $BLUE "  - Monitor interval: 60 minutes (can be changed in web UI)"
    show_message $BLUE "  - Wait for media: enabled (can be changed in web UI)"
    show_message $BLUE "  - All other settings: defaults (configurable in web UI)"
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
Environment=PATH=/opt/trailarr/.local/bin:/opt/trailarr/backend/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EnvironmentFile=$DATA_DIR/.env
ExecStartPre=+$INSTALL_DIR/scripts/baremetal/baremetal_pre_start.sh
ExecStart=$INSTALL_DIR/scripts/baremetal/baremetal_start.sh
Restart=always
RestartSec=60
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=$DATA_DIR $LOG_DIR $INSTALL_DIR
#ProtectHome=true
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
    
    start_message "Installing media processing tools"
    install_media_tools
    end_message "Media processing tools installed"
    
    show_message ""
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
