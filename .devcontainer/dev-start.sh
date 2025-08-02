#!/bin/sh


# Ensure Node.js and npm are in the PATH
export PATH=$PATH:/usr/local/bin:/usr/local/share/nvm/current/bin
echo $PATH

# Set TimeZone based on env variable
echo "Setting TimeZone to $TZ"
echo $TZ > /etc/timezone && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

# Create data folder for storing database and other config files
mkdir -p /config/logs && chown -R vscode:vscode /config

# Function to detect and map GPU devices dynamically
detect_gpu_devices() {
    # Initialize device mappings
    export GPU_DEVICE_NVIDIA=""
    export GPU_DEVICE_INTEL=""
    export GPU_DEVICE_AMD=""

    # Check for DRI devices and map them to specific GPUs
    if [ -d /dev/dri ]; then
        for device in /dev/dri/renderD*; do
            if [ -e "$device" ]; then
                # Get sysfs path
                syspath=$(udevadm info --query=path --name="$device" 2>/dev/null)
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
                            ;;
                        0x1002|0x1022)
                            [ -z "$GPU_DEVICE_AMD" ] && export GPU_DEVICE_AMD="$device"
                            ;;
                    esac
                fi
            fi
        done
    fi

    # Fallback to renderD128 if nothing was detected
    if [ -e "/dev/dri/renderD128" ]; then
        [ -z "$GPU_DEVICE_INTEL" ] && export GPU_DEVICE_INTEL="/dev/dri/renderD128"
        [ -z "$GPU_DEVICE_AMD" ] && export GPU_DEVICE_AMD="/dev/dri/renderD128"
        [ -z "$GPU_DEVICE_NVIDIA" ] && export GPU_DEVICE_NVIDIA="/dev/dri/renderD128"
    fi
}

# Detect GPU devices before checking for availability
detect_gpu_devices

# Check for NVIDIA GPU
echo "Checking for NVIDIA GPU availability..."
export GPU_AVAILABLE_NVIDIA="false"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        # Get NVIDIA GPU information
        GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            echo "NVIDIA GPU detected: $GPU_INFO"
            echo "NVIDIA hardware acceleration (CUDA) is available."
            export GPU_AVAILABLE_NVIDIA="true"
            if [ -n "$GPU_DEVICE_NVIDIA" ]; then
                echo "NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
            fi
        else
            echo "NVIDIA GPU not detected - no device information available."
        fi
    else
        echo "NVIDIA GPU not detected - nvidia-smi failed."
    fi
else
    echo "nvidia-smi command not found. NVIDIA GPU not detected."
fi

# Check if /dev/dri exists and check for Intel GPU
echo "Checking for Intel GPU availability..."
export GPU_AVAILABLE_INTEL="false"
if [ -d /dev/dri ]; then
    # Check for Intel GPU
    INTEL_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' Intel| ARC')
    if [ -n "$INTEL_GPU" ]; then
        export GPU_AVAILABLE_INTEL="true"
        echo "Intel GPU detected: $INTEL_GPU"
        if [ -n "$GPU_DEVICE_INTEL" ]; then
            echo "Intel GPU device: $GPU_DEVICE_INTEL"
        else
            echo "Intel GPU device: /dev/dri/renderD128 (default fallback)"
        fi
        echo "Intel hardware acceleration (VAAPI) is available."
        
        # Test VAAPI capability
        device_to_test="${GPU_DEVICE_INTEL:-/dev/dri/renderD128}"
        if command -v vainfo &> /dev/null; then
            VAAPI_INFO=$(vainfo --display drm --device "$device_to_test" 2>/dev/null | grep -i "VAProfile" | head -2)
            if [ -n "$VAAPI_INFO" ]; then
                echo "VAAPI capabilities detected:"
                echo "$VAAPI_INFO" | while read -r line; do echo "  $line"; done
            fi
        fi
    else
        echo "No Intel GPU detected in PCI devices."
    fi
else
    echo "Intel GPU is not available. /dev/dri does not exist."
fi

echo "Checking for AMD GPU availability..."
export GPU_AVAILABLE_AMD="false"
if [ -d /dev/dri ]; then
    # Check for AMD GPU
    AMD_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' AMD| ATI| Radeon')
    if [ -n "$AMD_GPU" ]; then
        export GPU_AVAILABLE_AMD="true"
        echo "AMD GPU detected: $AMD_GPU"
        if [ -n "$GPU_DEVICE_AMD" ]; then
            echo "AMD GPU device: $GPU_DEVICE_AMD"
        else
            echo "AMD GPU device: /dev/dri/renderD128 (default fallback)"
        fi
        echo "AMD hardware acceleration (VAAPI) is available."
        
        # Test VAAPI capability for AMD
        device_to_test="${GPU_DEVICE_AMD:-/dev/dri/renderD128}"
        if command -v vainfo &> /dev/null; then
            VAAPI_INFO=$(vainfo --display drm --device "$device_to_test" 2>/dev/null | grep -i "VAProfile" | head -2)
            if [ -n "$VAAPI_INFO" ]; then
                echo "VAAPI capabilities detected:"
                echo "$VAAPI_INFO" | while read -r line; do echo "  $line"; done
            fi
        fi
    else
        echo "No AMD GPU detected in PCI devices."
    fi
else
    echo "AMD GPU is not available. /dev/dri does not exist."
fi

# Check user group memberships for GPU access
echo "Checking container user permissions for GPU access..."
if [ -d /dev/dri ]; then
    # Check if render group exists and get GID
    RENDER_GID=$(stat -c '%g' /dev/dri/renderD128 2>/dev/null)
    VIDEO_GID=$(getent group video 2>/dev/null | cut -d: -f3)
    
    if [ -n "$RENDER_GID" ]; then
        echo "DRI render device group ID: $RENDER_GID"
        # Check if current user will have access to render devices
        if groups | grep -q "render\|$RENDER_GID"; then
            echo "Container user has render group access."
        else
            echo "Note: Container user may need render group access for optimal GPU performance."
        fi
    fi
    
    if [ -n "$VIDEO_GID" ]; then
        echo "Video group ID: $VIDEO_GID"
        if groups | grep -q "video\|$VIDEO_GID"; then
            echo "Container user has video group access."
        else
            echo "Note: Container user may need video group access for GPU functionality."
        fi
    fi
else
    echo "No DRI devices available - GPU group checks skipped."
fi

# Check the version of yt-dlp and store it in a global environment variable
YTDLP_VERSION=$(yt-dlp --version)
export YTDLP_VERSION

# Run Alembic migrations
echo "Running Alembic migrations"
cd backend
alembic upgrade head && echo "Alembic migrations ran successfully"

# Install Angular & dependencies
echo "Installing Angular and it's dependencies"
npm install -g @angular/cli@19.2.10
cd ../frontend && npm install
ng completion

# Start Angular application
# echo "Building Angular application"
# cd /app/frontend && nohup ng serve &

# Start FastAPI application
# echo "Starting FastAPI application"
# cd /app
# exec gunicorn --bind 0.0.0.0:7888 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api

echo "Dev container started successfully!"