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
    start_message "Configuring basic application settings"
    
    # Monitor interval
    show_message ""
    show_message "Monitor Interval Configuration"
    show_message ""
    show_message "How often should Trailarr check for new content?"
    show_message "  - Minimum is 10 minutes"
    show_message "  - This determines how frequently the app scans for new movies/shows"
    show_message "  - Shorter intervals = more responsive but higher system load"
    show_message ""
    show_message "Common values:"
    show_message "  - 60 (1 hour, default) [recommended]"
    show_message "  - 120 (2 hours)"
    show_message "  - 180 (3 hours)"
    show_message "  - 360 (6 hours)"
    show_message ""
    
    while true; do
        read -rp "Enter monitor interval in minutes [$DEFAULT_MONITOR_INTERVAL]: " monitor_interval
        monitor_interval=${monitor_interval:-$DEFAULT_MONITOR_INTERVAL}
        
        if [[ "$monitor_interval" =~ ^[0-9]+$ ]] && [ "$monitor_interval" -gt 9 ]; then
            export MONITOR_INTERVAL="$monitor_interval"
            show_message $GREEN "✓ Monitor interval set to $monitor_interval minutes"
            break
        else
            echo "Please enter a valid number greater than 10"
        fi
    done
    
    log_to_file "Monitor interval set to $monitor_interval minutes"
    
    # Wait for media
    show_message ""
    show_message "Wait for Media Configuration"
    show_message ""
    show_message "Should Trailarr wait for media files to be available before downloading trailers?"
    show_message "  - Yes: Wait until movie/show files exist before downloading trailers (recommended)"
    show_message "  - No: Download trailers immediately when items are added to Radarr/Sonarr"
    show_message ""
    
    while true; do
        read -rp "Wait for media files before downloading trailers? [Y/n]: " wait_choice
        wait_choice=${wait_choice:-Y}
        
        case "$wait_choice" in
            [Yy]|[Yy][Ee][Ss])
                export WAIT_FOR_MEDIA="true"
                show_message $GREEN "✓ Will wait for media files before downloading trailers"
                log_to_file "Will wait for media files before downloading trailers"
                break
                ;;
            [Nn]|[Nn][Oo])
                export WAIT_FOR_MEDIA="false"
                show_message $GREEN "✓ Will download trailers immediately when items are added"
                log_to_file "Will download trailers immediately when items are added"
                break
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # Port configuration
    show_message ""
    show_message "Port Configuration"
    show_message ""
    show_message "Default is 7889"
    show_message "- You can change it to a different port as needed"
    show_message "- Make sure the port is not being used by another program"
    show_message ""
    show_message "# To check if port is in use, run below commands"
    show_message "sudo netstat -tlnp | grep :7889"
    show_message "sudo lsof -i :7889"
    show_message ""
    
    while true; do
        read -rp "Web interface port [$DEFAULT_PORT]: " port
        port=${port:-$DEFAULT_PORT}
        
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt 1023 ] && [ "$port" -lt 65536 ]; then
            export APP_PORT="$port"
            show_message $GREEN "✓ Web interface will be available on port $port"
            log_to_file "Web interface will be available on port $port"
            break
        else
            echo "Please enter a valid port number (1024-65535)"
        fi
    done
    
    end_message "Basic configuration complete"
}

