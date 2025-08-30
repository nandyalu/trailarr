#!/bin/bash

# This script updates the youtube-dl-python (yt-dlp) package to the latest version
# if env variable YTDLP_UPDATE is set to true

# Check the current version of yt-dlp and display it
if [ "$YTDLP_UPDATE" = true ]; then
    uv pip install --no-cache --native-tls --system --upgrade yt-dlp
fi

#!/bin/bash

# Source the box_echo function
source /app/scripts/box_echo.sh

# Function to check and update yt-dlp
check_and_update_ytdlp() {
    local env_file="$APP_DATA_DIR/.env"

    box_echo "Running 'yt-dlp' update script..."
    # Check the version of yt-dlp and store it in a global environment variable
    YTDLP_VERSION=$(yt-dlp --version)
    export YTDLP_VERSION
    box_echo "Current version of yt-dlp: $YTDLP_VERSION"

    # Check if UPDATE_YTDLP is set in the environment variables
    if [ -z "$UPDATE_YTDLP" ]; then
        # UPDATE_YTDLP is not set in the environment variables
        
        # checking the .env file
        if [ ! -f "$env_file" ]; then
            # No .env file found in $APP_DATA_DIR
            box_echo "UPDATE_YTDLP is not set. Skipping yt-dlp update."
            box_echo "--------------------------------------------------------------------------";
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
        uv pip install --no-cache --native-tls --system --upgrade yt-dlp[default,curl-cffi] 2>/dev/null

        # Check the version of yt-dlp and store it in a global environment variable
        YTDLP_VERSION=$(yt-dlp --version)
        export YTDLP_VERSION
        box_echo "yt-dlp has been updated to the latest version: $YTDLP_VERSION"
    else
        box_echo "UPDATE_YTDLP is not set to True. No action taken."
    fi
    box_echo "--------------------------------------------------------------------------";
}

# Main script
