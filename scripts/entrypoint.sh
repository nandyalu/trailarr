#!/bin/bash

# THIS SCRIPT WILL BE RUN AS THE ROOT USER IN THE CONTAINER BEFORE APP STARTS

# Source the box_echo function
source /app/scripts/box_echo.sh

# Print 'TRAILARR' as ASCII Art 
# Generated using https://www.asciiart.eu/text-to-ascii-art
# Font: Banner3, Horizontal Layout: Wide, Vertical Layout: Wide, Width: 80
# Border: PlusBox v2, V. Padding: 1, H. Padding: 3
# Whitespace break: enabled, Trim Whitespace: enabled, Replace Whitespace: disabled
echo "+==============================================================================+";
echo "|                                                                              |";
echo "|   ######## ########     ###    #### ##          ###    ########  ########    |";
echo "|      ##    ##     ##   ## ##    ##  ##         ## ##   ##     ## ##     ##   |";
echo "|      ##    ##     ##  ##   ##   ##  ##        ##   ##  ##     ## ##     ##   |";
echo "|      ##    ########  ##     ##  ##  ##       ##     ## ########  ########    |";
echo "|      ##    ##   ##   #########  ##  ##       ######### ##   ##   ##   ##     |";
echo "|      ##    ##    ##  ##     ##  ##  ##       ##     ## ##    ##  ##    ##    |";
echo "|      ##    ##     ## ##     ## #### ######## ##     ## ##     ## ##     ##   |";
echo "|                                                                              |";
echo "+==============================================================================+";
box_echo "";
box_echo "               App Version: ${APP_VERSION}";
box_echo "";
box_echo "--------------------------------------------------------------------------";
box_echo "Starting Trailarr container with the following configuration:"
box_echo "APP_DATA_DIR: ${APP_DATA_DIR}"
box_echo "PUID: ${PUID}"
box_echo "PGID: ${PGID}"
box_echo "TZ: ${TZ}"
box_echo "--------------------------------------------------------------------------";

# Set TimeZone based on env variable
# Print date time before 
box_echo "Current date time: $(date)"
box_echo "Setting TimeZone to ${TZ}"
echo $TZ > /etc/timezone && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata > /dev/null 2>&1
box_echo "Current date time after update: $(date)"
box_echo "--------------------------------------------------------------------------";

box_echo "Creating '$APP_DATA_DIR' folder for storing database and other config files"
# Remove trailing slash from APP_DATA_DIR if it exists
export APP_DATA_DIR=$(echo $APP_DATA_DIR | sed 's:/*$::')

# Check if trailarr.db exists in APP_DATA_DIR folder
if [ -f "${APP_DATA_DIR}/trailarr.db" ]; then
    # Do nothing if database file exists in APP_DATA_DIR folder
    box_echo ""
else
    # Check if trailarr.db exists in /data folder
    if [ -f "/data/trailarr.db" ]; then
        box_echo "Database file 'trailarr.db' found in '/data' folder"
        box_echo "Setting 'APP_DATA_DIR' to '/data' folder to prevent data loss"
        export APP_DATA_DIR="/data"
    fi
fi

# Create appdata (default=/data) folder for storing database and other config files
mkdir -p "${APP_DATA_DIR}/logs" && chmod -R 755 $APP_DATA_DIR
chmod -R 755 /app/assets
mkdir -p /app/tmp && chmod -R 755 /app/tmp
box_echo "--------------------------------------------------------------------------";

# Check if the appdata folder has .env file and Check if there is a env variable 'UPDATE_YTDLP' set to true
/app/scripts/update_ytdlp.sh $APP_DATA_DIR
box_echo "--------------------------------------------------------------------------";

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
box_echo "Checking for NVIDIA GPU availability..."
export GPU_AVAILABLE_NVIDIA="false"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        # Get NVIDIA GPU information
        GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            box_echo "NVIDIA GPU detected: $GPU_INFO"
            box_echo "NVIDIA hardware acceleration (CUDA) is available."
            export GPU_AVAILABLE_NVIDIA="true"
            if [ -n "$GPU_DEVICE_NVIDIA" ]; then
                box_echo "NVIDIA GPU device: $GPU_DEVICE_NVIDIA"
            fi
        else
            box_echo "NVIDIA GPU not detected - no device information available."
        fi
    else
        box_echo "NVIDIA GPU not detected - nvidia-smi failed."
    fi
