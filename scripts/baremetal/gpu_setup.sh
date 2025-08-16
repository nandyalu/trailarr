#!/bin/bash

# GPU Detection and Driver Installation for Trailarr Bare Metal Installation
# Adapted from container scripts for system-wide installation

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
    show_message() { echo -e "$1\033[0m"; }
    start_message() { echo -e "$1$2\033[0m"; }
    end_message() { echo -e "$1$2\033[0m"; }
    log_to_file() { echo "$1"; }
    run_logged_command() { eval "$2"; }
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

# Variables
DETECTED_GPUS=()
AVAILABLE_GPUS=()

# Function to detect and map GPU devices dynamically (adapted from container script)
detect_gpu_devices() {
    log_to_file "Starting GPU device detection"
    
    # Initialize device mappings
    export GPU_DEVICE_NVIDIA=""
    export GPU_DEVICE_INTEL=""
    export GPU_DEVICE_AMD=""
    
    # Initialize availability flags
    export GPU_AVAILABLE_NVIDIA="false"
    export GPU_AVAILABLE_INTEL="false"
    export GPU_AVAILABLE_AMD="false"

    # Check for DRI devices and map them to specific GPUs
    if [ -d /dev/dri ]; then
        for device in /dev/dri/renderD*; do
            if [ -e "$device" ]; then
                log_to_file "Checking device: $device"
                # Get sysfs path
                syspath=$(udevadm info --query=path --name="$device" 2>/dev/null || echo "")
                if [ -n "$syspath" ]; then
                    fullpath="/sys$syspath/device"

                    # Check if the device has a vendor file
                    if [ -f "$fullpath/vendor" ]; then
                        vendor=$(cat "$fullpath/vendor")
                        log_to_file "Device $device has vendor: $vendor"
                        # NVIDIA: 10de, Intel: 8086, AMD: 1002
                        # PCI Vendor IDS: https://pci-ids.ucw.cz/
                        case "$vendor" in
                            0x10de)
                                [ -z "$GPU_DEVICE_NVIDIA" ] && export GPU_DEVICE_NVIDIA="$device"
                                log_to_file "NVIDIA device detected: $device"
                                ;;
                            0x8086)
                                [ -z "$GPU_DEVICE_INTEL" ] && export GPU_DEVICE_INTEL="$device"
                                export GPU_AVAILABLE_INTEL="true"
                                log_to_file "Intel device detected: $device"
                                ;;
                            0x1002|0x1022)
                                [ -z "$GPU_DEVICE_AMD" ] && export GPU_DEVICE_AMD="$device"
                                export GPU_AVAILABLE_AMD="true"
                                log_to_file "AMD device detected: $device"
                                ;;
                        esac
                    fi
                fi
            fi
        done
    fi

    # Check for NVIDIA GPU using nvidia-smi or lspci
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi > /dev/null 2>&1; then
            export GPU_AVAILABLE_NVIDIA="true"
        fi
    elif lspci | grep -i nvidia &> /dev/null; then
        # NVIDIA GPU present but drivers may not be installed
        export GPU_AVAILABLE_NVIDIA="potential"
    fi
}

