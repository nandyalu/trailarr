#!/bin/bash

# Interactive Configuration for Trailarr Bare Metal Installation
# Prompts user for application settings and GPU preferences

set -e

# Source the common functions
source "$(dirname "$0")/../box_echo.sh"

# Default values
DEFAULT_MONITOR_INTERVAL=10800  # 3 hours in seconds
DEFAULT_WAIT_FOR_MEDIA="true"
DEFAULT_PORT=7889

# Configuration file
CONFIG_FILE="/opt/trailarr/.env"

# Function to prompt for configuration values
prompt_basic_config() {
    box_echo "Basic Application Configuration"
    box_echo "=========================================================================="
    
    # Monitor interval
    box_echo "Monitor Interval: How often should Trailarr check for new content?"
    echo "  - This determines how frequently the app scans for new movies/shows"
    echo "  - Shorter intervals = more responsive but higher system load"
    echo "  - Longer intervals = less system load but slower to detect new content"
    echo ""
    echo "Common values:"
    echo "  - 3600 (1 hour)"
    echo "  - 7200 (2 hours)" 
    echo "  - 10800 (3 hours) [recommended]"
    echo "  - 21600 (6 hours)"
    echo ""
    
    while true; do
        read -p "Enter monitor interval in seconds [$DEFAULT_MONITOR_INTERVAL]: " monitor_interval
        monitor_interval=${monitor_interval:-$DEFAULT_MONITOR_INTERVAL}
        
        if [[ "$monitor_interval" =~ ^[0-9]+$ ]] && [ "$monitor_interval" -gt 0 ]; then
            export MONITOR_INTERVAL="$monitor_interval"
            break
        else
            echo "Please enter a valid positive number"
        fi
    done
    
    box_echo "✓ Monitor interval set to $monitor_interval seconds ($(($monitor_interval / 3600)) hours)"
    
    # Wait for media
    box_echo ""
    box_echo "Wait for Media: Should Trailarr wait for media files to be available before downloading trailers?"
    echo "  - true: Wait until movie/show files exist before downloading trailers (recommended)"
    echo "  - false: Download trailers immediately when items are added to Radarr/Sonarr"
    echo ""
    
    while true; do
        read -p "Wait for media files before downloading trailers? [Y/n]: " wait_choice
        wait_choice=${wait_choice:-Y}
        
        case "$wait_choice" in
            [Yy]|[Yy][Ee][Ss])
                export WAIT_FOR_MEDIA="true"
                box_echo "✓ Will wait for media files before downloading trailers"
                break
                ;;
            [Nn]|[Nn][Oo])
                export WAIT_FOR_MEDIA="false"
                box_echo "✓ Will download trailers immediately when items are added"
                break
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # Port configuration
    box_echo ""
    while true; do
        read -p "Web interface port [$DEFAULT_PORT]: " port
        port=${port:-$DEFAULT_PORT}
        
        if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt 1023 ] && [ "$port" -lt 65536 ]; then
            export APP_PORT="$port"
            box_echo "✓ Web interface will be available on port $port"
            break
        else
            echo "Please enter a valid port number (1024-65535)"
        fi
    done
    
    box_echo "=========================================================================="
}