else
    box_echo "nvidia-smi command not found. NVIDIA GPU not detected."
fi
box_echo "--------------------------------------------------------------------------";

# Check if /dev/dri exists and check for Intel GPU
box_echo "Checking for Intel GPU availability..."
export GPU_AVAILABLE_INTEL="false"
if [ -d /dev/dri ]; then
    # Check for Intel GPU
    INTEL_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' Intel| ARC')
    if [ -n "$INTEL_GPU" ]; then
        export GPU_AVAILABLE_INTEL="true"
        box_echo "Intel GPU detected: $INTEL_GPU"
        if [ -n "$GPU_DEVICE_INTEL" ]; then
            box_echo "Intel GPU device: $GPU_DEVICE_INTEL"
        else
            box_echo "Intel GPU device: /dev/dri/renderD128 (default fallback)"
        fi
        box_echo "Intel hardware acceleration (VAAPI) is available."
        
        # Test VAAPI capability
        device_to_test="${GPU_DEVICE_INTEL:-/dev/dri/renderD128}"
        if command -v vainfo &> /dev/null; then
            VAAPI_INFO=$(vainfo --display drm --device "$device_to_test" 2>/dev/null | grep -i "VAProfile" | head -2)
            if [ -n "$VAAPI_INFO" ]; then
                box_echo "VAAPI capabilities detected:"
                echo "$VAAPI_INFO" | while read line; do box_echo "  $line"; done
            fi
        fi
    else
        box_echo "No Intel GPU detected in PCI devices."
    fi
else
    box_echo "Intel GPU is not available. /dev/dri does not exist."
fi
box_echo "--------------------------------------------------------------------------";

box_echo "Checking for AMD GPU availability..."
export GPU_AVAILABLE_AMD="false"
if [ -d /dev/dri ]; then
    # Check for AMD GPU
    AMD_GPU=$(lspci | grep -iE 'Display|VGA|3D' | grep -iE ' AMD| ATI| Radeon')
    if [ -n "$AMD_GPU" ]; then
        export GPU_AVAILABLE_AMD="true"
        box_echo "AMD GPU detected: $AMD_GPU"
        if [ -n "$GPU_DEVICE_AMD" ]; then
            box_echo "AMD GPU device: $GPU_DEVICE_AMD"
        else
            box_echo "AMD GPU device: /dev/dri/renderD128 (default fallback)"
        fi
        box_echo "AMD hardware acceleration (VAAPI) is available."
        
        # Test VAAPI capability for AMD
        device_to_test="${GPU_DEVICE_AMD:-/dev/dri/renderD128}"
        if command -v vainfo &> /dev/null; then
            VAAPI_INFO=$(vainfo --display drm --device "$device_to_test" 2>/dev/null | grep -i "VAProfile" | head -2)
            if [ -n "$VAAPI_INFO" ]; then
                box_echo "VAAPI capabilities detected:"
                echo "$VAAPI_INFO" | while read line; do box_echo "  $line"; done
            fi
        fi
    else
        box_echo "No AMD GPU detected in PCI devices."
    fi
else
    box_echo "AMD GPU is not available. /dev/dri does not exist."
fi
box_echo "--------------------------------------------------------------------------";

# Check user group memberships for GPU access
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

# Set default values for PUID and PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}
APPUSER=appuser
APPGROUP=appuser

# Create the appuser group and user if they don't exist
# Check if a group with the supplied PGID already exists
if getent group "$PGID" > /dev/null 2>&1; then
    # Use the existing group name
    APPGROUP=$(getent group "$PGID" | cut -d: -f1)
    box_echo "Group with GID '$PGID' already exists, using group '$APPGROUP'"
else
    # Create the appuser group if it doesn't exist
    box_echo "Creating group '$APPGROUP' with GID '$PGID'"
    groupadd -g "$PGID" "$APPGROUP"
fi

