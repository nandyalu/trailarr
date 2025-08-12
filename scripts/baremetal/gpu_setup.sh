#!/bin/bash

# GPU Detection and Driver Installation for Trailarr Bare Metal Installation
# Adapted from container scripts for system-wide installation

set -e

# Source the common functions
source "$(dirname "$0")/../box_echo.sh"

# Variables
DETECTED_GPUS=()
AVAILABLE_GPUS=()

# Function to detect and map GPU devices dynamically (adapted from container script)
detect_gpu_devices() {
    box_echo "Detecting available GPU devices..."
    
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
                # Get sysfs path
                syspath=$(udevadm info --query=path --name="$device" 2>/dev/null || echo "")
                if [ -n "$syspath" ]; then
                    fullpath="/sys$syspath/device"

                    # Check if the device has a vendor file
                    if [ -f "$fullpath/vendor" ]; then
                        vendor=$(cat "$fullpath/vendor")
                        # NVIDIA: 10de, Intel: 8086, AMD: 1002
                        # PCI Vendor IDS: https://pci-ids.ucw.cz/
                        case "$vendor" in
                            0x10de)
                                [ -z "$GPU_DEVICE_NVIDIA" ] && export GPU_DEVICE_NVIDIA="$device"
                                ;;
                            0x8086)
                                [ -z "$GPU_DEVICE_INTEL" ] && export GPU_DEVICE_INTEL="$device"
                                export GPU_AVAILABLE_INTEL="true"
                                ;;
                            0x1002|0x1022)
                                [ -z "$GPU_DEVICE_AMD" ] && export GPU_DEVICE_AMD="$device"
                                export GPU_AVAILABLE_AMD="true"
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
    box_echo "Checking for NVIDIA GPU availability..."
    if [ "$GPU_AVAILABLE_NVIDIA" = "true" ]; then
        # Get NVIDIA GPU information
        GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            box_echo "✓ NVIDIA GPU detected with drivers: $GPU_INFO"
            box_echo "NVIDIA hardware acceleration (CUDA) is available."
            DETECTED_GPUS+=("NVIDIA")
            AVAILABLE_GPUS+=("nvidia")
            if [ -n "$GPU_DEVICE_NVIDIA" ]; then
                box_echo "NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
            fi
        fi
    elif [ "$GPU_AVAILABLE_NVIDIA" = "potential" ]; then
        NVIDIA_GPU=$(lspci | grep -i nvidia | head -1)
        if [ -n "$NVIDIA_GPU" ]; then
            box_echo "⚠ NVIDIA GPU detected but drivers not installed: $NVIDIA_GPU"
            box_echo "To enable NVIDIA hardware acceleration, install drivers with:"
            box_echo "  sudo apt update && sudo apt install -y nvidia-driver-535"
            box_echo "  (Reboot required after driver installation)"
            DETECTED_GPUS+=("NVIDIA (no drivers)")
        fi
    else
        box_echo "No NVIDIA GPU detected"
    fi
    box_echo "--------------------------------------------------------------------------"
}

# Check and report Intel GPU status
check_intel_gpu() {
    box_echo "Checking for Intel GPU availability..."
    if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
        # Check for Intel GPU using lspci
        INTEL_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' Intel| ARC')
        if [ -n "$INTEL_GPU" ]; then
            box_echo "✓ Intel GPU detected: $INTEL_GPU"
            box_echo "Intel GPU device: $GPU_DEVICE_INTEL"
            DETECTED_GPUS+=("Intel")
            AVAILABLE_GPUS+=("intel")
            
            # Test VAAPI capability
            if command -v vainfo &> /dev/null; then
                VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_INTEL" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|VP8|VP9|AV1")
                if [ -n "$VAAPI_INFO" ]; then
                    box_echo "VAAPI capabilities detected (H.264, HEVC, VP8, VP9, AV1)"
                fi
            else
                box_echo "vainfo not found. To enable Intel GPU acceleration, install VAAPI:"
                echo "  sudo apt update && sudo apt install -y intel-media-va-driver i965-va-driver vainfo"
                echo "  (App restart required after installation)"
            fi
        fi
    else
        if [ -d /dev/dri ]; then
            box_echo "No Intel GPU detected in DRI devices"
        else
            box_echo "Intel GPU is not available. /dev/dri does not exist"
        fi
    fi
    box_echo "--------------------------------------------------------------------------"
}