# Check and report NVIDIA GPU status
check_nvidia_gpu() {
    start_message "$BLUE" "Checking for NVIDIA GPU..."
    log_to_file "Starting NVIDIA GPU detection"
    
    if [ "$GPU_AVAILABLE_NVIDIA" = "true" ]; then
        # Get NVIDIA GPU information
        GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            show_message "$GREEN" "✓ NVIDIA GPU detected with drivers: $GPU_INFO"
            show_message "$GREEN" "  → NVIDIA hardware acceleration (CUDA) is available"
            log_to_file "NVIDIA GPU found with drivers: $GPU_INFO"
            DETECTED_GPUS+=("NVIDIA")
            AVAILABLE_GPUS+=("nvidia")
            if [ -n "$GPU_DEVICE_NVIDIA" ]; then
                show_message "  → NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
                log_to_file "NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
            fi
            end_message "$GREEN" "✓ NVIDIA GPU ready"
        fi
    elif [ "$GPU_AVAILABLE_NVIDIA" = "potential" ]; then
        NVIDIA_GPU=$(lspci | grep -i nvidia | head -1)
        if [ -n "$NVIDIA_GPU" ]; then
            show_message "$YELLOW" "⚠ NVIDIA GPU detected but drivers not installed:"
            show_message "$YELLOW" "  $NVIDIA_GPU"
            show_message "$YELLOW" "  To enable NVIDIA hardware acceleration, install drivers with:"
            show_message "$YELLOW" "    sudo apt update && sudo apt install -y nvidia-driver-535"
            show_message "$YELLOW" "    (Reboot required after driver installation)"
            log_to_file "NVIDIA GPU detected without drivers: $NVIDIA_GPU"
            DETECTED_GPUS+=("NVIDIA (no drivers)")
            end_message "$YELLOW" "! NVIDIA GPU needs drivers"
        fi
    else
        end_message "$BLUE" "→ No NVIDIA GPU detected"
        log_to_file "No NVIDIA GPU detected"
    fi
}

# Check and report Intel GPU status
check_intel_gpu() {
    start_message "$BLUE" "Checking for Intel GPU..."
    log_to_file "Starting Intel GPU detection"
    
    if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
        # Check for Intel GPU using lspci
        INTEL_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' Intel| ARC')
        if [ -n "$INTEL_GPU" ]; then
            show_message "$GREEN" "✓ Intel GPU detected: $INTEL_GPU"
            show_message "  → Intel GPU device: $GPU_DEVICE_INTEL"
            log_to_file "Intel GPU found: $INTEL_GPU"
            log_to_file "Intel GPU device: $GPU_DEVICE_INTEL"
            DETECTED_GPUS+=("Intel")
            AVAILABLE_GPUS+=("intel")
            
            # Test VAAPI capability
            if command -v vainfo &> /dev/null; then
                VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_INTEL" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|VP8|VP9|AV1")
                if [ -n "$VAAPI_INFO" ]; then
                    show_message "$GREEN" "  → VAAPI capabilities detected (H.264, HEVC, VP8, VP9, AV1)"
                    log_to_file "Intel VAAPI capabilities detected"
                fi
            else
                show_message "$YELLOW" "  → vainfo not found. To enable Intel GPU acceleration, install VAAPI:"
                show_message "$YELLOW" "    sudo apt update && sudo apt install -y intel-media-va-driver i965-va-driver vainfo"
                show_message "$YELLOW" "    (App restart required after installation)"
                log_to_file "Intel GPU detected but vainfo not available"
            fi
            end_message "$GREEN" "✓ Intel GPU ready"
        fi
    else
        if [ -d /dev/dri ]; then
            end_message "$BLUE" "→ No Intel GPU detected in DRI devices"
            log_to_file "No Intel GPU detected in DRI devices"
        else
            end_message "$BLUE" "→ Intel GPU not available (/dev/dri does not exist)"
            log_to_file "Intel GPU not available - /dev/dri does not exist"
        fi
    fi
}

