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
    echo "  logs       Show recent logs from Trailarr service"
    echo "  update     Update Trailarr to the latest version"
    echo "  uninstall  Uninstall Trailarr and its service"
    echo ""
    echo "Examples:"
    echo "  sudo trailarr run"
    echo "  sudo trailarr status"
    echo "  sudo trailarr logs"
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
    check_installation
    
    echo "Trailarr Service Logs (last 50 lines):"
    echo "======================================="
    journalctl -u "$SERVICE_NAME" -n 50 --no-pager
}

# Function to update Trailarr
update_service() {
    check_root
    check_installation
    
    show_message "$BLUE" "Updating Trailarr to the latest version..."
    
    # Stop the service
    show_message "$BLUE" "Stopping Trailarr service..."
    systemctl stop "$SERVICE_NAME" || true
    
    # Create backup of current installation
    BACKUP_DIR="/tmp/trailarr_backup_$(date +%Y%m%d_%H%M%S)"
    show_message "$BLUE" "Creating backup at $BACKUP_DIR..."
    cp -r "$INSTALL_DIR" "$BACKUP_DIR"
    
    # Download and run the installation script
    show_message "$BLUE" "Downloading latest installation script..."
    TEMP_SCRIPT="/tmp/trailarr_update_install.sh"
    
    if ! curl -L -o "$TEMP_SCRIPT" "https://raw.githubusercontent.com/$GITHUB_REPO/main/install.sh"; then
        show_message "$RED" "Failed to download installation script."
        show_message "$YELLOW" "Backup available at: $BACKUP_DIR"
        exit 1
    fi
    
    chmod +x "$TEMP_SCRIPT"
    
    show_message "$BLUE" "Running update installation..."
    if ! "$TEMP_SCRIPT"; then
        show_message "$RED" "Update failed! Restoring backup..."
        rm -rf "$INSTALL_DIR"
        mv "$BACKUP_DIR" "$INSTALL_DIR"
        systemctl start "$SERVICE_NAME"
        show_message "$RED" "Update failed and backup restored."
        exit 1
    fi
    
    # Clean up
    rm -f "$TEMP_SCRIPT"
    rm -rf "$BACKUP_DIR"
    
    show_message "$GREEN" "Trailarr updated successfully!"
    show_message "$BLUE" "Starting Trailarr service..."
    systemctl start "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        show_message "$GREEN" "Trailarr service started successfully!"
    else
        show_message "$YELLOW" "Update completed but service failed to start. Check logs."
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
        show_logs
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