#!/bin/bash

# Interactive Configuration for Trailarr Bare Metal Installation
# Prompts user for application settings and GPU preferences

set -e

# Source the common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logging.sh"

# If we're in a sub-script, we need to reuse the existing log file
if [ -z "$INSTALL_LOG_FILE" ]; then
    INSTALL_LOG_FILE="/tmp/trailarr_install.log"
    export INSTALL_LOG_FILE
fi

# Default values
DEFAULT_MONITOR_INTERVAL=60  # 1 hour in minutes
DEFAULT_WAIT_FOR_MEDIA="true"
DEFAULT_PORT=7889

# Configuration file
DATA_DIR="${APP_DATA_DIR:-/var/lib/trailarr}"
CONFIG_FILE="$DATA_DIR/.env"

# Function to prompt for configuration values
prompt_basic_config() {    
    # Monitor interval
    local msg="
Monitor Interval Configuration

How often should Trailarr check for new content?
    - Minimum is 10 minutes
    - This determines how frequently the app scans for new movies/shows
    - Shorter intervals = more responsive but higher system load

Common values:
    - 60 (1 hour, default) [recommended]
    - 120 (2 hours)
    - 180 (3 hours)
    - 360 (6 hours)

Enter monitor interval in minutes [$DEFAULT_MONITOR_INTERVAL]: 
    "
    
    
    while true; do
        read -rp "$msg" monitor_interval
        monitor_interval=${monitor_interval:-$DEFAULT_MONITOR_INTERVAL}
        
        if [[ "$monitor_interval" =~ ^[0-9]+$ ]] && [ "$monitor_interval" -gt 9 ]; then
            export MONITOR_INTERVAL="$monitor_interval"
            show_message $GREEN "Monitor interval set to '$monitor_interval' minutes"
            break
        else
            echo "Invalid value: '$monitor_interval'"
            echo "Please enter a valid number greater than 10"
        fi
    done
    
    log_to_file "Monitor interval set to $monitor_interval minutes"
    
    # Wait for media
    local msg="
Wait for Media Configuration

Should Trailarr wait for media files to be available before downloading trailers?
  - Yes: Wait until movie/show files exist before downloading trailers (recommended)
  - No: Download trailers immediately when items are added to Radarr/Sonarr

Wait for media files before downloading trailers? [Y/n]: 
"

    while true; do
        read -rp "$msg" wait_choice
        wait_choice=${wait_choice:-Y}
        
        case "$wait_choice" in
            [Yy]|[Yy][Ee][Ss])
                export WAIT_FOR_MEDIA="true"
                show_message $GREEN "Will wait for media files before downloading trailers"
                break
                ;;
            [Nn]|[Nn][Oo])
                export WAIT_FOR_MEDIA="false"
                show_message $GREEN "Will download trailers immediately when items are added"
                break
                ;;
            *)
                echo "Invalid choice: '$wait_choice'"
                echo "Please enter Y or N"
                ;;
        esac
    done

    # Port configuration
    local msg="
Port Configuration

Default is 7889
- You can change it to a different port as needed
- Make sure the port is not being used by another program

# To check if port is in use, run below commands
>>>    sudo netstat -tlnp | grep :7889
>>>>   sudo lsof -i :7889

Web interface port [$DEFAULT_PORT]: 
"

    while true; do
        read -rp "$msg" port
        port=${port:-$DEFAULT_PORT}
        
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt 1023 ] && [ "$port" -lt 65536 ]; then
            export APP_PORT="$port"
            show_message $GREEN "Web interface will port set to '$port'"
            break
        else
            echo "Invalid port: '$port'"
            echo "Please enter a valid port number (1024-65535)"
        fi
    done
    
}

# Function to write configuration to file
write_configuration() {        
    # Ensure data directory exists
    show_temp_message "Creating data directory for saving configuration"
    mkdir -p "$DATA_DIR"
    
    # Create .env file with configuration
    show_temp_message "Writing configuration file"
    update_env_var "APP_VERSION" "${APP_VERSION:-0.0.0}" "$DATA_DIR/.env"
    update_env_var "APP_DATA_DIR" "$DATA_DIR" "$DATA_DIR/.env"
    update_env_var "APP_PORT" "$APP_PORT" "$DATA_DIR/.env"
    update_env_var "INSTALLATION_MODE" "baremetal" "$DATA_DIR/.env"
    update_env_var "MONITOR_INTERVAL" "$MONITOR_INTERVAL" "$DATA_DIR/.env"
    update_env_var "PYTHONPATH" "/opt/trailarr/backend" "$DATA_DIR/.env"
    update_env_var "WAIT_FOR_MEDIA" "$WAIT_FOR_MEDIA" "$DATA_DIR/.env"
    update_env_var "GPU_AVAILABLE_NVIDIA" "${GPU_AVAILABLE_NVIDIA:-false}" "$DATA_DIR/.env"
    update_env_var "GPU_AVAILABLE_INTEL" "${GPU_AVAILABLE_INTEL:-false}" "$DATA_DIR/.env"
    update_env_var "GPU_AVAILABLE_AMD" "${GPU_AVAILABLE_AMD:-false}" "$DATA_DIR/.env"
    update_env_var "GPU_DEVICE_NVIDIA" "$GPU_DEVICE_NVIDIA" "$DATA_DIR/.env"
    update_env_var "GPU_DEVICE_INTEL" "$GPU_DEVICE_INTEL" "$DATA_DIR/.env"
    update_env_var "GPU_DEVICE_AMD" "$GPU_DEVICE_AMD" "$DATA_DIR/.env"
    TZ=$(timedatectl | grep "Time zone" | awk '{print $3}')
    update_env_var "TZ" "$TZ" "$DATA_DIR/.env"
    show_message $GREEN "Configuration written to '$CONFIG_FILE'"
}

# Function to display configuration summary
display_summary() {
    echo ""
    echo "Configuration Summary:"
    echo "======================================"
    echo "Application Port: ${APP_PORT}"
    echo "Data Directory: $DATA_DIR"
    echo "Monitor Interval: ${MONITOR_INTERVAL} minutes"
    echo "Wait for Media: ${WAIT_FOR_MEDIA}"
    echo "Installation Mode: baremetal"
    echo "======================================"
    
    echo ""
    echo "After installation completes, you can:"
    echo "  - Start the service: sudo systemctl start trailarr"
    echo "  - Enable auto-start: sudo systemctl enable trailarr"
    echo "  - View logs: sudo journalctl -u trailarr -f"
    echo "  - Access web interface: http://localhost:${APP_PORT}"
    echo ""
}

# Main function
main() {
    # Create install directory if it doesn't exist
    sudo mkdir -p "/opt/trailarr"
    # Create data directory if it doesn't exist
    sudo mkdir -p "$DATA_DIR"
    
    show_message ""
    show_message "Starting interactive configuration for Trailarr..."
    show_message ""
    
    # Prompt for basic configuration
    prompt_basic_config
    
    # Write configuration
    write_configuration
    
    # Display summary
    display_summary
}

# Run main function
main "$@"
