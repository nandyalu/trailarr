#!/bin/bash

# Interactive Configuration for Trailarr Bare Metal Installation
# Prompts user for application settings and GPU preferences

set -e

# Source the common functions - first try baremetal logging, fallback to interactive_echo
if [ -f "$(dirname "$0")/logging.sh" ]; then
    source "$(dirname "$0")/logging.sh"
    # If we're in a sub-script, we need to reuse the existing log file
    if [ -z "$INSTALL_LOG_FILE" ]; then
        INSTALL_LOG_FILE="$(pwd)/trailarr_install.log"
        export INSTALL_LOG_FILE
    fi
    # Use print_message for interactive prompts instead of interactive_echo
    interactive_echo() { 
        local message="$1"
        local width=80
        local padding="|  "
        local end_padding="  |"
        local line_length=$((width - ${#padding} - ${#end_padding}))
        
        while IFS= read -r line; do
            printf "%s%-${line_length}s%s\n" "$padding" "$line" "$end_padding"
        done <<< "$(echo "$message" | fold -sw $line_length)"
        log_to_file "INTERACTIVE: $message"
    }
else
    source "$(dirname "$0")/../interactive_echo.sh"
    # Use interactive_echo as interactive_echo for compatibility
    interactive_echo() { interactive_echo "$1"; }
    # Define print_message and start_message/end_message for compatibility
    print_message() { echo -e "$1$2\033[0m"; }
    start_message() { echo -e "$1$2\033[0m"; }
    end_message() { echo -e "$1$2\033[0m"; }
    log_to_file() { echo "$1"; }
    update_env_var() { 
        local var_name="$1"
        local var_value="$2"
        local env_file="$3"
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
    interactive_echo "Basic Application Configuration"
    interactive_echo "=========================================================================="
    
    # Monitor interval
    interactive_echo "Monitor Interval: How often should Trailarr check for new content?"
    echo "  - Minimum is 10"
    echo "  - This determines how frequently the app scans for new movies/shows"
    echo "  - Shorter intervals = more responsive but higher system load"
    echo "  - Longer intervals = less system load but slower to detect new content"
    echo ""
    echo "Common values:"
    echo "  - 60 (1 hour, default)"
    echo "  - 120 (2 hours)" 
    echo "  - 180 (3 hours) [recommended]"
    echo "  - 360 (6 hours)"
    echo ""
    
    while true; do
        read -rp "Enter monitor interval in minutes [$DEFAULT_MONITOR_INTERVAL]: " monitor_interval
        monitor_interval=${monitor_interval:-$DEFAULT_MONITOR_INTERVAL}
        
        if [[ "$monitor_interval" =~ ^[0-9]+$ ]] && [ "$monitor_interval" -gt 9 ]; then
            export MONITOR_INTERVAL="$monitor_interval"
            break
        else
            echo "Please enter a valid number greater than 10"
        fi
    done
    
    interactive_echo "✓ Monitor interval set to $monitor_interval minutes"
    
    # Wait for media
    interactive_echo ""
    interactive_echo "Wait for Media: Should Trailarr wait for media files to be available before downloading trailers?"
    echo "  - true: Wait until movie/show files exist before downloading trailers (recommended)"
    echo "  - false: Download trailers immediately when items are added to Radarr/Sonarr"
    echo ""
    
    while true; do
        read -rp "Wait for media files before downloading trailers? [Y/n]: " wait_choice
        wait_choice=${wait_choice:-Y}
        
        case "$wait_choice" in
            [Yy]|[Yy][Ee][Ss])
                export WAIT_FOR_MEDIA="true"
                interactive_echo "✓ Will wait for media files before downloading trailers"
                break
                ;;
            [Nn]|[Nn][Oo])
                export WAIT_FOR_MEDIA="false"
                interactive_echo "✓ Will download trailers immediately when items are added"
                break
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # Port configuration
    interactive_echo ""
    while true; do
        read -rp "Web interface port [$DEFAULT_PORT]: " port
        port=${port:-$DEFAULT_PORT}
        
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt 1023 ] && [ "$port" -lt 65536 ]; then
            export APP_PORT="$port"
            interactive_echo "✓ Web interface will be available on port $port"
            break
        else
            echo "Please enter a valid port number (1024-65535)"
        fi
    done
    
    interactive_echo "=========================================================================="
}