# Function to configure GPU settings
configure_gpu_settings() {
    # Source GPU detection results if available
    if [ -f "/tmp/gpu_detection_results" ]; then
        source "/tmp/gpu_detection_results"
    fi

    start_message "Configuring GPU settings"

    if [ ${#AVAILABLE_GPUS[@]} -eq 0 ]; then
        log_to_file "No supported GPUs detected. Hardware acceleration not enabled."
        export ENABLE_HWACCEL="false"
        export HWACCEL_TYPE="none"
        show_message $YELLOW "! No supported GPUs detected - hardware acceleration disabled"
        end_message "GPU configuration complete (hardware acceleration disabled)"
        return 0
    fi

    show_message ""
    show_message "GPU Hardware Acceleration Configuration"
    show_message ""
    show_message "Detected GPUs: ${DETECTED_GPUS[*]}"
    show_message "Hardware acceleration can significantly improve video processing performance"
    show_message "but may require additional system setup and drivers."
    show_message ""
    
    # Ask if user wants to enable hardware acceleration
    while true; do
        read -rp "Enable GPU hardware acceleration? [Y/n]: " hwaccel_choice
        hwaccel_choice=${hwaccel_choice:-Y}
        
        case "$hwaccel_choice" in
            [Yy]|[Yy][Ee][Ss])
                export ENABLE_HWACCEL="true"
                show_message $GREEN "✓ Hardware acceleration enabled"
                break
                ;;
            [Nn]|[Nn][Oo])
                export ENABLE_HWACCEL="false"
                export HWACCEL_TYPE="none"
                log_to_file "Hardware acceleration disabled by user choice"
                show_message $GREEN "✓ Hardware acceleration disabled"
                end_message "GPU configuration complete (hardware acceleration disabled)"
                return 0
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # If multiple GPUs are available, ask user to choose
    if [ ${#AVAILABLE_GPUS[@]} -gt 1 ]; then
        show_message ""
        show_message "GPU Selection:"
        show_message ""
        show_message "Multiple GPUs detected. Trailarr can only use one GPU for hardware acceleration."
        show_message "Please select which GPU to use:"
        show_message ""

        for i in "${!AVAILABLE_GPUS[@]}"; do
            show_message "  $((i+1)). ${DETECTED_GPUS[$i]}"
        done
        show_message ""
        
        while true; do
            read -rp "Select GPU (1-${#AVAILABLE_GPUS[@]}): " gpu_choice
            
            if [[ "$gpu_choice" =~ ^[0-9]+$ ]] && [ "$gpu_choice" -ge 1 ] && [ "$gpu_choice" -le ${#AVAILABLE_GPUS[@]} ]; then
                selected_index=$((gpu_choice - 1))
                export HWACCEL_TYPE="${AVAILABLE_GPUS[$selected_index]}"
                show_message $GREEN "✓ Selected ${DETECTED_GPUS[$selected_index]} for hardware acceleration"
                log_to_file "Selected ${DETECTED_GPUS[$selected_index]} for hardware acceleration"
                break
            else
                echo "Please enter a number between 1 and ${#AVAILABLE_GPUS[@]}"
            fi
        done
    else
        # Only one GPU available
        export HWACCEL_TYPE="${AVAILABLE_GPUS[0]}"
        show_message $GREEN "✓ Using ${DETECTED_GPUS[0]} for hardware acceleration"
        log_to_file "Using ${DETECTED_GPUS[0]} for hardware acceleration"
    fi
    
    # Provide driver installation instructions based on detected GPUs
    if [ "$ENABLE_HWACCEL" = "true" ]; then
        show_message ""
        show_message "Hardware Acceleration Setup Instructions"
        show_message ""
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
    
    end_message "GPU configuration complete"
}

# Function to write configuration to file
write_configuration() {    
    start_message "Writing configuration to file"
    
    # Ensure data directory exists
    show_temp_message "Creating data directory"
    mkdir -p "$DATA_DIR"
    
    # Create .env file with configuration
    show_temp_message "Writing configuration file"
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
    end_message "Configuration written to file"
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
}

# Main function
main() {
    # Create install directory if it doesn't exist
    sudo mkdir -p "/opt/trailarr"
    # Create data directory if it doesn't exist
    sudo mkdir -p "$DATA_DIR"
    
    start_message "Starting interactive configuration"
    
    show_message ""
    show_message "Interactive Configuration Setup"
    show_message ""
    show_message "Starting interactive configuration for Trailarr..."
    show_message ""
        
    # Prompt for basic configuration
    prompt_basic_config
    
    # Configure GPU settings
    configure_gpu_settings
    
    # Write configuration
    write_configuration
    
    # Display summary
    display_summary
    
    end_message "Interactive configuration complete"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
