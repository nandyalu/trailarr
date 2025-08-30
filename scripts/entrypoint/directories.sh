#!/bin/bash

# Setup directories and handle database migration
setup_directories() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh
    
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
}