# Check if a user with the supplied PUID already exists
if getent passwd "$PUID" > /dev/null 2>&1; then
    # Use the existing user name
    APPUSER=$(getent passwd "$PUID" | cut -d: -f1)
    box_echo "User with UID '$PUID' already exists, using user '$APPUSER'"
else
    # Create the appuser user if it doesn't exist
    box_echo "Creating user '$APPUSER' with UID '$PUID'"
    useradd -u "$PUID" -g "$PGID" -m "$APPUSER"
fi

# Add appuser to GPU-related groups for hardware acceleration access
box_echo "Adding user '$APPUSER' to GPU-related groups for hardware acceleration..."
groups_added=""

# Add to render group (for GPU access)
if getent group render > /dev/null 2>&1; then
    usermod -a -G render "$APPUSER" 2>/dev/null && groups_added="$groups_added render"
fi

# Add to video group (for video device access)
if getent group video > /dev/null 2>&1; then
    usermod -a -G video "$APPUSER" 2>/dev/null && groups_added="$groups_added video"
fi

# Add to common GPU device group IDs (226, 128, 129) if they exist
for gid in 226 128 129; do
    if getent group "$gid" > /dev/null 2>&1; then
        group_name=$(getent group "$gid" | cut -d: -f1)
        usermod -a -G "$group_name" "$APPUSER" 2>/dev/null && groups_added="$groups_added $group_name($gid)"
    fi
done

if [ -n "$groups_added" ]; then
    box_echo "Added user '$APPUSER' to GPU groups:$groups_added"
else
    box_echo "No additional GPU groups found or user already has access"
fi

# Write GPU detection results to .env file for the application to use
box_echo "Writing GPU detection results to '$APP_DATA_DIR/.env' file..."
ENV_FILE="$APP_DATA_DIR/.env"

# Create or update the .env file with GPU variables
{
    # Remove any existing GPU-related variables from .env file if it exists
    if [ -f "$ENV_FILE" ]; then
        grep -v "^GPU_AVAILABLE_\|^GPU_DEVICE_" "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
    fi
    
    # Add GPU detection results
    echo "# GPU Detection Results - Auto-generated by entrypoint.sh"
    echo "GPU_AVAILABLE_NVIDIA=$GPU_AVAILABLE_NVIDIA"
    echo "GPU_AVAILABLE_INTEL=$GPU_AVAILABLE_INTEL"
    echo "GPU_AVAILABLE_AMD=$GPU_AVAILABLE_AMD"
    
    # Add device paths if they exist
    [ -n "$GPU_DEVICE_NVIDIA" ] && echo "GPU_DEVICE_NVIDIA=$GPU_DEVICE_NVIDIA"
    [ -n "$GPU_DEVICE_INTEL" ] && echo "GPU_DEVICE_INTEL=$GPU_DEVICE_INTEL"
    [ -n "$GPU_DEVICE_AMD" ] && echo "GPU_DEVICE_AMD=$GPU_DEVICE_AMD"
    
} >> "$ENV_FILE"

box_echo "GPU environment variables written to .env file"

# Set permissions for appuser on /app and /data directories
box_echo "Changing the owner of '/app' and '$APP_DATA_DIR' directories to '$APPUSER'"
chmod -R 750 /app
chown -R "$APPUSER":"$APPGROUP" /app
chown -R "$APPUSER":"$APPGROUP" "$APP_DATA_DIR"
box_echo "--------------------------------------------------------------------------";

# # Create a temporary directory to download trailers to
# mkdir -p /app/tmp

# Switch to the non-root user and execute the command
box_echo "Switching to user '$APPUSER' and starting the application"

# Get the shell for the user
USER_SHELL=$(getent passwd "$APPUSER" | cut -d: -f7)

# Check if the shell is valid and executable
if [[ -x "$USER_SHELL" && "$USER_SHELL" != "/usr/sbin/nologin" && "$USER_SHELL" != "/bin/false" ]]; then
    exec su "$APPUSER" -c /app/scripts/start.sh
else
    # If the shell is invalid or missing, use a fallback shell (Ex: user www-data doesn't have a shell)
    box_echo "User shell is invalid or missing, using fallback shell: '/bin/bash'"
    exec su "$APPUSER" -s /bin/bash -c /app/scripts/start.sh
fi

# DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
# Instead add them in the start.sh script