# Function to configure GPU settings
configure_gpu_settings() {
    # Source GPU detection results if available
    if [ -f "/tmp/gpu_detection_results" ]; then
        source "/tmp/gpu_detection_results"
    fi
    
    if [ ${#AVAILABLE_GPUS[@]} -eq 0 ]; then
        interactive_echo "No supported GPUs detected. Hardware acceleration not enabled."
        export ENABLE_HWACCEL="false"
        export HWACCEL_TYPE="none"
        return 0
    fi
    
    interactive_echo "GPU Hardware Acceleration Configuration"
    interactive_echo "=========================================================================="
    
    interactive_echo "Detected GPUs: ${DETECTED_GPUS[*]}"
    echo ""
    echo "Hardware acceleration can significantly improve video processing performance"
    echo "but may require additional system setup and drivers."
    echo ""
    
    # Ask if user wants to enable hardware acceleration
    while true; do
        read -rp "Enable GPU hardware acceleration? [Y/n]: " hwaccel_choice
        hwaccel_choice=${hwaccel_choice:-Y}
        
        case "$hwaccel_choice" in
            [Yy]|[Yy][Ee][Ss])
                export ENABLE_HWACCEL="true"
                break
                ;;
            [Nn]|[Nn][Oo])
                export ENABLE_HWACCEL="false"
                export HWACCEL_TYPE="none"
                interactive_echo "✓ Hardware acceleration disabled"
                return 0
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # If multiple GPUs are available, ask user to choose
    if [ ${#AVAILABLE_GPUS[@]} -gt 1 ]; then
        interactive_echo ""
        interactive_echo "Multiple GPUs detected. Trailarr can only use one GPU for hardware acceleration."
        echo "Please select which GPU to use:"
        echo ""
        
        for i in "${!AVAILABLE_GPUS[@]}"; do
            echo "  $((i+1)). ${DETECTED_GPUS[$i]}"
        done
        echo ""
        
        while true; do
            read -rp "Select GPU (1-${#AVAILABLE_GPUS[@]}): " gpu_choice
            
            if [[ "$gpu_choice" =~ ^[0-9]+$ ]] && [ "$gpu_choice" -ge 1 ] && [ "$gpu_choice" -le ${#AVAILABLE_GPUS[@]} ]; then
                selected_index=$((gpu_choice - 1))
                export HWACCEL_TYPE="${AVAILABLE_GPUS[$selected_index]}"
                interactive_echo "✓ Selected ${DETECTED_GPUS[$selected_index]} for hardware acceleration"
                break
            else
                echo "Please enter a number between 1 and ${#AVAILABLE_GPUS[@]}"
            fi
        done
    else
        # Only one GPU available
        export HWACCEL_TYPE="${AVAILABLE_GPUS[0]}"
        interactive_echo "✓ Using ${DETECTED_GPUS[0]} for hardware acceleration"
    fi
    
    # Provide driver installation instructions based on detected GPUs
    if [ "$ENABLE_HWACCEL" = "true" ]; then
        interactive_echo ""
        interactive_echo "Hardware Acceleration Setup Instructions:"
        case "$HWACCEL_TYPE" in
            "nvidia")
                interactive_echo "NVIDIA GPU selected. Ensure NVIDIA drivers are installed:"
                interactive_echo "  sudo apt update && sudo apt install -y nvidia-driver-535"
                interactive_echo "  (Reboot required after driver installation)"
                ;;
            "intel")
                interactive_echo "Intel GPU selected. Ensure VAAPI drivers are installed:"
                interactive_echo "  sudo apt update && sudo apt install -y intel-media-va-driver i965-va-driver vainfo"
                ;;
            "amd")
                interactive_echo "AMD GPU selected. Ensure VAAPI drivers are installed:"
                interactive_echo "  sudo apt update && sudo apt install -y mesa-va-drivers vainfo"
                ;;
        esac
        interactive_echo "Note: After installing drivers, restart the Trailarr service to use hardware acceleration"
    fi
    
    interactive_echo "=========================================================================="
}

# Function to write configuration to file
write_configuration() {    
    interactive_echo "Writing configuration to $CONFIG_FILE..."
    
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
    
    interactive_echo "✓ Configuration written to $CONFIG_FILE"
}

# Function to display configuration summary
display_summary() {
    interactive_echo "Configuration Summary"
    interactive_echo "=========================================================================="
    interactive_echo "Application Port: ${APP_PORT}"
    interactive_echo "Data Directory: $DATA_DIR"
    interactive_echo "Monitor Interval: ${MONITOR_INTERVAL} minutes"
    interactive_echo "Wait for Media: ${WAIT_FOR_MEDIA}"
    interactive_echo "Hardware Acceleration: ${ENABLE_HWACCEL}"
    if [ "$ENABLE_HWACCEL" = "true" ]; then
        interactive_echo "GPU Type: ${HWACCEL_TYPE}"
    fi
    interactive_echo "Installation Mode: baremetal"
    interactive_echo "=========================================================================="
    
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
    interactive_echo "Interactive Configuration Setup"
    interactive_echo "=========================================================================="
    
    # Create install directory if it doesn't exist
    sudo mkdir -p "/opt/trailarr"
    # Create data directory if it doesn't exist
    sudo mkdir -p "$DATA_DIR"
    
    # Prompt for basic configuration
    prompt_basic_config
    
    # Configure GPU settings
    configure_gpu_settings
    
    # Write configuration
    write_configuration
    
    # Display summary
    display_summary
    
    interactive_echo "✓ Interactive configuration complete"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
