#!/bin/bash

# Interactive Configuration for Trailarr Bare Metal Installation
# Prompts user for application settings and GPU preferences

set -e

# Source the common functions - first try baremetal logging, fallback to box_echo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/logging.sh" ]; then
    source "$SCRIPT_DIR/logging.sh"
    # If we're in a sub-script, we need to reuse the existing log file
    if [ -z "$INSTALL_LOG_FILE" ]; then
        INSTALL_LOG_FILE="/tmp/trailarr_install.log"
        export INSTALL_LOG_FILE
    fi
else
    source "$SCRIPT_DIR/../box_echo.sh"
    # Define print_message and start_message/end_message for compatibility
    print_message() { echo -e "$1$2\033[0m"; }
    start_message() { echo -e "$1$2\033[0m"; }
    end_message() { echo -e "$1$2\033[0m"; }
    log_to_file() { echo "$1"; }
    update_env_var() { 
        local var_name="$1"
        local var_value="$2"
        local env_file="$3"
        touch "$env_file"
        grep -v "^${var_name}=" "$env_file" > "${env_file}.tmp" 2>/dev/null || touch "${env_file}.tmp"
        echo "${var_name}=${var_value}" >> "${env_file}.tmp"
        mv "${env_file}.tmp" "$env_file"
    }
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
    print_message "$BLUE" "Configuring basic application settings"
    
    # Monitor interval
    local monitor_msg="Monitor Interval Configuration\n
How often should Trailarr check for new content?
  - Minimum is 10 minutes
  - This determines how frequently the app scans for new movies/shows
  - Shorter intervals = more responsive but higher system load
  - Longer intervals = less system load but slower to detect new content

Common values:
  - 60 (1 hour, default) [recommended]
  - 120 (2 hours)
  - 180 (3 hours)
  - 360 (6 hours)

"
    show_temp_status "$BLUE" "$monitor_msg"
    
    while true; do
        read -rp "Enter monitor interval in minutes [$DEFAULT_MONITOR_INTERVAL]: " monitor_interval
        monitor_interval=${monitor_interval:-$DEFAULT_MONITOR_INTERVAL}
        
        if [[ "$monitor_interval" =~ ^[0-9]+$ ]] && [ "$monitor_interval" -gt 9 ]; then
            export MONITOR_INTERVAL="$monitor_interval"
            show_status "$GREEN" "✓ Monitor interval set to $monitor_interval minutes"
            break
        else
            echo "Please enter a valid number greater than 10"
        fi
    done
    
    log_to_file "Monitor interval set to $monitor_interval minutes"
    
    # Wait for media
    local wait_for_media_msg="Wait for Media Configuration\n
Should Trailarr wait for media files to be available before downloading trailers?
  - Yes: Wait until movie/show files exist before downloading trailers (recommended)
  - No: Download trailers immediately when items are added to Radarr/Sonarr
"
    show_temp_status "$BLUE" "$wait_for_media_msg"
    
    while true; do
        read -rp "Wait for media files before downloading trailers? [Y/n]: " wait_choice
        wait_choice=${wait_choice:-Y}
        
        case "$wait_choice" in
            [Yy]|[Yy][Ee][Ss])
                export WAIT_FOR_MEDIA="true"
                show_status "$GREEN" "✓ Will wait for media files before downloading trailers"
                log_to_file "Will wait for media files before downloading trailers"
                break
                ;;
            [Nn]|[Nn][Oo])
                export WAIT_FOR_MEDIA="false"
                show_status "$GREEN" "✓ Will download trailers immediately when items are added"
                log_to_file "Will download trailers immediately when items are added"
                break
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # Port configuration
    show_temp_status "$BLUE" "Port Configuration"
    while true; do
        read -rp "Web interface port [$DEFAULT_PORT]: " port
        port=${port:-$DEFAULT_PORT}
        
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt 1023 ] && [ "$port" -lt 65536 ]; then
            export APP_PORT="$port"
            show_status "$GREEN" "✓ Web interface will be available on port $port"
            log_to_file "Web interface will be available on port $port"
            break
        else
            echo "Please enter a valid port number (1024-65535)"
        fi
    done
    
    show_status "$GREEN" "✓ Basic configuration complete"
}

