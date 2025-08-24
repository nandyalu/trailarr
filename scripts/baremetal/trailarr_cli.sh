#!/bin/bash

# Trailarr CLI Management Script
# Provides commands to manage Trailarr service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/trailarr"
SERVICE_NAME="trailarr"
GITHUB_REPO="nandyalu/trailarr"

# Function to display colored messages
show_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if script is run as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        show_message "$RED" "Error: This command requires root privileges. Please run with sudo."
        exit 1
    fi
}

# Function to check if Trailarr is installed
check_installation() {
    if [ ! -d "$INSTALL_DIR" ] || [ ! -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        show_message "$RED" "Error: Trailarr is not installed or installation is incomplete."
        show_message "$YELLOW" "Please run the installation script first."
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Trailarr Management CLI"
    echo ""
    echo "Usage: trailarr <command>"
    echo ""
    echo "Commands:"
    echo "  run        Start the Trailarr service"
    echo "  stop       Stop the Trailarr service"
    echo "  restart    Restart the Trailarr service"
    echo "  status     Show the status of Trailarr service"
    echo "  logs       Show recent logs from Trailarr service."
    echo "             Optionally provide line count. Defaults to 50"
    echo "  update     Update Trailarr to the latest version"
    echo "  uninstall  Uninstall Trailarr and its service"
    echo ""
    echo "Examples:"
    echo "  sudo trailarr run"
    echo "  sudo trailarr status"
    echo "  sudo trailarr logs"
    echo "  sudo trailarr logs 100"
    echo ""
}

# Function to start Trailarr
start_service() {
    check_root
    check_installation
    
    show_message "$BLUE" "Starting Trailarr service..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        show_message "$YELLOW" "Trailarr is already running."
    else
        systemctl start "$SERVICE_NAME"
        sleep 2
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            show_message "$GREEN" "Trailarr service started successfully!"
            show_message "$BLUE" "You can check the status with: trailarr status"
        else
            show_message "$RED" "Failed to start Trailarr service."
            show_message "$YELLOW" "Check the logs with: trailarr logs"
            exit 1
        fi
    fi
}

# Function to stop Trailarr
stop_service() {
    check_root
    check_installation
    
    show_message "$BLUE" "Stopping Trailarr service..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        show_message "$GREEN" "Trailarr service stopped successfully!"
    else
        show_message "$YELLOW" "Trailarr service is already stopped."
    fi
}

# Function to restart Trailarr
restart_service() {
    check_root
    check_installation
    
    show_message "$BLUE" "Restarting Trailarr service..."
    
    systemctl restart "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        show_message "$GREEN" "Trailarr service restarted successfully!"
    else
        show_message "$RED" "Failed to restart Trailarr service."
        show_message "$YELLOW" "Check the logs with: trailarr logs"
        exit 1
    fi
}

# Function to show service status
show_status() {
    check_installation
    
    echo "Trailarr Service Status:"
    echo "========================"
    systemctl status "$SERVICE_NAME" --no-pager
}

# Function to show logs
show_logs() {
    lines_count=$1
    check_installation
    if [ -z "$lines_count" ]; then
        lines_count=50
    fi

    echo "Trailarr Service Logs (last $lines_count lines):"
    echo "======================================="
    journalctl -u "$SERVICE_NAME" -n "$lines_count" --no-pager
}

# Function to update Trailarr
update_service() {
    check_root
    check_installation
    
    show_message "$BLUE" "Updating Trailarr to the latest version..."
    show_message "$YELLOW" "This will preserve your configuration and database."
    
    # Stop the service
    show_message "$BLUE" "Stopping Trailarr service..."
    systemctl stop "$SERVICE_NAME" || true
    
    # Create backup of current installation (excluding data directory)
    BACKUP_DIR="/tmp/trailarr_backup_$(date +%Y%m%d_%H%M%S)"
    show_message "$BLUE" "Creating backup at $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup only the application files, not user data
    cp -r "$INSTALL_DIR/backend" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$INSTALL_DIR/frontend-build" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$INSTALL_DIR/assets" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$INSTALL_DIR/scripts" "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup user data separately (configuration and database)
    DATA_BACKUP_DIR="/var/lib/trailarr/backups/update_$(date +%Y%m%d_%H%M%S)"
    show_message "$BLUE" "Creating user data backup at $DATA_BACKUP_DIR..."
    mkdir -p "$DATA_BACKUP_DIR"
    cp -r "/var/lib/trailarr/.env" "$DATA_BACKUP_DIR/" 2>/dev/null || true
    cp -r "/var/lib/trailarr/trailarr.db" "$DATA_BACKUP_DIR/" 2>/dev/null || true
    cp -r "/var/lib/trailarr/logs" "$DATA_BACKUP_DIR/" 2>/dev/null || true
    chown -R trailarr:trailarr "$DATA_BACKUP_DIR"
    
    # Download the latest release files instead of running the installer
    show_message "$BLUE" "Downloading latest Trailarr release..."
    TEMP_DIR="/tmp/trailarr_update_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$TEMP_DIR"
    
    # Download the latest release archive
    if ! curl -L -o "$TEMP_DIR/trailarr-latest.tar.gz" "https://github.com/$GITHUB_REPO/archive/refs/heads/main.tar.gz"; then
        show_message "$RED" "Failed to download latest release."
        show_message "$YELLOW" "Backup available at: $BACKUP_DIR"
        exit 1
    fi
    
    # Extract the release
    show_message "$BLUE" "Extracting release files..."
    cd "$TEMP_DIR"
    if ! tar -xzf "trailarr-latest.tar.gz"; then
        show_message "$RED" "Failed to extract release files."
        show_message "$YELLOW" "Backup available at: $BACKUP_DIR"
        exit 1
    fi
    
    # Find the extracted directory
    EXTRACT_DIR=$(find "$TEMP_DIR" -name "trailarr-main" -type d | head -1)
    if [ -z "$EXTRACT_DIR" ]; then
        show_message "$RED" "Failed to find extracted release directory."
        show_message "$YELLOW" "Backup available at: $BACKUP_DIR"
        exit 1
    fi
    
    # Update application files only (preserve user data)
    show_message "$BLUE" "Updating application files..."
    
    # Update backend
    if [ -d "$EXTRACT_DIR/backend" ]; then
        rm -rf "$INSTALL_DIR/backend"
        cp -r "$EXTRACT_DIR/backend" "$INSTALL_DIR/"
    fi
    
    # Update frontend
    if [ -d "$EXTRACT_DIR/frontend-build" ]; then
        rm -rf "$INSTALL_DIR/frontend-build"
        cp -r "$EXTRACT_DIR/frontend-build" "$INSTALL_DIR/"
    fi
    
    # Update assets
    if [ -d "$EXTRACT_DIR/assets" ]; then
        rm -rf "$INSTALL_DIR/assets"
        cp -r "$EXTRACT_DIR/assets" "$INSTALL_DIR/"
    fi
    
    # Update scripts
    if [ -d "$EXTRACT_DIR/scripts" ]; then
        rm -rf "$INSTALL_DIR/scripts"
        cp -r "$EXTRACT_DIR/scripts" "$INSTALL_DIR/"
    fi
    
    # Set proper ownership
    chown -R trailarr:trailarr "$INSTALL_DIR"
    
    # Update Python dependencies with uv sync
    show_message "$BLUE" "Updating Python dependencies..."
    cd "$INSTALL_DIR/backend"
    if [ -f "$INSTALL_DIR/.local/bin/uv" ]; then
        UV_CMD="$INSTALL_DIR/.local/bin/uv"
    else
        UV_CMD="uv"
    fi
    
    if sudo -u trailarr $UV_CMD sync --no-cache-dir; then
        show_message "$GREEN" "Dependencies updated successfully"
    else
        show_message "$YELLOW" "Failed to update dependencies, but application files updated"
    fi
    
    # Update CLI script
    if [ -f "$INSTALL_DIR/scripts/baremetal/trailarr_cli.sh" ]; then
        cp "$INSTALL_DIR/scripts/baremetal/trailarr_cli.sh" /usr/local/bin/trailarr
        chmod +x /usr/local/bin/trailarr
    fi
    
    # Clean up temporary files
    rm -rf "$TEMP_DIR"
    rm -rf "$BACKUP_DIR"
    
    show_message "$GREEN" "Trailarr updated successfully!"
    show_message "$GREEN" "Your configuration and database have been preserved."
    show_message "$BLUE" "User data backup created at: $DATA_BACKUP_DIR"
    
    # Start the service
    show_message "$BLUE" "Starting Trailarr service..."
    systemctl start "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        show_message "$GREEN" "Trailarr service started successfully!"
        show_message "$BLUE" "Update completed successfully!"
    else
        show_message "$YELLOW" "Update completed but service failed to start. Check logs with:"
        show_message "$YELLOW" "  sudo journalctl -u trailarr -f"
    fi
}

# Function to uninstall Trailarr
uninstall_service() {
    check_root
    
    echo "WARNING: This will completely remove Trailarr and all its data!"
    echo "This action cannot be undone."
    echo ""
    read -p "Are you sure you want to uninstall Trailarr? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        show_message "$YELLOW" "Uninstall cancelled."
        exit 0
    fi
    
    show_message "$BLUE" "Uninstalling Trailarr..."
    
    # Stop and disable service
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        show_message "$BLUE" "Stopping Trailarr service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        show_message "$BLUE" "Disabling Trailarr service..."
        systemctl disable "$SERVICE_NAME"
    fi
    
    # Remove service file
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        show_message "$BLUE" "Removing systemd service file..."
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
    fi
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        show_message "$BLUE" "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Remove trailarr user
    if id "trailarr" &>/dev/null; then
        show_message "$BLUE" "Removing trailarr user..."
        userdel -r trailarr 2>/dev/null || true
    fi
    
    # Remove this script
    if [ -f "/usr/local/bin/trailarr" ]; then
        rm -f "/usr/local/bin/trailarr"
    fi
    
    show_message "$GREEN" "Trailarr has been completely uninstalled."
}

# Main script logic
case "${1:-}" in
    "run"|"start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        show_status
        ;;
    "logs")
        # $2 is the optional number argument
        num="${2:-50}"  # If $2 is not set, num will be 50
        show_logs "$num"
        ;;
    "update")
        update_service
        ;;
    "uninstall")
        uninstall_service
        ;;
    "help"|"-h"|"--help"|"")
        show_usage
        ;;
    *)
        show_message "$RED" "Error: Unknown command '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac