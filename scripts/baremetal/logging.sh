#!/bin/bash

# Common logging functions for Trailarr bare metal installation
# Provides both terminal output (user-friendly) and file logging (verbose)
# Uses tput for better terminal control and clean message display

# Global variable to store the PID of the spinner process.
SPINNER_PID=""
# Global variable to store the current spinner message.
SPINNER_MSG=""
# Global variable to count the number of messages logged below the spinner.
LOG_COUNT=0
# Global array to store persistent messages as "color:message" strings.
PERSISTENT_MESSAGES=()
# Global variable to store the start time of the current spinner.
START_TIME=""

# --- Color Definitions ---
# These variables map color names to their tput color codes.
# You can use these variables in your function calls for better readability.
BLACK=0
RED=1
GREEN=2
YELLOW=3
BLUE=4
MAGENTA=5
CYAN=6
WHITE=7
NC='\033[0m' # No Color

# Function to clean up the terminal on script exit or interruption.
# This ensures the spinner is stopped and the cursor is visible.
cleanup() {
    # Check if a spinner process exists and is running
    if [ -n "$SPINNER_PID" ] && kill -0 "$SPINNER_PID" 2>/dev/null; then
        # Kill the background spinner process
        kill "$SPINNER_PID" 2>/dev/null
        # Wait for the process to terminate
        wait "$SPINNER_PID" 2>/dev/null
    fi
    # Restore cursor visibility
    tput cnorm
}

# Trap common termination signals and call the cleanup function
trap cleanup INT TERM EXIT

# Function to reset the log counter and persistent message array for a new task.
reset_state() {
    LOG_COUNT=0
    PERSISTENT_MESSAGES=()
    SPINNER_MSG=""
}

