#!/bin/bash

# User and group management for the container
setup_user_and_groups() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh
    
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

    # Export these variables for use in other scripts
    export APPUSER
    export APPGROUP
    export PUID
    export PGID
}

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

# Configure GPU groups for hardware acceleration
configure_gpu_groups() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh
    
    # Identify GPU-related groups for hardware acceleration access
    box_echo "Identifying GPU-related groups for hardware acceleration..."
    gpu_groups=()
    groups_found=""

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

    # Export gpu_groups array for use in other scripts
    export gpu_groups
}

# Add user to GPU groups and set permissions
finalize_user_setup() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh
    
    # Set permissions for appuser on /app and /data directories
    box_echo "Changing the owner of '/app' and '$APP_DATA_DIR' directories to '$APPUSER'"
    chmod -R 750 /app
    chown -R "$APPUSER":"$APPGROUP" /app
    chown -R "$APPUSER":"$APPGROUP" "$APP_DATA_DIR"
    box_echo "--------------------------------------------------------------------------";

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
}
