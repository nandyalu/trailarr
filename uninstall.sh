#!/bin/bash

# Trailarr Bare Metal Uninstallation Bootstrap Script
# This script downloads the latest Trailarr release and runs the uninstaller

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
TEMP_DIR="/tmp/trailarr_uninstall"
UNINSTALL_SCRIPT="scripts/baremetal/uninstall.sh"

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
                                             
       Bare Metal Uninstaller               
                                             
EOF
    print_message $YELLOW "This script will download and run the Trailarr uninstaller"
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

# Function to check if Trailarr is installed
check_installation() {
    if [ ! -d "/opt/trailarr" ] && [ ! -f "/etc/systemd/system/trailarr.service" ]; then
        print_message $YELLOW "Trailarr does not appear to be installed on this system."
        echo ""
        echo "If you want to remove any remaining files manually:"
        echo "  sudo rm -rf /opt/trailarr"
        echo "  sudo rm -rf /var/lib/trailarr"  
        echo "  sudo rm -rf /var/log/trailarr"
        echo "  sudo rm -f /etc/systemd/system/trailarr.service"
        echo "  sudo userdel trailarr"
        echo ""
        exit 0
    fi
}

# Function to check dependencies
check_dependencies() {
    print_message $BLUE "Checking required dependencies..."
    
    # Check for required commands
    MISSING_DEPS=()
    
    for cmd in curl wget unzip; do
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
    print_message $BLUE "Downloading Trailarr uninstaller..."
    
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
    
    print_message $GREEN "✓ Uninstaller downloaded and extracted"
}

# Function to run uninstallation
run_uninstallation() {
    print_message $BLUE "Starting Trailarr uninstallation..."
    
    cd "$TEMP_DIR/$EXTRACT_DIR"
    
    # Check if uninstall script exists
    if [ ! -f "$UNINSTALL_SCRIPT" ]; then
        print_message $RED "Uninstall script not found: $UNINSTALL_SCRIPT"
        exit 1
    fi
    
    # Make uninstall script executable
    chmod +x "$UNINSTALL_SCRIPT"
    
    # Run the uninstallation
    bash "$UNINSTALL_SCRIPT"
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
    check_installation
    check_dependencies
    get_latest_version
    download_source
    run_uninstallation
    
    print_message $GREEN ""
    print_message $GREEN "🗑️ Trailarr uninstallation bootstrap completed!"
    print_message $GREEN ""
    echo "The uninstallation script has been downloaded and executed."
    echo "Please check the output above for any further instructions."
}

# Run main function
main "$@"

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