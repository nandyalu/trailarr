#!/bin/bash

# THIS SCRIPT WILL BE RUN AS THE ROOT USER IN THE CONTAINER BEFORE APP STARTS
# This is the main entrypoint script that orchestrates the container startup process
# by calling modular components for better maintainability.

# Source modular entrypoint components
source /app/scripts/entrypoint/banner.sh
source /app/scripts/entrypoint/timezone.sh
source /app/scripts/entrypoint/directories.sh
source /app/scripts/entrypoint/update_ytdlp.sh
source /app/scripts/entrypoint/gpu_detection.sh
source /app/scripts/entrypoint/user_groups.sh
source /app/scripts/entrypoint/env_file.sh
source /app/scripts/entrypoint/startup.sh

# Execute startup sequence
display_startup_banner
configure_timezone
setup_directories
check_and_update_ytdlp
setup_gpu_detection
setup_user_and_groups
configure_gpu_groups
generate_env_file
finalize_user_setup
start_application

# DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
# Instead add them in the start.sh script