# Function to stop the previous spinner gracefully.
# This is an internal helper function.
_finalize_previous_spinner() {
    # Only proceed if a spinner is actually running
    if [ -n "$SPINNER_PID" ] && kill -0 "$SPINNER_PID" 2>/dev/null; then
        # Kill the background spinner process
        kill "$SPINNER_PID" 2> /dev/null
        # Wait for the process to ensure it's terminated
        wait "$SPINNER_PID" 2>/dev/null
        
        # Restore the cursor to the initial saved position (the spinner's line)
        tput rc
        
        # Clear the entire screen from the current cursor position to the end.
        tput ed
        
        # Calculate the final elapsed time
        local final_time=$(( $(date +%s) - START_TIME ))

        # Print a final message for the automatically stopped task.
        local term_width=$(tput cols)
        local msg_core="✓ ${SPINNER_MSG}"
        local final_time_str="(${final_time}s)"
        local line_content="${msg_core} ${final_time_str}"
        local effective_width=$((term_width > 80 ? 80 : term_width))
        local padding=$((effective_width - ${#line_content}))
        
        tput bold; tput smul
        tput setaf "$GREEN"
        echo -n "$msg_core"
        if [ "$padding" -gt 0 ]; then
            printf "%*s" "$padding" " "
        fi
        echo -n "$final_time_str"
        tput sgr0
        
        # Add post-padding to clear the rest of the line if > 80 cols
        local post_padding=$((term_width - effective_width))
        if [ "$post_padding" -gt 0 ]; then
            printf "%*s" "$post_padding" " "
        fi
        echo ""

        # Loop through and print all persistent messages with their stored color
        for p_msg in "${PERSISTENT_MESSAGES[@]}"; do
            local color_code="${p_msg%%:*}"
            local message="${p_msg#*:}"
            tput setaf "$color_code"
            echo "$message"
            tput sgr0
        done
        
        # Show the cursor again
        tput cnorm
        
        # Add a new line to separate tasks cleanly
        echo ""
        
        # Reset state for the next task
        reset_state
    fi
}

# Function to start the spinner animation
# Usage: start_message "Your message here"
start_message() {
    # If a spinner is already running, finalize it before starting a new one
    _finalize_previous_spinner

    # Add a new line to separate tasks
    echo ""

    # Hide the cursor to prevent it from interfering with the spinner
    tput civis

    # Store the message provided as an argument
    SPINNER_MSG="$1"
    
    # An array of spinner characters
    local spinner_chars=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')

    # Get the start time in seconds since the epoch and store it globally
    START_TIME=$(date +%s)
    
    # Save the initial cursor position of the spinner's line
    tput sc
    
    # Run the spinner logic in a background process
    (
        local i=0
        while :
        do
            # Calculate elapsed time in seconds
            local elapsed_time=$(( $(date +%s) - START_TIME ))
            local timer_str="(${elapsed_time}s)"

            # Restore the cursor to the saved spinner position
            tput rc
            
            # Get terminal width for padding
            local term_width=$(tput cols)
            local line_content_core="${spinner_chars[i]} ${SPINNER_MSG}"
            local effective_width=$((term_width > 80 ? 80 : term_width))
            local padding=$((effective_width - ${#line_content_core} - ${#timer_str}))
            
            # Apply bold and underline formatting
            tput bold; tput smul
            tput setaf "$BLUE"
            
            # Print the spinner and message
            echo -n "${line_content_core}"
            
            # Add padding to push the timer to the right
            if [ "$padding" -gt 0 ]; then
                printf "%*s" "$padding" " "
            fi
            
            # Print the timer in a different color
            tput setaf "$BLUE"
            echo -n "${timer_str}"
            tput sgr0
            
            # Add post-padding to clear the rest of the line if > 80 cols
            local post_padding=$((term_width - effective_width))
            if [ "$post_padding" -gt 0 ]; then
                printf "%*s" "$post_padding" " "
            fi
            
            # Move to the next character in the array, looping back to the start
            i=$(( (i+1) % ${#spinner_chars[@]} ))
            
            # Sleep for a short duration to control the speed of the animation
            sleep 0.1
        done
    ) &
    
    # Save the PID of the background process so we can kill it later
    SPINNER_PID=$!
}

# Function to stop the spinner and show a final message
# Usage: stop_spinner "Your message here"
stop_spinner() {
    local msg="$1"
    
    # If a spinner is running, kill it gracefully
    if [ -n "$SPINNER_PID" ] && kill -0 "$SPINNER_PID" 2>/dev/null; then
        # Kill the background spinner process
        kill "$SPINNER_PID" 2> /dev/null
        # Wait for the process to ensure it's terminated
        wait "$SPINNER_PID" 2>/dev/null
    fi
    
    # Restore the cursor to the initial saved position (the spinner's line)
    tput rc
    
    # Clear the entire screen from the current cursor position to the end.
    tput ed
    
    # Calculate the final elapsed time
    local final_time=$(( $(date +%s) - START_TIME ))

    # Print a final message to the terminal with a checkmark.
    local term_width=$(tput cols)
    local msg_core="✓ ${msg}"
    local final_time_str="(${final_time}s)"
    local line_content="${msg_core} ${final_time_str}"
    local effective_width=$((term_width > 80 ? 80 : term_width))
    local padding=$((effective_width - ${#line_content}))
    
    tput bold; tput smul
    tput setaf "$GREEN"
    echo -n "$msg_core"
    if [ "$padding" -gt 0 ]; then
        printf "%*s" "$padding" " "
    fi
    echo -n "$final_time_str"
    tput sgr0
    
    # Add post-padding to clear the rest of the line if > 80 cols
    local post_padding=$((term_width - effective_width))
    if [ "$post_padding" -gt 0 ]; then
        printf "%*s" "$post_padding" " "
    fi
    echo ""

    # Loop through and print all persistent messages with their stored color
    for p_msg in "${PERSISTENT_MESSAGES[@]}"; do
        local color_code="${p_msg%%:*}"
        local message="${p_msg#*:}"
        tput setaf "$color_code"
        echo "$message"
        tput sgr0
    done

    # Show the cursor again
    tput cnorm
    
    # Reset state for the next task
    reset_state
}

# Function to print a message to the console without disturbing the spinner.
# This is for real-time messages that are not persistent.
# Usage: log_and_spinner ["color_code"] "Your message here"
log_and_spinner() {
    local color_code=""
    local msg=""
    if [ "$#" -eq 1 ]; then
        color_code="$CYAN"
        msg="$1"
    else
        # Check if first argument is a number (color code)
        if [[ "$1" =~ ^[0-9]+$ ]]; then
            color_code="$1"
            msg="$2"
        else
            color_code="$CYAN"
            msg="$1"
        fi
    fi
    
    tput rc
    tput cud $((LOG_COUNT + 1))
    
    local term_width=$(tput cols)
    local msg_len=${#msg}
    local padding=$((term_width - msg_len))

    tput setaf "$color_code"
    echo -n "$msg"
    
    if [ "$padding" -gt 0 ]; then
        printf "%*s" "$padding" " "
    fi
    echo ""

    tput sgr0
    
    tput rc
    
    LOG_COUNT=$((LOG_COUNT + 1))
}

# Function to store a message that will be printed when the spinner stops.
# This function will either store the message if a spinner is running or
# print it directly if no spinner is active.
# Usage: show_message ["color_code"] "Your message here"
show_message() {
    local color_code=""
    local msg=""
    if [ "$#" -eq 1 ]; then
        color_code="$BLUE"
        msg="$1"
    else
        # Check if first argument is a number (color code)
        if [[ "$1" =~ ^[0-9]+$ ]]; then
            color_code="$1"
            msg="$2"
        else
            color_code="$BLUE"
            msg="$1"
        fi
    fi
    
    # Check if the spinner is running
    if [ -n "$SPINNER_PID" ] && kill -0 "$SPINNER_PID" 2>/dev/null; then
        # Log it to the screen immediately
        log_and_spinner "$color_code" "$msg"
        # Store it for later
        PERSISTENT_MESSAGES+=("$color_code:$msg")
    else
        local term_width=$(tput cols)
        local msg_len=${#msg}
        local padding=$((term_width - msg_len))
        
        tput setaf "$color_code"
        echo -n "$msg"
        if [ "$padding" -gt 0 ]; then
            printf "%*s" "$padding" " "
        fi
        echo ""
        tput sgr0
    fi
}

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

# --- Original Logging Function Wrappers ---
# These functions wrap the new, more robust functions to maintain compatibility with existing scripts.

# Function to start a message with a spinner
# start_message() {
#     start_message "$1"
# }

# Function to display a temporary status message without a spinner
show_temp_message() {
    local color_code=""
    local msg=""
    if [ "$#" -eq 1 ]; then
        color_code="$CYAN"
        msg="$1"
    else
        # Check if first argument is a number (color code)
        if [[ "$1" =~ ^[0-9]+$ ]]; then
            color_code="$1"
            msg="$2"
        else
            color_code="$CYAN"
            msg="$1"
        fi
    fi
    log_and_spinner "$color_code" "$msg"
}

# Backward compatibility alias
show_temp_status() {
    show_temp_message "$1" "$2"
}

# Function to show a final status message and stop the spinner
end_message() {
    stop_spinner "$1"
}

# Function to display a persistent message
# show_message() {
#     show_message "$1" "$2"
# }

# Alias for print_message, to maintain backward compatibility
show_status() {
    show_message "$1" "$2"
}

# The update_progress function is no longer needed as the new spinner
# automatically updates its own progress.


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

# Function to run a command with output logging and progress animation
run_logged_command() {
    local description="$1"
    local command="$2"
    local success_msg="$3"
    local error_msg="$4"
    
    log_to_file "COMMAND START: $description - Running: $command"
    
    start_message "$description"
    
    # Run command and capture output
    local output
    local exit_code
    local temp_output="/tmp/cmd_output_$$"
    
    # Run command in background and capture output
    (eval "$command" > "$temp_output" 2>&1) &
    local cmd_pid=$!
    
    # Wait for command to complete
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
        stop_spinner "✓ $success_msg"
        return 0
    else
        log_to_file "COMMAND FAILED: $description (exit code: $exit_code)"
        stop_spinner "✗ $error_msg"
        return $exit_code
    fi
}

# Function to run a simple command with just progress indication
run_command_with_progress() {
    local description="$1"
    local command="$2"
    
    log_to_file "COMMAND START: $description - Running: $command"
    
    # Show progress
    start_message "$description"
    
    # Run command and capture output
    local output
    local exit_code
    output=$(eval "$command" 2>&1)
    exit_code=$?
    
    # Log the full output
    log_command_output "$command" "$output"
    
    if [ $exit_code -eq 0 ]; then
        log_to_file "COMMAND SUCCESS: $description"
        stop_spinner "✓ $description"
        return 0
    else
        log_to_file "COMMAND FAILED: $description (exit code: $exit_code)"
        stop_spinner "✗ $description failed"
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
    show_message "$GREEN" ""
    show_message "$GREEN" "📄 Complete installation log saved to: $INSTALL_LOG_FILE"
    show_message "$GREEN" "   Use this file for troubleshooting or debugging if needed."
    show_message "$GREEN" ""
}