# Function to configure GPU settings
configure_gpu_settings() {
    # Source GPU detection results if available
    if [ -f "/tmp/gpu_detection_results" ]; then
        source "/tmp/gpu_detection_results"
    fi
    
    if [ ${#AVAILABLE_GPUS[@]} -eq 0 ]; then
        box_echo "No supported GPUs detected. Hardware acceleration will be disabled."
        export ENABLE_HWACCEL="false"
        export HWACCEL_TYPE="none"
        return 0
    fi
    
    box_echo "GPU Hardware Acceleration Configuration"
    box_echo "=========================================================================="
    
    box_echo "Detected GPUs: ${DETECTED_GPUS[*]}"
    echo ""
    echo "Hardware acceleration can significantly improve video processing performance"
    echo "but may require additional system setup and drivers."
    echo ""
    
    # Ask if user wants to enable hardware acceleration
    while true; do
        read -p "Enable GPU hardware acceleration? [Y/n]: " hwaccel_choice
        hwaccel_choice=${hwaccel_choice:-Y}
        
        case "$hwaccel_choice" in
            [Yy]|[Yy][Ee][Ss])
                export ENABLE_HWACCEL="true"
                break
                ;;
            [Nn]|[Nn][Oo])
                export ENABLE_HWACCEL="false"
                export HWACCEL_TYPE="none"
                box_echo "✓ Hardware acceleration disabled"
                return 0
                ;;
            *)
                echo "Please enter Y or N"
                ;;
        esac
    done
    
    # If multiple GPUs are available, ask user to choose
    if [ ${#AVAILABLE_GPUS[@]} -gt 1 ]; then
        box_echo ""
        box_echo "Multiple GPUs detected. Trailarr can only use one GPU for hardware acceleration."
        echo "Please select which GPU to use:"
        echo ""
        
        for i in "${!AVAILABLE_GPUS[@]}"; do
            echo "  $((i+1)). ${DETECTED_GPUS[$i]}"
        done
        echo ""
        
        while true; do
            read -p "Select GPU (1-${#AVAILABLE_GPUS[@]}): " gpu_choice
            
            if [[ "$gpu_choice" =~ ^[0-9]+$ ]] && [ "$gpu_choice" -ge 1 ] && [ "$gpu_choice" -le ${#AVAILABLE_GPUS[@]} ]; then
                selected_index=$((gpu_choice - 1))
                export HWACCEL_TYPE="${AVAILABLE_GPUS[$selected_index]}"
                box_echo "✓ Selected ${DETECTED_GPUS[$selected_index]} for hardware acceleration"
                break
            else
                echo "Please enter a number between 1 and ${#AVAILABLE_GPUS[@]}"
            fi
        done
    else
        # Only one GPU available
        export HWACCEL_TYPE="${AVAILABLE_GPUS[0]}"
        box_echo "✓ Using ${DETECTED_GPUS[0]} for hardware acceleration"
    fi
    
    # Provide driver installation instructions
    case "$HWACCEL_TYPE" in
        "nvidia")
            box_echo ""
            box_echo "NVIDIA GPU selected. Please ensure NVIDIA drivers are installed:"
            echo "  sudo apt install nvidia-driver-535"
            echo "  (Reboot may be required)"
            ;;
        "intel")
            box_echo ""
            box_echo "Intel GPU selected. Required drivers will be installed automatically."
            ;;
        "amd")
            box_echo ""
            box_echo "AMD GPU selected. Required drivers will be installed automatically."
            ;;
    esac
    
    box_echo "=========================================================================="
}

# Function to write configuration to file
write_configuration() {
    box_echo "Writing configuration to $CONFIG_FILE..."
    
    # Create .env file with configuration
    cat > "$CONFIG_FILE" << EOF
# Trailarr Bare Metal Configuration
# Generated on $(date)

# Application Settings
APP_PORT=${APP_PORT:-7889}
APP_DATA_DIR=/var/lib/trailarr
MONITOR_INTERVAL=${MONITOR_INTERVAL:-10800}
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
    
    box_echo "✓ Configuration written to $CONFIG_FILE"
}

# Function to display configuration summary
display_summary() {
    box_echo "Configuration Summary"
    box_echo "=========================================================================="
    box_echo "Application Port: ${APP_PORT}"
    box_echo "Data Directory: /var/lib/trailarr"
    box_echo "Monitor Interval: ${MONITOR_INTERVAL} seconds ($(($MONITOR_INTERVAL / 3600)) hours)"
    box_echo "Wait for Media: ${WAIT_FOR_MEDIA}"
    box_echo "Hardware Acceleration: ${ENABLE_HWACCEL}"
    if [ "$ENABLE_HWACCEL" = "true" ]; then
        box_echo "GPU Type: ${HWACCEL_TYPE}"
    fi
    box_echo "Installation Mode: baremetal"
    box_echo "=========================================================================="
    
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
    box_echo "Interactive Configuration Setup"
    box_echo "=========================================================================="
    
    # Create install directory if it doesn't exist
    sudo mkdir -p "/opt/trailarr"
    
    # Prompt for basic configuration
    prompt_basic_config
    
    # Configure GPU settings
    configure_gpu_settings
    
    # Write configuration
    write_configuration
    
    # Display summary
    display_summary
    
    box_echo "✓ Interactive configuration complete"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi