#!/bin/bash

# Source the box_echo function
source /app/scripts/box_echo.sh

# Function to check and update yt-dlp
check_and_update() {
    local local_appdata_dir=$1
    local env_file="$local_appdata_dir/.env"

    # Check if UPDATE_YTDLP is set in the environment variables
    if [ -z "$UPDATE_YTDLP" ]; then
        # UPDATE_YTDLP is not set in the environment variables
        
        # checking the .env file
        if [ ! -f "$env_file" ]; then
            # No .env file found in $local_appdata_dir
            box_echo "UPDATE_YTDLP is not set. Skipping yt-dlp update."
            return
        fi

        # Load environment variables from the .env file
        set -a
        source "$env_file"
        set +a
    fi

    # Convert UPDATE_YTDLP to lowercase for case-insensitive comparison
    update_ytdlp_lower=$(echo "$UPDATE_YTDLP" | tr '[:upper:]' '[:lower:]')

    if [ "$update_ytdlp_lower" == "true" ] || [ "$update_ytdlp_lower" == "1" ]; then
        box_echo "UPDATE_YTDLP is set to True. Installing the latest version of yt-dlp..."
        pip install --upgrade yt-dlp[default]
        
        # Check the version of yt-dlp and store it in a global environment variable
        YTDLP_VERSION=$(yt-dlp --version)
        export YTDLP_VERSION
        box_echo "yt-dlp has been updated to the latest version: $YTDLP_VERSION"
    else
        box_echo "UPDATE_YTDLP is not set to True. No action taken."
    fi
}

# Main script
box_echo "Running 'yt-dlp' update script..."
# Check the version of yt-dlp and store it in a global environment variable
YTDLP_VERSION=$(yt-dlp --version)
export YTDLP_VERSION
box_echo "Current version of yt-dlp: $YTDLP_VERSION"
if [ "$#" -ne 1 ]; then
    box_echo "Usage: check_and_update.sh <local_appdata_dir>"
    exit 1
fi

local_appdata_dir=$1
check_and_update "$local_appdata_dir"