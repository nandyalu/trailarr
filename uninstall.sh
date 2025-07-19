#!/bin/bash

# Trailarr Bare Metal Uninstallation Script
# This script removes Trailarr from bare metal installations

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
        print_message $RED "This script should not be run as root."
        print_message $YELLOW "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to stop and disable service
stop_service() {
    print_message $BLUE "Stopping Trailarr service..."
    
    if systemctl is-active --quiet trailarr; then
        sudo systemctl stop trailarr
        print_message $GREEN "✓ Trailarr service stopped"
    else
        print_message $YELLOW "! Trailarr service is not running"
    fi
    
    if systemctl is-enabled --quiet trailarr; then
        sudo systemctl disable trailarr
        print_message $GREEN "✓ Trailarr service disabled"
    else
        print_message $YELLOW "! Trailarr service is not enabled"
    fi
    
    sudo systemctl daemon-reload
}

# Function to remove systemd service
remove_service() {
    print_message $BLUE "Removing systemd service..."
    
    if [ -f /etc/systemd/system/trailarr.service ]; then
        sudo rm /etc/systemd/system/trailarr.service
        sudo systemctl daemon-reload
        print_message $GREEN "✓ Systemd service removed"
    else
        print_message $YELLOW "! Systemd service file not found"
    fi
}

# Function to remove application files
remove_application() {
    print_message $BLUE "Removing application files..."
    
    if [ -d /opt/trailarr ]; then
        sudo rm -rf /opt/trailarr
        print_message $GREEN "✓ Application files removed from /opt/trailarr"
    else
        print_message $YELLOW "! Application directory /opt/trailarr not found"
    fi
}

# Function to remove user and data (optional)
remove_user_and_data() {
    local remove_data=$1
    
    print_message $BLUE "Removing trailarr user..."
    
    if id "trailarr" &>/dev/null; then
        sudo userdel trailarr
        print_message $GREEN "✓ trailarr user removed"
    else
        print_message $YELLOW "! trailarr user not found"
    fi
    
    if [ "$remove_data" = "yes" ]; then
        print_message $BLUE "Removing data directories..."
        
        if [ -d /var/lib/trailarr ]; then
            sudo rm -rf /var/lib/trailarr
            print_message $GREEN "✓ Data directory removed: /var/lib/trailarr"
        fi
        
        if [ -d /var/log/trailarr ]; then
            sudo rm -rf /var/log/trailarr
            print_message $GREEN "✓ Log directory removed: /var/log/trailarr"
        fi
    else
        print_message $YELLOW "! Data directories preserved:"
        print_message $YELLOW "  /var/lib/trailarr (configuration and database)"
        print_message $YELLOW "  /var/log/trailarr (logs)"
    fi
}

# Main uninstallation function
main() {
    print_message $GREEN "=== Trailarr Bare Metal Uninstallation ==="
    print_message $RED "This will remove Trailarr from your system"
    echo
    
    check_root
    
    # Ask for confirmation
    read -p "Do you want to continue with the uninstallation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message $YELLOW "Uninstallation cancelled"
        exit 0
    fi
    
    # Ask about data removal
    echo
    read -p "Do you also want to remove configuration and data files? (y/N): " -n 1 -r
    echo
    remove_data="no"
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        remove_data="yes"
        print_message $RED "WARNING: This will permanently delete your Trailarr database and configuration!"
        read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            remove_data="no"
            print_message $YELLOW "Data files will be preserved"
        fi
    fi
    
    stop_service
    remove_service
    remove_application
    remove_user_and_data "$remove_data"
    
    echo
    print_message $GREEN "=== Uninstallation Complete! ==="
    
    if [ "$remove_data" = "no" ]; then
        print_message $YELLOW "Your configuration and data files have been preserved:"
        print_message $YELLOW "  /var/lib/trailarr/"
        print_message $YELLOW "  /var/log/trailarr/"
        print_message $BLUE "You can reinstall Trailarr later and your data will be restored."
    fi
    
    print_message $BLUE "Thank you for using Trailarr!"
}

# Run main function
main "$@"