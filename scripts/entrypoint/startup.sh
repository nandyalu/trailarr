#!/bin/bash

# Start the application as the non-root user
start_application() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh
    
    # Switch to the non-root user and execute the command
    box_echo "Switching to user '$APPUSER' and starting the application"

    # Build the gosu command with GPU groups
    if [ ${#gpu_groups[@]} -gt 0 ]; then
        # Join the groups with commas for gosu's --groups parameter
        gpu_groups_str=$(IFS=','; echo "${gpu_groups[*]}")
        box_echo "Starting application as '$APPUSER' with GPU groups: '$gpu_groups_str'"
    else
        box_echo "Starting application as '$APPUSER'"
    fi
    exec gosu "$APPUSER" /usr/bin/env /app/scripts/start.sh

    # DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
    # Instead add them in the start.sh script
}
