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
            box_echo "✓ NVIDIA GPU detected: $GPU_INFO"
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

# Install NVIDIA drivers
install_nvidia_drivers() {
    box_echo "Installing NVIDIA drivers and CUDA runtime..."
    
    # Add NVIDIA package repositories
    if [ ! -f /etc/apt/sources.list.d/nvidia-container-toolkit.list ]; then
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
        curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    fi
    
    sudo apt-get update
    
    # Install NVIDIA drivers and CUDA
    sudo apt-get install -y nvidia-driver nvidia-utils nvidia-cuda-toolkit || {
        box_echo "Failed to install NVIDIA drivers, trying alternative method..."
        # Try installing drivers from Ubuntu repositories
        sudo apt-get install -y nvidia-driver-535 nvidia-utils-535 || {
            box_echo "Warning: Could not install NVIDIA drivers automatically"
            box_echo "Please install NVIDIA drivers manually using:"
            box_echo "  sudo apt install nvidia-driver-535"
            return 1
        }
    }
    
    box_echo "✓ NVIDIA drivers installed successfully"
    box_echo "Note: A reboot may be required for NVIDIA drivers to take effect"
}

# Install Intel GPU drivers and VAAPI support
install_intel_drivers() {
    box_echo "Installing Intel GPU drivers and VAAPI support..."
    
    sudo apt-get update
    sudo apt-get install -y \
        intel-media-va-driver \
        intel-media-va-driver-non-free \
        i965-va-driver \
        i965-va-driver-shaders \
        libva2 \
        libva-drm2 \
        vainfo \
        libdrm2 \
        libmfx1 || {
        box_echo "Warning: Some Intel GPU packages could not be installed"
    }
    
    box_echo "✓ Intel GPU drivers installed successfully"
}

# Install AMD GPU drivers and VAAPI support
install_amd_drivers() {
    box_echo "Installing AMD GPU drivers and VAAPI support..."
    
    sudo apt-get update
    sudo apt-get install -y \
        mesa-va-drivers \
        libva2 \
        libva-drm2 \
        vainfo \
        libdrm2 || {
        box_echo "Warning: Some AMD GPU packages could not be installed"
    }
    
    box_echo "✓ AMD GPU drivers installed successfully"
}

# Add user to GPU groups
setup_gpu_groups() {
    box_echo "Setting up user groups for GPU access..."
    
    local username="$1"
    if [ -z "$username" ]; then
        username="$USER"
    fi
    
    # Add user to render group if it exists
    if getent group render > /dev/null 2>&1; then
        sudo usermod -aG render "$username"
        box_echo "Added $username to 'render' group"
    fi
    
    # Add user to video group if it exists
    if getent group video > /dev/null 2>&1; then
        sudo usermod -aG video "$username"
        box_echo "Added $username to 'video' group"
    fi
    
    box_echo "✓ User group setup complete"
    box_echo "Note: You may need to log out and back in for group changes to take effect"
}

# Main GPU detection and setup function
main() {
    box_echo "GPU Detection and Driver Installation"
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
        return 0
    fi
    
    box_echo "Summary: Detected GPUs: ${DETECTED_GPUS[*]}"
    
    # Return the detected GPUs for use by the installer
    export DETECTED_GPUS
    export AVAILABLE_GPUS
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi