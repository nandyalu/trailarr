#!/bin/bash

# GPU detection and configuration functions
# Source the box_echo function
source /app/scripts/box_echo.sh

# Function to detect and map GPU devices dynamically
detect_gpu_devices() {
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
                syspath=$(udevadm info --query=path --name="$device")
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
        done
    fi

    # Check for NVIDIA GPU using nvidia-smi
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi > /dev/null 2>&1; then
            # Get NVIDIA GPU information
            GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
            if [ -n "$GPU_INFO" ]; then
                export GPU_AVAILABLE_NVIDIA="true"
            fi
        fi
    fi
}

# Check and report NVIDIA GPU status
check_nvidia_gpu() {
    box_echo "Checking for NVIDIA GPU availability..."
    if [ "$GPU_AVAILABLE_NVIDIA" = "true" ]; then
        # Get NVIDIA GPU information
        GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            box_echo "NVIDIA GPU detected: $GPU_INFO"
            box_echo "NVIDIA hardware acceleration (CUDA) is available."
            if [ -n "$GPU_DEVICE_NVIDIA" ]; then
                box_echo "NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
            fi
        else
            box_echo "NVIDIA GPU not detected - no device information available."
            export GPU_AVAILABLE_NVIDIA="false"
        fi
    else
        if command -v nvidia-smi &> /dev/null; then
            box_echo "NVIDIA GPU not detected - nvidia-smi failed or no GPU found."
        else
            box_echo "nvidia-smi command not found. NVIDIA GPU not detected."
        fi
    fi
    box_echo "--------------------------------------------------------------------------";
}

# Check and report Intel GPU status
check_intel_gpu() {
    box_echo "Checking for Intel GPU availability..."
    if [ "$GPU_AVAILABLE_INTEL" = "true" ]; then
        # Check for Intel GPU using lspci
        INTEL_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' Intel| ARC')
        if [ -n "$INTEL_GPU" ]; then
            box_echo "Intel GPU detected: $INTEL_GPU"
            box_echo "Intel GPU device: $GPU_DEVICE_INTEL"
            box_echo "Intel hardware acceleration (VAAPI) is available."
            
            # Test VAAPI capability
            if command -v vainfo &> /dev/null; then
                VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_INTEL" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|VP8|VP9|AV1")
                if [ -n "$VAAPI_INFO" ]; then
                    box_echo "VAAPI capabilities detected (H.264, HEVC, VP8, VP9, AV1):"
                    echo "$VAAPI_INFO" | while read -r line; do box_echo "  $line"; done
                fi
            fi
        else
            box_echo "Intel GPU device detected but not found in PCI devices."
        fi
    else
        if [ -d /dev/dri ]; then
            box_echo "No Intel GPU detected in DRI devices."
        else
            box_echo "Intel GPU is not available. /dev/dri does not exist."
        fi
    fi
    box_echo "--------------------------------------------------------------------------";
}

# Check and report AMD GPU status
check_amd_gpu() {
    box_echo "Checking for AMD GPU availability..."
    if [ "$GPU_AVAILABLE_AMD" = "true" ]; then
        # Check for AMD GPU using lspci
        AMD_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' AMD| ATI| Radeon')
        if [ -n "$AMD_GPU" ]; then
            box_echo "AMD GPU detected: $AMD_GPU"
            box_echo "AMD GPU device: $GPU_DEVICE_AMD"
            box_echo "AMD hardware acceleration (VAAPI) is available."
            
            # Test VAAPI capability for AMD
            if command -v vainfo &> /dev/null; then
                VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_AMD" 2>/dev/null | grep -i "VAProfile" | grep -iE "H264|HEVC|AV1")
                if [ -n "$VAAPI_INFO" ]; then
                    box_echo "VAAPI capabilities detected (H.264, HEVC, AV1):"
                    echo "$VAAPI_INFO" | while read -r line; do box_echo "  $line"; done
                fi
            fi
        else
            box_echo "AMD GPU device detected but not found in PCI devices."
        fi
    else
        if [ -d /dev/dri ]; then
            box_echo "No AMD GPU detected in DRI devices."
        else
            box_echo "AMD GPU is not available. /dev/dri does not exist."
        fi
    fi
    box_echo "--------------------------------------------------------------------------";
}

# Check user permissions for GPU access
check_gpu_permissions() {
    box_echo "Checking container user permissions for GPU access..."
    if [ -d /dev/dri ]; then
        # Check if render group exists and get GID
        RENDER_GID=$(stat -c '%g' /dev/dri/renderD128 2>/dev/null)
        VIDEO_GID=$(getent group video 2>/dev/null | cut -d: -f3)
        
        if [ -n "$RENDER_GID" ]; then
            box_echo "DRI render device group ID: $RENDER_GID"
            # Check if current user will have access to render devices
            if groups | grep -q "render\|$RENDER_GID"; then
                box_echo "Container user has render group access."
            else
                box_echo "Note: Container user may need render group access for optimal GPU performance."
            fi
        fi
        
        if [ -n "$VIDEO_GID" ]; then
            box_echo "Video group ID: $VIDEO_GID"
            if groups | grep -q "video\|$VIDEO_GID"; then
                box_echo "Container user has video group access."
            else
                box_echo "Note: Container user may need video group access for GPU functionality."
            fi
        fi
    else
        box_echo "No DRI devices available - GPU group checks skipped."
    fi
    box_echo "--------------------------------------------------------------------------";
}

# Main GPU detection function that calls all the checks
setup_gpu_detection() {
    # Detect GPU devices before checking for availability
    detect_gpu_devices
    
    # Check each GPU type
    check_nvidia_gpu
    check_intel_gpu
    check_amd_gpu
    check_gpu_permissions
}