# Check and report AMD GPU status
check_amd_gpu() {
    box_echo "Checking for AMD GPU availability..."
    if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
        # Check for AMD GPU using lspci
        AMD_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' AMD| ATI| Radeon')
        if [ -n "$AMD_GPU" ]; then
            box_echo "✓ AMD GPU detected: $AMD_GPU"
            box_echo "AMD GPU device: $GPU_DEVICE_AMD"
            DETECTED_GPUS+=("AMD")
            AVAILABLE_GPUS+=("amd")
            
            # Test VAAPI capability for AMD
            if command -v vainfo &> /dev/null; then
                VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_AMD" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|AV1")
                if [ -n "$VAAPI_INFO" ]; then
                    box_echo "VAAPI capabilities detected (H.264, HEVC, AV1)"
                fi
            else
                box_echo "vainfo not found. To enable AMD GPU acceleration, install VAAPI:"
                echo "  sudo apt update && sudo apt install -y mesa-va-drivers vainfo"
                echo "  (App restart required after installation)"
            fi
        fi
    else
        if [ -d /dev/dri ]; then
            box_echo "No AMD GPU detected in DRI devices"
        else
            box_echo "AMD GPU is not available. /dev/dri does not exist"
        fi
    fi
    box_echo "--------------------------------------------------------------------------"
}

# Save GPU detection results to environment file
save_gpu_env_vars() {
    local data_dir="${APP_DATA_DIR:-/var/lib/trailarr}"
    local env_file="$data_dir/.env"
    
    # Ensure data directory exists
    mkdir -p "$data_dir"
    touch "$env_file"
    
    # Function to update or add environment variable
    update_env_var() {
        local var_name="$1"
        local var_value="$2"
        local env_file="$3"
        
        # Remove existing entry if it exists
        grep -v "^${var_name}=" "$env_file" > "${env_file}.tmp" 2>/dev/null || touch "${env_file}.tmp"
        
        # Add new entry
        echo "${var_name}=${var_value}" >> "${env_file}.tmp"
        
        # Replace original file
        mv "${env_file}.tmp" "$env_file"
    }
    
    # Set GPU availability environment variables
    update_env_var "GPU_AVAILABLE_NVIDIA" "$GPU_AVAILABLE_NVIDIA" "$env_file"
    update_env_var "GPU_AVAILABLE_INTEL" "$GPU_AVAILABLE_INTEL" "$env_file"
    update_env_var "GPU_AVAILABLE_AMD" "$GPU_AVAILABLE_AMD" "$env_file"
    
    # Set GPU device environment variables
    update_env_var "GPU_DEVICE_NVIDIA" "$GPU_DEVICE_NVIDIA" "$env_file"
    update_env_var "GPU_DEVICE_INTEL" "$GPU_DEVICE_INTEL" "$env_file"
    update_env_var "GPU_DEVICE_AMD" "$GPU_DEVICE_AMD" "$env_file"
    
    box_echo "✓ GPU detection results saved to $env_file"
}

# Main GPU detection and setup function
main() {
    box_echo "GPU Detection for Trailarr"
    box_echo "=========================================================================="
    
    # Detect GPU devices
    detect_gpu_devices
    
    # Check each GPU type
    check_nvidia_gpu
    check_intel_gpu  
    check_amd_gpu
    
    if [ ${#DETECTED_GPUS[@]} -eq 0 ]; then
        box_echo "No supported GPUs detected. Hardware acceleration will not be available."
        box_echo "The application will run using software encoding/decoding."
    else
        box_echo "Summary: Detected GPUs: ${DETECTED_GPUS[*]}"
        
        if [ ${#DETECTED_GPUS[@]} -gt 0 ]; then
            box_echo ""
            box_echo "Note: If you plan to use hardware acceleration, ensure all necessary"
            box_echo "drivers and tools are installed as shown above, then restart the app."
        fi
    fi
    
    # Save GPU detection results to .env file
    save_gpu_env_vars
    
    # Return the detected GPUs for use by the installer
    export DETECTED_GPUS
    export AVAILABLE_GPUS
    
    box_echo "=========================================================================="
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi