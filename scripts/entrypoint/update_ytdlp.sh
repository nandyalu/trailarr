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
        # Convert YTDLP_NIGHTLY to lowercase for case-insensitive comparison
        ytdlp_nightly_lower=$(echo "$YTDLP_NIGHTLY" | tr '[:upper:]' '[:lower:]')

        if [ "$ytdlp_nightly_lower" == "true" ] || [ "$ytdlp_nightly_lower" == "1" ]; then
            box_echo "YTDLP_NIGHTLY is set to True. Installing the latest nightly build of yt-dlp..."
            uv pip install --no-cache --native-tls --system --upgrade --force-reinstall \
                "yt-dlp[default,curl-cffi] @ https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp.tar.gz" 2>/dev/null
        else
            # Nightly versions have 4 date segments (e.g. 2026.06.09.185432) vs 3
            # for stable (2026.03.17). --upgrade alone won't downgrade a nightly,
            # so force-reinstall when switching back to stable.
            version_dots=$(echo "$YTDLP_VERSION" | tr -cd '.' | wc -c)
            if [ "$version_dots" -gt 2 ]; then
                box_echo "Nightly build detected — force-reinstalling stable version of yt-dlp..."
                force_flag="--force-reinstall"
            else
                box_echo "UPDATE_YTDLP is set to True. Installing the latest stable version of yt-dlp..."
                force_flag=""
            fi
            uv pip install --no-cache --native-tls --system --upgrade $force_flag yt-dlp[default,curl-cffi] 2>/dev/null
        fi

        # Check the version of yt-dlp and store it in a global environment variable
        YTDLP_VERSION=$(yt-dlp --version)
        export YTDLP_VERSION
        box_echo "yt-dlp has been updated to version: $YTDLP_VERSION"
    else
        box_echo "UPDATE_YTDLP is not set to True. No action taken."
    fi
    box_echo "--------------------------------------------------------------------------";
}

# Main script
