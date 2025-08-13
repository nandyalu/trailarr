#!/bin/bash

# Trailarr Bootstrap Installation Script
# This script downloads the latest release and runs the full installation
# Can be run standalone without any dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Simple logging function for bootstrap
print_message() {
    local color="$1"
    local message="$2"
    printf "${color}${message}${NC}\n"
}

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

                Bootstrap Installation Script

EOF
    print_message "$BLUE" "Downloading and installing Trailarr for maximum performance"
    print_message "$BLUE" "with native GPU hardware acceleration support"
    echo ""
}

# Function to check if running as root or not with sudo
check_root() {
    # Block direct root execution (not via sudo)
    if [[ $EUID -eq 0 && -z "$SUDO_USER" ]]; then
        print_message "$RED" "Do NOT run this script directly as root."
        print_message "$YELLOW" "Please run as a regular user with sudo: sudo bash bootstrap_install.sh"
        exit 1
    fi
    # Block non-sudo runs (must be run with sudo)
    if [[ $EUID -ne 0 || -z "$SUDO_USER" ]]; then
        print_message "$RED" "This script must be run with sudo."
        print_message "$YELLOW" "Please run: sudo bash bootstrap_install.sh"
        exit 1
    fi
}

# Function to check system requirements
check_requirements() {
    print_message "$BLUE" "Checking system requirements..."
    
    # Check for required commands
    local missing_commands=()
    for cmd in curl unzip tar wget; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        print_message "$RED" "Missing required commands: ${missing_commands[*]}"
        print_message "$YELLOW" "Please install them with: apt update && apt install -y ${missing_commands[*]}"
        exit 1
    fi
    
    # Check for Debian-based system
    if [[ ! -f /etc/debian_version ]]; then
        print_message "$RED" "This installer is designed for Debian-based systems only."
        print_message "$YELLOW" "Please check the documentation for alternative installation methods."
        exit 1
    fi
    
    print_message "$GREEN" "✓ System requirements met"
}

# Function to download latest release
download_latest_release() {
    print_message "$BLUE" "Downloading latest Trailarr release..."
    
    # Create temporary directory
    local temp_dir="/tmp/trailarr-bootstrap-$$"
    mkdir -p "$temp_dir"
    
    # Get the latest release info from GitHub API
    print_message "$BLUE" "Fetching latest release information..."
    local release_json
    if ! release_json=$(curl -s https://api.github.com/repos/nandyalu/trailarr/releases/latest); then
        print_message "$RED" "✗ Failed to fetch release information from GitHub"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    # Extract tag_name for version
    local app_version=$(echo "$release_json" | grep '"tag_name":' | head -n1 | cut -d '"' -f4)
    print_message "$GREEN" "→ Latest version: $app_version"
    
    # Extract the source code zip URL
    local src_archive_url=$(echo "$release_json" | grep "zipball_url" | head -n1 | cut -d '"' -f4)
    
    # Fallback to tar.gz if zip not found
    local archive_type="zip"
    local unpacker="unzip -q"
    if [[ -z "$src_archive_url" ]]; then
        src_archive_url=$(echo "$release_json" | grep "tarball_url" | head -n1 | cut -d '"' -f4)
        archive_type="tar.gz"
        unpacker="tar -xzf"
    fi
    
    print_message "$BLUE" "Downloading source archive..."
    
    # Download the source archive
    if ! curl -L -o "$temp_dir/trailarr-source.$archive_type" "$src_archive_url"; then
        print_message "$RED" "✗ Failed to download Trailarr source code"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    print_message "$BLUE" "Extracting source archive..."
    
    # Extract the downloaded archive
    if ! $unpacker "$temp_dir/trailarr-source.$archive_type" -d "$temp_dir/"; then
        print_message "$RED" "✗ Failed to extract Trailarr source code archive"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    # Find the extracted folder (should be the only directory inside temp_dir that's not the archive)
    local extracted_dir=$(find "$temp_dir" -mindepth 1 -maxdepth 1 -type d | head -n1)
    
    if [[ -z "$extracted_dir" ]]; then
        print_message "$RED" "✗ No extracted directory found"
        rm -rf "$temp_dir"
        exit 1
    fi
    
    print_message "$GREEN" "✓ Source code downloaded and extracted"
    
    # Store paths for later use
    export TRAILARR_SOURCE_DIR="$extracted_dir"
    export TRAILARR_TEMP_DIR="$temp_dir"
}

# Function to run the actual installation
run_installation() {
    print_message "$BLUE" "Starting Trailarr installation..."
    
    local install_script="$TRAILARR_SOURCE_DIR/scripts/baremetal/install.sh"
    
    if [[ ! -f "$install_script" ]]; then
        print_message "$RED" "✗ Installation script not found in downloaded source"
        print_message "$RED" "Expected: $install_script"
        cleanup_temp_files
        exit 1
    fi
    
    # Make sure the install script is executable
    chmod +x "$install_script"
    
    print_message "$GREEN" "✓ Running installation script..."
    echo ""
    
    # Run the installation script
    # Pass through any arguments that were passed to this bootstrap script
    if ! bash "$install_script" "$@"; then
        print_message "$RED" "✗ Installation failed"
        cleanup_temp_files
        exit 1
    fi
    
    cleanup_temp_files
    print_message "$GREEN" "✓ Trailarr installation completed successfully!"
}

# Function to clean up temporary files
cleanup_temp_files() {
    if [[ -n "$TRAILARR_TEMP_DIR" && -d "$TRAILARR_TEMP_DIR" ]]; then
        print_message "$BLUE" "Cleaning up temporary files..."
        rm -rf "$TRAILARR_TEMP_DIR"
    fi
}

# Trap to ensure cleanup happens even if script is interrupted
trap cleanup_temp_files EXIT

# Main execution
main() {
    display_banner
    check_root
    check_requirements
    download_latest_release
    run_installation "$@"
}

# Run main function with all passed arguments
main "$@"