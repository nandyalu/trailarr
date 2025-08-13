#!/bin/bash

# Common logging functions for Trailarr bare metal installation
# Provides both terminal output (user-friendly) and file logging (verbose)

# Initialize logging - call this first in the main script
init_logging() {
    # Set log file in current directory where script is being run
    INSTALL_LOG_FILE="$(pwd)/trailarr_install.log"
    
    # Create/truncate log file
    cat > "$INSTALL_LOG_FILE" << EOF
Trailarr Bare Metal Installation Log
====================================
Started: $(date)
Run from: $(pwd)
User: $(whoami)
Sudo User: ${SUDO_USER:-N/A}

EOF
    
    # Log environment info
    {
        echo "System Information:"
        echo "  OS: $(lsb_release -d 2>/dev/null | cut -d: -f2 | xargs || echo "Unknown")"
        echo "  Kernel: $(uname -r)"
        echo "  Architecture: $(uname -m)"
        echo ""
    } >> "$INSTALL_LOG_FILE"
    
    export INSTALL_LOG_FILE
}

# Function to write to log file only
log_to_file() {
    local message="$1"
    if [ -n "$INSTALL_LOG_FILE" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$INSTALL_LOG_FILE"
    fi
}

# Function to write verbose command output to log file
log_command_output() {
    local command="$1"
    local output="$2"
    if [ -n "$INSTALL_LOG_FILE" ]; then
        {
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Command: $command"
            echo "Output:"
            echo "$output"
            echo "---"
        } >> "$INSTALL_LOG_FILE"
    fi
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Spinner state
SPINNER=( '-' '\' '|' '/' )
SPINNER_PID=0
SPINNER_MSG=""
SPINNER_COLOR=""
SPINNER_ACTIVE=false

# Cleanup function to kill spinner on exit or interrupt
cleanup_spinner() {
    if $SPINNER_ACTIVE && [[ $SPINNER_PID -ne 0 ]]; then
        # Check if process is running before kill/wait
        if kill -0 "$SPINNER_PID" 2>/dev/null; then
            kill "$SPINNER_PID" 2>/dev/null
            # Wait for spinner to exit, but don't hang if already dead
            timeout 2s wait "$SPINNER_PID" 2>/dev/null || true
        fi
        SPINNER_PID=0
        SPINNER_ACTIVE=false
    fi
}

# Trap signals to ensure spinner is cleaned up
trap cleanup_spinner EXIT INT TERM

# Function to print colored output to terminal and log to file
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
    log_to_file "INFO: $message"
}

# Function to show start message with spinner (user sees spinner, file gets detailed log)
start_message() {
    SPINNER_COLOR="$1"
    SPINNER_MSG="$2"
    SPINNER_ACTIVE=true
    
    # Log start to file
    log_to_file "START: $SPINNER_MSG"
    
    # Start spinner for user
    (
        i=0
        while true; do
            printf "\r${SPINNER_COLOR}${SPINNER[i]} $SPINNER_MSG${NC}   "
            i=$(( (i + 1) % 4 ))
            sleep 0.2
        done
    ) &
    SPINNER_PID=$!
}

# Function to stop spinner and show end message
end_message() {
    local color_code="$1"
    local message="$2"
    
    # Log completion to file
    log_to_file "END: $message"
    
    if $SPINNER_ACTIVE; then
        cleanup_spinner
        # Pad with spaces to overwrite longer spinner line
        local pad_length=$(( ${#SPINNER_MSG} - ${#message} + 10 ))
        local padding=""
        if (( pad_length > 0 )); then
            padding=$(printf '%*s' "$pad_length" "")
        fi
        printf "\r${color_code}$message${NC}${padding}\n"
    else
        # No spinner was started, just print the message
        printf "${color_code}$message${NC}\n"
    fi
    echo ""
}

# Function to run a command with output logging (user sees minimal output, file gets all output)
run_logged_command() {
    local description="$1"
    local command="$2"
    local success_msg="$3"
    local error_msg="$4"
    
    log_to_file "COMMAND START: $description - Running: $command"
    
    # Run command and capture output
    local output
    local exit_code
    output=$(eval "$command" 2>&1)
    exit_code=$?
    
    # Log the full output
    log_command_output "$command" "$output"
    
    if [ $exit_code -eq 0 ]; then
        log_to_file "COMMAND SUCCESS: $description"
        return 0
    else
        log_to_file "COMMAND FAILED: $description (exit code: $exit_code)"
        return $exit_code
    fi
}

# Function to update or add environment variable to .env file (only writes once)
update_env_var() {
    local var_name="$1"
    local var_value="$2"
    local env_file="$3"
    
    log_to_file "ENV UPDATE: Setting $var_name in $env_file"
    
    # Create file if it doesn't exist
    touch "$env_file"
    
    # Check if variable already exists with the same value
    if grep -q "^${var_name}=${var_value}$" "$env_file" 2>/dev/null; then
        log_to_file "ENV SKIP: $var_name already set to correct value"
        return 0
    fi
    
    # Remove existing entry if it exists
    if grep -q "^${var_name}=" "$env_file" 2>/dev/null; then
        grep -v "^${var_name}=" "$env_file" > "${env_file}.tmp"
        mv "${env_file}.tmp" "$env_file"
        log_to_file "ENV REPLACE: Updated existing $var_name"
    else
        log_to_file "ENV ADD: Adding new $var_name"
    fi
    
    # Add new entry
    echo "${var_name}=${var_value}" >> "$env_file"
    log_to_file "ENV SET: $var_name=${var_value}"
}

# Function to display final log file location
show_log_location() {
    print_message "$GREEN" ""
    print_message "$GREEN" "📄 Complete installation log saved to: $INSTALL_LOG_FILE"
    print_message "$GREEN" "   Use this file for troubleshooting or debugging if needed."
    print_message "$GREEN" ""
}