# Function to configure GPU settings
configure_gpu_settings() {
    # Source GPU detection results if available
    if [ -f "/tmp/gpu_detection_results" ]; then
        source "/tmp/gpu_detection_results"
    fi
    
    print_message "$BLUE" "Configuring GPU settings"
    
    if [ ${#AVAILABLE_GPUS[@]} -eq 0 ]; then
        log_to_file "No supported GPUs detected. Hardware acceleration not enabled."
        export ENABLE_HWACCEL="false"
        export HWACCEL_TYPE="none"
        end_message "$YELLOW" "! No supported GPUs detected - hardware acceleration disabled"
        return 0
    fi

    local gpu_selection_msg="GPU Hardware Acceleration Configuration\n
Detected GPUs: ${DETECTED_GPUS[*]}\n
Hardware acceleration can significantly improve video processing performance
but may require additional system setup and drivers.
"
    show_temp_status "$BLUE" "$gpu_selection_msg"
    
    # Ask if user wants to enable hardware acceleration
    while true; do
        read -rp "Enable GPU hardware acceleration? [Y/n]: " hwaccel_choice
        hwaccel_choice=${hwaccel_choice:-Y}
        
        case "$hwaccel_choice" in
            [Yy]|[Yy][Ee][Ss])
                export ENABLE_HWACCEL="true"
                show_status "$GREEN" "✓ Hardware acceleration enabled"
                break
                ;;
            [Nn]|[Nn][Oo])
                export ENABLE_HWACCEL="false"
                export HWACCEL_TYPE="none"
                log_to_file "Hardware acceleration disabled by user choice"
                show_status "$GREEN" "✓ Hardware acceleration disabled"
                return 0
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # If multiple GPUs are available, ask user to choose
    if [ ${#AVAILABLE_GPUS[@]} -gt 1 ]; then
        local gpu_selection_choice_msg="GPU Selection:\n
Multiple GPUs detected. Trailarr can only use one GPU for hardware acceleration.
Please select which GPU to use:
"

        for i in "${!AVAILABLE_GPUS[@]}"; do
            gpu_selection_choice_msg="${gpu_selection_choice_msg}\n  $((i+1)). ${DETECTED_GPUS[$i]}"
        done
        show_temp_status "$BLUE" "$gpu_selection_choice_msg"
        
        while true; do
            read -rp "Select GPU (1-${#AVAILABLE_GPUS[@]}): " gpu_choice
            
            if [[ "$gpu_choice" =~ ^[0-9]+$ ]] && [ "$gpu_choice" -ge 1 ] && [ "$gpu_choice" -le ${#AVAILABLE_GPUS[@]} ]; then
                selected_index=$((gpu_choice - 1))
                export HWACCEL_TYPE="${AVAILABLE_GPUS[$selected_index]}"
                show_status "$GREEN" "✓ Selected ${DETECTED_GPUS[$selected_index]} for hardware acceleration"
                log_to_file "Selected ${DETECTED_GPUS[$selected_index]} for hardware acceleration"
                break
            else
                echo "Please enter a number between 1 and ${#AVAILABLE_GPUS[@]}"
            fi
        done
    else
        # Only one GPU available
        export HWACCEL_TYPE="${AVAILABLE_GPUS[0]}"
        show_status "$GREEN" "✓ Using ${DETECTED_GPUS[0]} for hardware acceleration"
        log_to_file "Using ${DETECTED_GPUS[0]} for hardware acceleration"
    fi
    
    # Provide driver installation instructions based on detected GPUs
    if [ "$ENABLE_HWACCEL" = "true" ]; then
        show_temp_status "$BLUE" "Hardware Acceleration Setup Instructions"
        case "$HWACCEL_TYPE" in
            "nvidia")
                echo "NVIDIA GPU selected. Ensure NVIDIA drivers are installed:"
                echo "  sudo apt update && sudo apt install -y nvidia-driver-535"
                echo "  (Reboot required after driver installation)"
                ;;
            "intel")
                echo "Intel GPU selected. Ensure VAAPI drivers are installed:"
                echo "  sudo apt update && sudo apt install -y intel-media-va-driver i965-va-driver vainfo"
                ;;
            "amd")
                echo "AMD GPU selected. Ensure VAAPI drivers are installed:"
                echo "  sudo apt update && sudo apt install -y mesa-va-drivers vainfo"
                ;;
        esac
        echo ""
        echo "Note: After installing drivers, restart the Trailarr service to use hardware acceleration"
    fi
    
    show_status "$GREEN" "✓ GPU configuration complete"
}

# Function to write configuration to file
write_configuration() {    
    start_message "$BLUE" "Writing configuration to file"
    
    # Ensure data directory exists
    mkdir -p "$DATA_DIR"
    
    # Create .env file with configuration
    cat > "$CONFIG_FILE" << EOF
# Trailarr Bare Metal Configuration
# Generated on $(date)

# Application Settings
APP_PORT=${APP_PORT:-7889}
APP_DATA_DIR=$DATA_DIR
MONITOR_INTERVAL=${MONITOR_INTERVAL:-60}
WAIT_FOR_MEDIA=${WAIT_FOR_MEDIA:-true}

# Hardware Acceleration
ENABLE_HWACCEL=${ENABLE_HWACCEL:-false}
HWACCEL_TYPE=${HWACCEL_TYPE:-none}

# Installation Mode
INSTALLATION_MODE=baremetal

# Runtime Environment
TZ=${TZ:-UTC}
PYTHONPATH=/opt/trailarr/backend
EOF
    
    log_to_file "Configuration written to $CONFIG_FILE"
    end_message "$GREEN" "✓ Configuration written to $CONFIG_FILE"
}

# Function to display configuration summary
display_summary() {
    # print_message "$BLUE" "Displaying configuration summary..."
    
    echo ""
    echo "Configuration Summary:"
    echo "======================================"
    echo "Application Port: ${APP_PORT}"
    echo "Data Directory: $DATA_DIR"
    echo "Monitor Interval: ${MONITOR_INTERVAL} minutes"
    echo "Wait for Media: ${WAIT_FOR_MEDIA}"
    echo "Hardware Acceleration: ${ENABLE_HWACCEL}"
    if [ "$ENABLE_HWACCEL" = "true" ]; then
        echo "GPU Type: ${HWACCEL_TYPE}"
    fi
    echo "Installation Mode: baremetal"
    echo "======================================"
    
    echo ""
    echo "After installation completes, you can:"
    echo "  - Start the service: sudo systemctl start trailarr"
    echo "  - Enable auto-start: sudo systemctl enable trailarr"
    echo "  - View logs: sudo journalctl -u trailarr -f"
    echo "  - Access web interface: http://localhost:${APP_PORT}"
    echo ""
    
    # end_message "$GREEN" "✓ Configuration summary displayed"
}

# Main function
main() {
    start_message "$BLUE" "Starting interactive configuration"
    
    # Create install directory if it doesn't exist
    sudo mkdir -p "/opt/trailarr"
    # Create data directory if it doesn't exist
    sudo mkdir -p "$DATA_DIR"
    
    end_message "$BLUE" "Interactive Configuration Setup"
    echo ""
    echo "Starting interactive configuration for Trailarr..."
    echo ""
        
    # Prompt for basic configuration
    prompt_basic_config
    
    # Configure GPU settings
    configure_gpu_settings
    
    # Write configuration
    write_configuration
    
    # Display summary
    display_summary
    
    show_status "$GREEN" "✓ Interactive configuration complete"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
