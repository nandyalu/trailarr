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


# Detect GPU devices before checking for availability
detect_gpu_devices

# Check for NVIDIA GPU
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

# Check for Intel GPU
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
            VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_INTEL" 2>/dev/null | grep -i "VAProfile" | head -2)
            if [ -n "$VAAPI_INFO" ]; then
                box_echo "VAAPI capabilities detected:"
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

# Check for AMD GPU
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
            VAAPI_INFO=$(vainfo --display drm --device "$GPU_DEVICE_AMD" 2>/dev/null | grep -i "VAProfile" | head -2)
            if [ -n "$VAAPI_INFO" ]; then
                box_echo "VAAPI capabilities detected:"
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

# Identify GPU-related groups for hardware acceleration access
box_echo "Identifying GPU-related groups for hardware acceleration..."
gpu_groups=()
groups_found=""

# Function to check if group is already in the array
group_exists() {
    local group_to_check="$1"
    local group
    for group in "${gpu_groups[@]}"; do
        if [ "$group" = "$group_to_check" ]; then
            return 0
        fi
    done
    return 1
}

# Check for render group (for GPU access)
if getent group render > /dev/null 2>&1; then
    gpu_groups+=("render")
    groups_found="$groups_found render"
fi

# Check for video group (for video device access)
if getent group video > /dev/null 2>&1; then
    gpu_groups+=("video")
    groups_found="$groups_found video"
fi

# Check for specific DRI device groups for detected Intel/AMD GPUs
if [ -n "$GPU_DEVICE_INTEL" ] || [ -n "$GPU_DEVICE_AMD" ]; then
    box_echo "Checking groups for detected Intel/AMD GPU devices..."
    
    # Check Intel GPU device group if detected
    if [ -n "$GPU_DEVICE_INTEL" ] && [ -e "$GPU_DEVICE_INTEL" ]; then
        intel_gid=$(stat -c '%g' "$GPU_DEVICE_INTEL" 2>/dev/null)
        if [[ -n "$intel_gid" ]]; then
            if getent group "$intel_gid" > /dev/null 2>&1; then
                intel_group_name=$(getent group "$intel_gid" | cut -d: -f1)
            else
                intel_group_name="gpuintel"
                box_echo "Creating group '$intel_group_name' with GID '$intel_gid'"
                groupadd -g "$intel_gid" "$intel_group_name"
            fi
            box_echo "Adding user '$APPUSER' to group '$intel_group_name'"
            usermod -aG "$intel_group_name" "$APPUSER"
            gpu_groups+=("$intel_group_name")
            groups_found="$groups_found $intel_group_name($intel_gid)"
        fi
    fi
    
    # Check AMD GPU device group if detected
    if [ -n "$GPU_DEVICE_AMD" ] && [ -e "$GPU_DEVICE_AMD" ]; then
        amd_gid=$(stat -c '%g' "$GPU_DEVICE_AMD" 2>/dev/null)
        if [[ -n "$amd_gid" ]]; then
            if getent group "$amd_gid" > /dev/null 2>&1; then
                amd_group_name=$(getent group "$amd_gid" | cut -d: -f1)
            else
                amd_group_name="gpuamd"
                box_echo "Creating group '$amd_group_name' with GID '$amd_gid'"
                groupadd -g "$amd_gid" "$amd_group_name"
            fi
            box_echo "Found AMD GPU device group '$amd_group_name' (GID: $amd_gid)"
            # Check if group is not already in the list
            if ! group_exists "$amd_group_name"; then
                gpu_groups+=("$amd_group_name")
            fi
            groups_found="$groups_found $amd_group_name($amd_gid)"
        fi
    fi
else
    box_echo "No Intel or AMD GPU devices detected for group assignment"
fi

# Check for common GPU device group IDs (226, 128, 129) if they exist
for gid in 226 128 129; do
    if getent group "$gid" > /dev/null 2>&1; then
        group_name=$(getent group "$gid" | cut -d: -f1)
        # Check if group is not already in the list
        if ! group_exists "$group_name"; then
            gpu_groups+=("$group_name")
            groups_found="$groups_found $group_name($gid)"
        fi
    fi
done

if [ -n "$groups_found" ]; then
    box_echo "GPU groups identified for gosu:$groups_found"
else
    box_echo "No GPU groups found for hardware acceleration"
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

box_echo "Ensuring appuser has access to GPU-related groups..."

group_index=1
for group in "${gpu_groups[@]}"; do
    group_entry=$(getent group "$group")
    if [ -n "$group_entry" ]; then
        group_name=$(echo "$group_entry" | cut -d: -f1)
        group_gid=$(echo "$group_entry" | cut -d: -f3)
    else
        # Fallback: assume $group is a GID and create a synthetic name
        group_gid="$group"
        group_name="gpugroup${group_index}"
        group_index=$((group_index + 1))
        box_echo "Group name not found for GID '$group_gid', creating fallback group '$group_name'"
        groupadd -g "$group_gid" "$group_name"
    fi

    # Create group inside container if it doesn't exist
    if ! getent group "$group_gid" > /dev/null 2>&1; then
        box_echo "Creating group '$group_name' with GID '$group_gid'"
        groupadd -g "$group_gid" "$group_name"
    fi
    # Add appuser to the group
    box_echo "Adding user '$APPUSER' to group '$group_name'"
    usermod -aG "$group_name" "$APPUSER"
    box_echo "appuser groups: $(id -Gn appuser)"
done


# Switch to the non-root user and execute the command
box_echo "Switching to user '$APPUSER' and starting the application"

# Build the gosu command with GPU groups
if [ ${#gpu_groups[@]} -gt 0 ]; then
    # Join the groups with commas for gosu's --groups parameter
    gpu_groups_str=$(IFS=','; echo "${gpu_groups[*]}")
    box_echo "Starting application as '$APPUSER' with GPU groups: '$gpu_groups_str'"
    exec gosu "$APPUSER" /usr/bin/env /app/scripts/start.sh
else
    box_echo "Starting application as '$APPUSER'"
    exec gosu "$APPUSER" /usr/bin/env /app/scripts/start.sh
fi

# DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
# Instead add them in the start.sh script
