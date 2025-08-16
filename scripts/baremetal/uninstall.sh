#!/bin/bash

# Trailarr Bare Metal Uninstallation Script
# This script removes Trailarr from bare metal installations with data preservation options

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
DATA_DIR="/var/lib/trailarr"
LOG_DIR="/var/log/trailarr"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try to source logging functions if available, otherwise use simple echo
if [ -f "$SCRIPT_DIR/logging.sh" ]; then
    source "$SCRIPT_DIR/logging.sh"
    INSTALL_LOG_FILE="/tmp/trailarr_uninstall.log"
    export INSTALL_LOG_FILE
    init_logging
else
    # Fallback logging functions
    RED=1
    GREEN=2  
    YELLOW=3
    BLUE=4
    show_message() {
        local color=""
        local msg=""
        if [ "$#" -eq 1 ]; then
            msg="$1"
        else
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                color="$1"
                msg="$2"
            else
                msg="$1"
            fi
        fi
        echo "$msg"
    }
    start_message() { echo "$1"; }
    end_message() { echo "$1"; }
    show_temp_message() { echo "$2"; }
fi

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
    show_message $YELLOW "This will remove Trailarr from your system"
    echo ""
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        show_message $RED "This script should not be run as root."
        show_message $YELLOW "Please run as a regular user with sudo privileges."
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
                show_message $GREEN "✓ Data will be preserved"
                break
                ;;
            [Nn]|[Nn][Oo])
                export PRESERVE_DATA="false"
                show_message $YELLOW "⚠ Data will be removed permanently"
                
                while true; do
                    read -rp "Are you sure you want to delete all data? [y/N]: " confirm_delete
                    confirm_delete=${confirm_delete:-N}
                    
                    case "$confirm_delete" in
                        [Yy]|[Yy][Ee][Ss])
                            break 2
                            ;;
                        [Nn]|[Nn][Oo])
                            export PRESERVE_DATA="true"
                            show_message $GREEN "✓ Data will be preserved"
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
    
    start_message "Creating data backup"
    
    BACKUP_DIR="$HOME/trailarr_backup_$(date +%Y%m%d_%H%M%S)"
    show_temp_message "Creating backup directory"
    mkdir -p "$BACKUP_DIR"
    
    # Backup data directory
    if [ -d "$DATA_DIR" ]; then
        show_temp_message "Backing up data directory"
        sudo cp -r "$DATA_DIR" "$BACKUP_DIR/data"
        sudo chown -R "$USER:$USER" "$BACKUP_DIR/data"
    fi
    
    # Backup configuration
    if [ -f "$INSTALL_DIR/.env" ]; then
        show_temp_message "Backing up configuration"
        sudo cp "$INSTALL_DIR/.env" "$BACKUP_DIR/config.env"
        sudo chown "$USER:$USER" "$BACKUP_DIR/config.env"
    fi
    
    show_message $GREEN "✓ Data backed up to: $BACKUP_DIR"
    echo "You can restore this data during a future installation"
    end_message "Data backup complete"
}

# Function to stop and disable service
stop_service() {
    start_message "Stopping Trailarr service"
    
    if systemctl is-active --quiet trailarr 2>/dev/null; then
        show_temp_message "Stopping trailarr service"
        sudo systemctl stop trailarr
        show_message $GREEN "✓ Trailarr service stopped"
    else
        show_message $YELLOW "! Trailarr service is not running"
    fi
    
    if systemctl is-enabled --quiet trailarr 2>/dev/null; then
        show_temp_message "Disabling trailarr service"
        sudo systemctl disable trailarr
        show_message $GREEN "✓ Trailarr service disabled"
    else
        show_message $YELLOW "! Trailarr service is not enabled"
    fi
    
    end_message "Service stopped and disabled"
}

# Function to remove systemd service
remove_systemd_service() {
    start_message "Removing systemd service"
    
    if [ -f "/etc/systemd/system/trailarr.service" ]; then
        show_temp_message "Removing service file"
        sudo rm -f "/etc/systemd/system/trailarr.service"
        show_temp_message "Reloading systemd daemon"
        sudo systemctl daemon-reload
        show_message $GREEN "✓ Systemd service removed"
    else
        show_message $YELLOW "! Systemd service file not found"
    fi
    
    end_message "Systemd service cleanup complete"
}

# Function to remove application files
remove_application() {
    start_message "Removing application files"
    
    if [ -d "$INSTALL_DIR" ]; then
        show_temp_message "Removing installation directory"
        sudo rm -rf "$INSTALL_DIR"
        show_message $GREEN "✓ Application files removed"
    else
        show_message $YELLOW "! Application directory not found"
    fi
    
    end_message "Application files removed"
}

# Function to remove data
remove_data() {
    if [ "$PRESERVE_DATA" = "true" ]; then
        show_message $BLUE "Preserving data directory: $DATA_DIR"
        return 0
    fi
    
    start_message "Removing data files"
    
    if [ -d "$DATA_DIR" ]; then
        show_temp_message "Removing data directory"
        sudo rm -rf "$DATA_DIR"
        show_message $GREEN "✓ Data directory removed"
    else
        show_message $YELLOW "! Data directory not found"
    fi
    
    if [ -d "$LOG_DIR" ]; then
        show_temp_message "Removing log directory"
        sudo rm -rf "$LOG_DIR"
        show_message $GREEN "✓ Log directory removed"
    else
        show_message $YELLOW "! Log directory not found"
    fi
    
    end_message "Data removal complete"
}

# Function to remove user
remove_user() {
    start_message "Removing trailarr user"
    
    if id "trailarr" &>/dev/null; then
        show_temp_message "Removing trailarr user account"
        if sudo userdel trailarr 2>/dev/null; then
            show_message $GREEN "✓ Trailarr user removed"
        else
            show_message $YELLOW "! Could not remove trailarr user (may have active processes)"
        fi
    else
        show_message $YELLOW "! Trailarr user does not exist"
    fi
    
    end_message "User cleanup complete"
}

# Function to clean up system packages (optional)
cleanup_packages() {
    echo ""
    while true; do
        read -rp "Remove Python packages installed specifically for Trailarr? [y/N]: " remove_packages
        remove_packages=${remove_packages:-N}
        
        case "$remove_packages" in
            [Yy]|[Yy][Ee][Ss])
                show_message $BLUE "Note: This will only remove packages if they were installed in Trailarr's directory"
                show_message $BLUE "System Python packages will not be affected"
                break
                ;;
            [Nn]|[Nn][Oo])
                show_message $BLUE "Keeping system packages intact"
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
    show_message $GREEN ""
    show_message $GREEN "🗑️  Trailarr uninstallation completed"
    show_message $GREEN ""
    
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
        show_message $YELLOW "Trailarr does not appear to be installed on this system"
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
