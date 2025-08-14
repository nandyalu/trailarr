#!/bin/bash

# Common logging functions for Trailarr bare metal installation
# Provides both terminal output (user-friendly) and file logging (verbose)
# Uses tput for better terminal control and clean message display

# Initialize logging - call this first in the main script
init_logging() {
    # Set log file in /tmp directory which is always writable
    INSTALL_LOG_FILE="/tmp/trailarr_install.log"
    
    # Create/truncate log file with proper permissions
    cat > "$INSTALL_LOG_FILE" << EOF
Trailarr Bare Metal Installation Log
====================================
Started: $(date)
Run from: $(pwd)
User: $(whoami)
Sudo User: ${SUDO_USER:-N/A}

EOF
    
    # Set proper permissions for the log file (world-writable since multiple users need access)
    chmod 666 "$INSTALL_LOG_FILE"
    
    # Log environment info
    {
        echo "System Information:"
        echo "  OS: $(lsb_release -d 2>/dev/null | cut -d: -f2 | xargs || echo "Unknown")"
        echo "  Kernel: $(uname -r)"
        echo "  Architecture: $(uname -m)"
        echo ""
    } >> "$INSTALL_LOG_FILE"
    
    export INSTALL_LOG_FILE
    
    # Initialize tput capabilities
    TERM_COLS=$(tput cols 2>/dev/null || echo 80)
    export TERM_COLS
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

# Progress state
PROGRESS_ACTIVE=false
PROGRESS_MSG=""
PROGRESS_COLOR=""
PROGRESS_CHARS=( '⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏' )
PROGRESS_INDEX=0

# Global variable to store number of temp lines
TEMP_STATUS_LINES=0

# Function to clean the current line using tput
clear_line() {
    tput cr 2>/dev/null || printf "\r"
    tput el 2>/dev/null || printf "\033[K"
    # Move cursor up and clear each temp line
    for ((i=0; i<TEMP_STATUS_LINES; i++)); do
        tput cuu1   # Move cursor up one line
        tput el     # Clear the line
    done
    TEMP_STATUS_LINES=0
}

# Function to print colored output to terminal and log to file
print_message() {
    local color=$1
    local message=$2
    clear_line
    # Clear any active progress display
    # if $PROGRESS_ACTIVE; then
    #     clear_line
    # fi
    
    # Print the message
    echo " "
    printf "${color}%s${NC}\n" "$message"
    log_to_file "INFO: $message"
}

# Function to show start message with progress animation
start_message() {
    PROGRESS_COLOR="$1"
    PROGRESS_MSG="$2"
    PROGRESS_ACTIVE=true
    PROGRESS_INDEX=0
    
    # Log start to file
    log_to_file "START: $PROGRESS_MSG"

    # Show initial progress message
    printf "${PROGRESS_COLOR}%s %s${NC}" "${PROGRESS_CHARS[0]}" "$PROGRESS_MSG"
}

# Function to update progress animation (call this in loops for long operations)
update_progress() {
    if $PROGRESS_ACTIVE; then
        PROGRESS_INDEX=$(( (PROGRESS_INDEX + 1) % ${#PROGRESS_CHARS[@]} ))
        clear_line
        printf "${PROGRESS_COLOR}%s %s${NC}" "${PROGRESS_CHARS[PROGRESS_INDEX]}" "$PROGRESS_MSG"
    fi
}

# Function to stop progress and show end message
end_message() {
    local color_code="$1"
    local message="$2"
    
    # Log completion to file
    log_to_file "END: $message"
    
    clear_line
    if $PROGRESS_ACTIVE; then
        PROGRESS_ACTIVE=false
    fi
    
    # Print the final message
    printf "${color_code}%s${NC}\n" "$message"
    echo ""
}

# Function to show temporary status that will be replaced
show_temp_status() {
    local color="$1"
    local message="$2"
    
    clear_line
    # printf "${color}%s${NC}" "====> $message"
    # Prepend "===> " to each line and print
    while IFS= read -r line; do
        printf "${color}===> %s${NC}\n" "$line"
    done <<< "$(echo -e "$message")"
    log_to_file "TEMP: $message"
    # Count lines in message
    TEMP_STATUS_LINES=$(echo -e "$message" | wc -l)
}

# Function to show permanent status (like end_message but without clearing progress)
show_status() {
    local color="$1"
    local message="$2"
    
    clear_line
    printf "${color}%s${NC}\n" "$message"
    log_to_file "STATUS: $message"
}

# Function to run a command with output logging and progress animation
run_logged_command() {
    local description="$1"
    local command="$2"
    local success_msg="$3"
    local error_msg="$4"
    
    log_to_file "COMMAND START: $description - Running: $command"
    
    # Start progress animation if not already active
    local was_active=$PROGRESS_ACTIVE
    if ! $PROGRESS_ACTIVE; then
        start_message "$BLUE" "$description"
    fi
    
    # Run command and capture output
    local output
    local exit_code
    local temp_output="/tmp/cmd_output_$$"
    
    # Run command in background and capture output
    (eval "$command" > "$temp_output" 2>&1) &
    local cmd_pid=$!
    
    # Update progress while command runs
    while kill -0 $cmd_pid 2>/dev/null; do
        if $PROGRESS_ACTIVE; then
            update_progress
        fi
        sleep 0.1
    done
    
    # Wait for command to complete and get exit code
    wait $cmd_pid
    exit_code=$?
    
    # Read the output
    if [ -f "$temp_output" ]; then
        output=$(cat "$temp_output")
        rm -f "$temp_output"
    fi
    
    # Log the full output
    log_command_output "$command" "$output"
    
    if [ $exit_code -eq 0 ]; then
        log_to_file "COMMAND SUCCESS: $description"
        if ! $was_active; then
            end_message "$GREEN" "✓ $description completed"
        fi
        return 0
    else
        log_to_file "COMMAND FAILED: $description (exit code: $exit_code)"
        if ! $was_active; then
            end_message "$RED" "✗ $description failed"
        fi
        return $exit_code
    fi
}

# Function to run a simple command with just progress indication
run_command_with_progress() {
    local description="$1"
    local command="$2"
    
    log_to_file "COMMAND START: $description - Running: $command"
    
    # Show progress
    start_message "$BLUE" "$description"
    
    # Run command and capture output
    local output
    local exit_code
    output=$(eval "$command" 2>&1)
    exit_code=$?
    
    # Log the full output
    log_command_output "$command" "$output"
    
    if [ $exit_code -eq 0 ]; then
        log_to_file "COMMAND SUCCESS: $description"
        end_message "$GREEN" "✓ $description"
        return 0
    else
        log_to_file "COMMAND FAILED: $description (exit code: $exit_code)"
        end_message "$RED" "✗ $description failed"
        return $exit_code
    fi
}

# Function to update or add environment variable to .env file (only writes once)
update_env_var() {
    local var_name="$1"
    local var_value="$2"
    local env_file="$3"
    
    log_to_file "ENV UPDATE: Setting $var_name in $env_file"
    
    # Create file if it doesn't exist with proper permissions
    if [ ! -f "$env_file" ]; then
        # Create directory if it doesn't exist
        mkdir -p "$(dirname "$env_file")"
        
        # Create file with proper ownership for trailarr user
        touch "$env_file"
        
        # Set proper ownership if we have sudo privileges and trailarr user exists
        if [ "$EUID" -eq 0 ] && getent passwd trailarr > /dev/null 2>&1; then
            chown trailarr:trailarr "$env_file"
            log_to_file "ENV CREATE: Created $env_file with trailarr ownership"
        elif [ "$EUID" -ne 0 ] && [ -f "$env_file" ]; then
            # If we're not root but file exists, check if we can write to it
            if [ ! -w "$env_file" ]; then
                log_to_file "ENV ERROR: Cannot write to $env_file - permission denied"
                # Try to fix via sudo if available
                if command -v sudo > /dev/null 2>&1 && getent passwd trailarr > /dev/null 2>&1; then
                    sudo chown trailarr:trailarr "$env_file" 2>/dev/null || true
                    log_to_file "ENV FIX: Attempted to fix ownership of $env_file"
                fi
            fi
        fi
    fi
    
    # Ensure we can write to the file before proceeding
    if [ ! -w "$env_file" ]; then
        log_to_file "ENV ERROR: Cannot write to $env_file after creation attempts"
        return 1
    fi
    
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