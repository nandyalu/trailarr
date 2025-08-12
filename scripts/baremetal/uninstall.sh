#!/bin/bash

# Trailarr Bare Metal Uninstallation Script
# This script removes Trailarr from bare metal installations with data preservation options

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
DATA_DIR="/var/lib/trailarr"
LOG_DIR="/var/log/trailarr"

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

# Function to display uninstall banner
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

                     Bare Metal Uninstall Script          
                                             
EOF
    print_message $YELLOW "This will remove Trailarr from your system"
    echo ""
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_message $RED "This script should not be run as root."
        print_message $YELLOW "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to prompt for data preservation
prompt_data_preservation() {
    echo "Data Preservation Options:"
    echo "  Your data is stored in: $DATA_DIR"
    echo "  This includes:"
    echo "    - Database with movie/show information"
    echo "    - Downloaded trailers"
    echo "    - Configuration settings"
    echo "    - Log files"
    echo ""
    
    while true; do
        read -rp "Do you want to keep your data for future reinstalls? [Y/n]: " keep_data
        keep_data=${keep_data:-Y}
        
        case "$keep_data" in
            [Yy]|[Yy][Ee][Ss])
                export PRESERVE_DATA="true"
                print_message $GREEN "✓ Data will be preserved"
                break
                ;;
            [Nn]|[Nn][Oo])
                export PRESERVE_DATA="false"
                print_message $YELLOW "⚠ Data will be removed permanently"
                
                while true; do
                    read -rp "Are you sure you want to delete all data? [y/N]: " confirm_delete
                    confirm_delete=${confirm_delete:-N}
                    
                    case "$confirm_delete" in
                        [Yy]|[Yy][Ee][Ss])
                            break 2
                            ;;
                        [Nn]|[Nn][Oo])
                            export PRESERVE_DATA="true"
                            print_message $GREEN "✓ Data will be preserved"
                            break 2
                            ;;
                        *)
                            echo "Please enter Y or N"
                            ;;
                    esac
                done
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
}

# Function to create data backup
create_data_backup() {
    if [ "$PRESERVE_DATA" = "false" ]; then
        return 0
    fi
    
    print_message $BLUE "Creating data backup..."
    
    BACKUP_DIR="$HOME/trailarr_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup data directory
    if [ -d "$DATA_DIR" ]; then
        sudo cp -r "$DATA_DIR" "$BACKUP_DIR/data"
        sudo chown -R "$USER:$USER" "$BACKUP_DIR/data"
    fi
    
    # Backup configuration
    if [ -f "$INSTALL_DIR/.env" ]; then
        sudo cp "$INSTALL_DIR/.env" "$BACKUP_DIR/config.env"
        sudo chown "$USER:$USER" "$BACKUP_DIR/config.env"
    fi
    
    print_message $GREEN "✓ Data backed up to: $BACKUP_DIR"
    echo "You can restore this data during a future installation"
}

# Function to stop and disable service
stop_service() {
    print_message $BLUE "Stopping Trailarr service..."
    
    if systemctl is-active --quiet trailarr 2>/dev/null; then
        sudo systemctl stop trailarr
        print_message $GREEN "✓ Trailarr service stopped"
    else
        print_message $YELLOW "! Trailarr service is not running"
    fi
    
    if systemctl is-enabled --quiet trailarr 2>/dev/null; then
        sudo systemctl disable trailarr
        print_message $GREEN "✓ Trailarr service disabled"
    else
        print_message $YELLOW "! Trailarr service is not enabled"
    fi
}

# Function to remove systemd service
remove_systemd_service() {
    print_message $BLUE "Removing systemd service..."
    
    if [ -f "/etc/systemd/system/trailarr.service" ]; then
        sudo rm -f "/etc/systemd/system/trailarr.service"
        sudo systemctl daemon-reload
        print_message $GREEN "✓ Systemd service removed"
    else
        print_message $YELLOW "! Systemd service file not found"
    fi
}

# Function to remove application files
remove_application() {
    print_message $BLUE "Removing application files..."
    
    if [ -d "$INSTALL_DIR" ]; then
        sudo rm -rf "$INSTALL_DIR"
        print_message $GREEN "✓ Application files removed"
    else
        print_message $YELLOW "! Application directory not found"
    fi
}

# Function to remove data
remove_data() {
    if [ "$PRESERVE_DATA" = "true" ]; then
        print_message $BLUE "Preserving data directory: $DATA_DIR"
        return 0
    fi
    
    print_message $BLUE "Removing data files..."
    
    if [ -d "$DATA_DIR" ]; then
        sudo rm -rf "$DATA_DIR"
        print_message $GREEN "✓ Data directory removed"
    else
        print_message $YELLOW "! Data directory not found"
    fi
    
    if [ -d "$LOG_DIR" ]; then
        sudo rm -rf "$LOG_DIR"
        print_message $GREEN "✓ Log directory removed"
    else
        print_message $YELLOW "! Log directory not found"
    fi
}

# Function to remove user
remove_user() {
    print_message $BLUE "Removing trailarr user..."
    
    if id "trailarr" &>/dev/null; then
        sudo userdel trailarr 2>/dev/null || {
            print_message $YELLOW "! Could not remove trailarr user (may have active processes)"
        }
        print_message $GREEN "✓ Trailarr user removed"
    else
        print_message $YELLOW "! Trailarr user does not exist"
    fi
}

# Function to clean up system packages (optional)
cleanup_packages() {
    echo ""
    while true; do
        read -rp "Remove Python packages installed specifically for Trailarr? [y/N]: " remove_packages
        remove_packages=${remove_packages:-N}
        
        case "$remove_packages" in
            [Yy]|[Yy][Ee][Ss])
                print_message $BLUE "Note: This will only remove packages if they were installed in Trailarr's directory"
                print_message $BLUE "System Python packages will not be affected"
                break
                ;;
            [Nn]|[Nn][Oo])
                print_message $BLUE "Keeping system packages intact"
                break
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
}

# Function to display completion message
display_completion() {
    print_message $GREEN ""
    print_message $GREEN "🗑️  Trailarr uninstallation completed"
    print_message $GREEN ""
    
    if [ "$PRESERVE_DATA" = "true" ]; then
        echo "Data Preservation:"
        for backup_dir in "$HOME"/trailarr_backup_*; do
            if [ -d "$backup_dir" ]; then
                echo "  - Backup created in: $backup_dir"
                break  # Stop after the first match (optional)
            fi
        done

        if [ -d "$DATA_DIR" ]; then
            echo "  - Original data preserved in: $DATA_DIR"
        fi
        echo ""
        echo "To reinstall Trailarr with your existing data:"
        echo "  1. Run the installation script again"
        echo "  2. Your data will be automatically detected and preserved"
    else
        echo "All Trailarr data has been removed from the system."
    fi
    
    echo ""
    echo "Thank you for using Trailarr!"
    echo ""
}

# Main uninstallation function
main() {
    display_banner
    
    # Check if running as root
    check_root
    
    # Check if Trailarr is installed
    if [ ! -d "$INSTALL_DIR" ] && [ ! -f "/etc/systemd/system/trailarr.service" ]; then
        print_message $YELLOW "Trailarr does not appear to be installed on this system"
        exit 0
    fi
    
    # Prompt for data preservation
    prompt_data_preservation
    
    # Create backup if preserving data
    create_data_backup
    
    # Uninstallation steps
    stop_service
    remove_systemd_service
    remove_application
    remove_data
    remove_user
    cleanup_packages
    
    display_completion
}

# Run main uninstallation
main "$@"