# Check and report AMD GPU status
check_amd_gpu() {
    start_message "$BLUE" "Checking for AMD GPU..."
    log_to_file "Starting AMD GPU detection"
    
    if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
        # Check for AMD GPU using lspci
        AMD_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' AMD| ATI| Radeon')
        if [ -n "$AMD_GPU" ]; then
            show_message "$GREEN" "✓ AMD GPU detected: $AMD_GPU"
            show_message "  → AMD GPU device: $GPU_DEVICE_AMD"
            log_to_file "AMD GPU found: $AMD_GPU"
            log_to_file "AMD GPU device: $GPU_DEVICE_AMD"
            DETECTED_GPUS+=("AMD")
            AVAILABLE_GPUS+=("amd")
            
            # Test VAAPI capability for AMD
            if command -v vainfo &> /dev/null; then
                VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_AMD" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|AV1")
                if [ -n "$VAAPI_INFO" ]; then
                    show_message "$GREEN" "  → VAAPI capabilities detected (H.264, HEVC, AV1)"
                    log_to_file "AMD VAAPI capabilities detected"
                fi
            else
                show_message "$YELLOW" "  → vainfo not found. To enable AMD GPU acceleration, install VAAPI:"
                show_message "$YELLOW" "    sudo apt update && sudo apt install -y mesa-va-drivers vainfo"
                show_message "$YELLOW" "    (App restart required after installation)"
                log_to_file "AMD GPU detected but vainfo not available"
            fi
            end_message "$GREEN" "✓ AMD GPU ready"
        fi
    else
        if [ -d /dev/dri ]; then
            end_message "$BLUE" "→ No AMD GPU detected in DRI devices"
            log_to_file "No AMD GPU detected in DRI devices"
        else
            end_message "$BLUE" "→ AMD GPU not available (/dev/dri does not exist)"
            log_to_file "AMD GPU not available - /dev/dri does not exist"
        fi
    fi
}

# Save GPU detection results to environment file
save_gpu_env_vars() {
    local data_dir="${APP_DATA_DIR:-/var/lib/trailarr}"
    local env_file="$data_dir/.env"
    
    start_message "$BLUE" "Saving GPU configuration..."
    log_to_file "Saving GPU detection results to $env_file"
    
    # Ensure data directory exists
    mkdir -p "$data_dir"
    touch "$env_file"
    
    # Set GPU availability environment variables using the new function
    update_env_var "GPU_AVAILABLE_NVIDIA" "$GPU_AVAILABLE_NVIDIA" "$env_file"
    update_env_var "GPU_AVAILABLE_INTEL" "$GPU_AVAILABLE_INTEL" "$env_file"
    update_env_var "GPU_AVAILABLE_AMD" "$GPU_AVAILABLE_AMD" "$env_file"
    
    # Set GPU device environment variables
    update_env_var "GPU_DEVICE_NVIDIA" "$GPU_DEVICE_NVIDIA" "$env_file"
    update_env_var "GPU_DEVICE_INTEL" "$GPU_DEVICE_INTEL" "$env_file"
    update_env_var "GPU_DEVICE_AMD" "$GPU_DEVICE_AMD" "$env_file"
    
    log_to_file "GPU configuration saved successfully"
    end_message "$GREEN" "✓ GPU configuration saved"
}

# Main GPU detection and setup function
main() {
    show_message "GPU Detection for Trailarr"
    log_to_file "========== GPU Detection Process Started =========="
    
    # Detect GPU devices
    detect_gpu_devices
    
    # Check each GPU type
    check_nvidia_gpu
    check_intel_gpu  
    check_amd_gpu
    
    # Summary
    if [ ${#DETECTED_GPUS[@]} -eq 0 ]; then
        echo " "
        show_message "$YELLOW" "No supported GPUs detected. Hardware acceleration will not be available.
The application will run using software encoding/decoding."
        log_to_file "No GPUs detected - software encoding will be used"
    else
        echo " "
        show_message "$GREEN" "Summary: Detected GPUs: ${DETECTED_GPUS[*]}"
        log_to_file "GPU detection summary: ${DETECTED_GPUS[*]}"
        
        if [ ${#DETECTED_GPUS[@]} -gt 0 ]; then
            echo " "
            show_message "Note: If you plan to use hardware acceleration, ensure all necessary
drivers and tools are installed as shown above, then restart the app."
        fi
    fi
    
    # Save GPU detection results to .env file
    save_gpu_env_vars
    
    # Return the detected GPUs for use by the installer
    export DETECTED_GPUS
    export AVAILABLE_GPUS
    
    log_to_file "========== GPU Detection Process Completed =========="
    show_message "$GREEN" "GPU detection complete"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi