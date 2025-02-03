#!/bin/sh

# THIS SCRIPT WILL BE RUN AS THE ROOT USER IN THE CONTAINER BEFORE APP STARTS

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
echo "Starting Trailarr container with the following configuration:"
echo "APP_DATA_DIR: ${APP_DATA_DIR}"
echo "PUID: ${PUID}"
echo "PGID: ${PGID}"
echo "TZ: ${TZ}"
echo "-----------------------------------------------------------------";

# Set TimeZone based on env variable
# Print date time before 
echo "Current date time: $(date)"
echo "Setting TimeZone to ${TZ}"
echo $TZ > /etc/timezone && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata
echo "Current date time after tzdate: $(date)"

# Remove trailing slash from APP_DATA_DIR if it exists
export APP_DATA_DIR=$(echo $APP_DATA_DIR | sed 's:/*$::')

# Check if trailarr.db exists in APP_DATA_DIR folder
if [ -f "${APP_DATA_DIR}/trailarr.db" ]; then
    # Do nothing if database file exists in APP_DATA_DIR folder
    echo ""
else
    # Check if trailarr.db exists in /data folder
    if [ -f "/data/trailarr.db" ]; then
        echo "Database file 'trailarr.db' found in '/data' folder"
        echo "Setting 'APP_DATA_DIR' to '/data' folder to prevent data loss"
        export APP_DATA_DIR="/data"
    fi
fi


# Create appdata (default=/data) folder for storing database and other config files
echo "Creating '$APP_DATA_DIR' folder for storing database and other config files"
mkdir -p "${APP_DATA_DIR}/logs" && chmod -R 755 $APP_DATA_DIR
chmod -R 755 /app/assets
mkdir -p /app/tmp && chmod -R 755 /app/tmp

# Check if the appdata folder has .env file and Check if there is a env variable 'UPDATE_YTDLP' set to true
if [ -f "${APP_DATA_DIR}/.env" ]; then
    echo "Found .env file in '$APP_DATA_DIR' folder"
    if [ "$UPDATE_YTDLP" = "true" ]; then
        echo "UPDATE_YTDLP is set to true. Updating .env file with new values"
        pip install yt-dlp --upgrade
    fi
fi

echo "Checking for GPU availability..."
# Check for NVIDIA GPU
export NVIDIA_GPU_AVAILABLE="false"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        echo "NVIDIA GPU is available."
        export NVIDIA_GPU_AVAILABLE="true"
    else
        echo "NVIDIA GPU is not available."
    fi
else
    echo "nvidia-smi command not found."
fi

# Check if /dev/dri exists
export QSV_GPU_AVAILABLE="false"
if [ -d /dev/dri ]; then
    # Check for Intel GPU
    if ls /dev/dri | grep -q "renderD"; then
        # Intel QSV might be available. Further check for Intel-specific devices
        if lspci | grep -iE 'Display|VGA' | grep -i 'Intel'; then
            export QSV_GPU_AVAILABLE="true"
            echo "Intel GPU detected. Intel QSV is likely available."
        else
            echo "No Intel GPU detected. Intel QSV is not available."
        fi
    else
        echo "Intel QSV not detected. No renderD devices found in /dev/dri."
    fi
else
    echo "Intel QSV is not available. /dev/dri does not exist."
fi

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
    echo "Group with GID '$PGID' already exists, using group '$APPGROUP'"
else
    # Create the appuser group if it doesn't exist
    echo "Creating group '$APPGROUP' with GID '$PGID'"
    groupadd -g "$PGID" "$APPGROUP"
fi

# Check if a user with the supplied PUID already exists
if getent passwd "$PUID" > /dev/null 2>&1; then
    # Use the existing user name
    APPUSER=$(getent passwd "$PUID" | cut -d: -f1)
    echo "User with UID '$PUID' already exists, using user '$APPUSER'"
else
    # Create the appuser user if it doesn't exist
    echo "Creating user '$APPUSER' with UID '$PUID'"
    useradd -u "$PUID" -g "$PGID" -m "$APPUSER"
fi

# Set permissions for appuser on /app and /data directories
echo "Changing the owner of '/app' and '$APP_DATA_DIR' directories to '$APPUSER'"
chmod -R 750 /app
chown -R "$APPUSER":"$APPGROUP" /app
chown -R "$APPUSER":"$APPGROUP" "$APP_DATA_DIR"

# # Create a temporary directory to download trailers to
# mkdir -p /app/tmp

# Switch to the non-root user and execute the command
echo "Switching to user '$APPUSER' and starting the application"
exec gosu "$APPUSER" bash -c /app/start.sh

# DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
# Instead add them in the start.sh script
