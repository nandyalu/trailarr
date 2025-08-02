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

box_echo "Checking for NVIDIA GPU availability..."
# Check for NVIDIA GPU
export NVIDIA_GPU_AVAILABLE="false"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        box_echo "NVIDIA GPU is available."
        export NVIDIA_GPU_AVAILABLE="true"
    else
        box_echo "NVIDIA GPU is not available."
    fi
else
    box_echo "nvidia-smi command not found. NVIDIA GPU not detected."
fi
box_echo "--------------------------------------------------------------------------";

# Check if /dev/dri exists and check for Intel/AMD GPU
box_echo "Checking for Intel GPU availability..."
export QSV_GPU_AVAILABLE="false"
if [ -d /dev/dri ]; then
    # Check for Intel GPU
    if ls /dev/dri | grep -q "renderD"; then
        # Intel QSV might be available. Further check for Intel-specific devices
        if lspci | grep -iE 'Display|VGA' | grep -i 'Intel' > /dev/null 2>&1; then
            export QSV_GPU_AVAILABLE="true"
            box_echo "Intel GPU detected. Intel QSV is likely available."
        else
            box_echo "No Intel GPU detected. Intel QSV is not available."
        fi
    else
        box_echo "Intel QSV not detected. No renderD devices found in /dev/dri."
    fi
else
    box_echo "Intel QSV is not available. /dev/dri does not exist."
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

# Set permissions for appuser on /app and /data directories
box_echo "Changing the owner of '/app' and '$APP_DATA_DIR' directories to '$APPUSER'"
chmod -R 750 /app
chown -R "$APPUSER":"$APPGROUP" /app
chown -R "$APPUSER":"$APPGROUP" "$APP_DATA_DIR"
box_echo "--------------------------------------------------------------------------";

# Grant access to video hardware if /dev/dri exists
if [ -d /dev/dri ]; then
    box_echo "Hardware acceleration device found at /dev/dri"
    RENDER_GID=$(stat -c "%g" /dev/dri/render* | head -n 1)
    if [ -n "$RENDER_GID" ]; then
        RENDER_GROUP=$(getent group "$RENDER_GID" | cut -d: -f1)
        if [ -z "$RENDER_GROUP" ]; then
            RENDER_GROUP="render"
            box_echo "Creating group '$RENDER_GROUP' with GID '$RENDER_GID'"
            groupadd -g "$RENDER_GID" "$RENDER_GROUP"
        else
            box_echo "Group '$RENDER_GROUP' with GID '$RENDER_GID' already exists"
        fi
        box_echo "Adding user '$APPUSER' to group '$RENDER_GROUP'"
        usermod -a -G "$RENDER_GROUP" "$APPUSER"
    else
        box_echo "Could not determine GID of render device. Hardware acceleration might not work."
    fi
else
    box_echo "No hardware acceleration device found at /dev/dri"
fi
box_echo "--------------------------------------------------------------------------";

# # Create a temporary directory to download trailers to
# mkdir -p /app/tmp

# Switch to the non-root user and execute the command
box_echo "Switching to user '$APPUSER' and starting the application"

exec gosu "$APPUSER" /usr/bin/env /app/scripts/start.sh

# DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
# Instead add them in the start.sh script
