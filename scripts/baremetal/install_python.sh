#!/bin/bash

# Python 3.13.5 Installation Script for Trailarr Bare Metal Installation
# This script checks for Python 3.13.5+ and uses uv for dependency management

set -e

# Source the common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logging.sh"

# If we're in a sub-script, we need to reuse the existing log file
if [ -z "$INSTALL_LOG_FILE" ]; then
    INSTALL_LOG_FILE="/tmp/trailarr_install.log"
    export INSTALL_LOG_FILE
fi

# Python version required
PYTHON_VERSION="3.13.5"
PYTHON_MAJOR_MINOR="3.13"

# Installation directory
INSTALL_DIR="/opt/trailarr"

# Function to install uv
install_uv() {
    show_temp_message "Installing uv package manager"
    log_to_file "Installing uv package manager"
    
    # Install uv using the official installer
    if ! run_logged_command "Install uv" "curl -LsSf https://astral.sh/uv/install.sh | sh"; then
        show_message $RED "Failed to install uv"
        return 1
    fi
    
    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        # Try alternative path
        export PATH="$HOME/.cargo/bin:$PATH"
        if ! command -v uv &> /dev/null; then
            show_message $RED "uv installation failed - command not found"
            return 1
        fi
    fi
    
    # Also make uv available for trailarr user
    show_temp_message "Making uv available for trailarr user"
    if ! run_logged_command "Install uv for trailarr user" "sudo -u trailarr bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'"; then
        show_message $YELLOW "Failed to install uv for trailarr user, will use global installation"
    else
        # Make sure uv is in PATH for trailarr user
        run_logged_command "Add uv to trailarr PATH" "echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> /home/trailarr/.bashrc" || true
    fi
    
    UV_VERSION=$(uv --version)
    show_message $GREEN "uv installed successfully: $UV_VERSION"
    log_to_file "uv installed: $UV_VERSION"
    return 0
}

# Function to check if system Python 3.13.5+ is available
check_system_python() {
    show_temp_message "Checking for system Python $PYTHON_VERSION or newer"
    
    # List of python commands to check
    PYTHON_COMMANDS=(python3.13 python3 python)
    
    for CMD in "${PYTHON_COMMANDS[@]}"; do
        if command -v "$CMD" &> /dev/null; then
            SYSTEM_PYTHON_VERSION=$("$CMD" --version 2>&1 | awk '{print $2}')
            log_to_file "Found $CMD with version $SYSTEM_PYTHON_VERSION"
            # Compare major.minor.patch
            if [ "$SYSTEM_PYTHON_VERSION" = "$PYTHON_VERSION" ]; then
                export PYTHON_EXECUTABLE="$(which $CMD)"
                show_temp_message "Found system Python $PYTHON_VERSION at $PYTHON_EXECUTABLE"
                show_message $GREEN "Using system Python: $PYTHON_EXECUTABLE"
                return 0
            else
                # Check if version is greater than required
                # Use sort -V for version comparison
                if printf '%s\n%s\n' "$PYTHON_VERSION" "$SYSTEM_PYTHON_VERSION" | sort -V -C; then
                    export PYTHON_EXECUTABLE="$(which $CMD)"
                    show_temp_message "Found system Python $SYSTEM_PYTHON_VERSION (>= $PYTHON_VERSION) at $PYTHON_EXECUTABLE"
                    show_message $GREEN "Using newer system Python: $PYTHON_EXECUTABLE"
                    return 0
                else
                    show_temp_message "Found $CMD but version is $SYSTEM_PYTHON_VERSION, need >= $PYTHON_VERSION"
                fi
            fi
        fi
    done
    show_message $YELLOW "System Python $PYTHON_VERSION or newer not found, will use uv with Python $PYTHON_MAJOR_MINOR"
    log_to_file "No suitable system Python found, proceeding with uv installation"
    return 1
}

# Function to setup Python environment using uv
setup_python_with_uv() {
    log_to_file "Setting up Python environment using uv"
    
    # Change to trailarr user for uv operations
    export UV_PYTHON="$PYTHON_MAJOR_MINOR"
    
    # Setup virtual environment with uv
    show_temp_message "Creating Python virtual environment with uv"
    if ! run_logged_command "Create Python virtual environment with uv" "sudo -u trailarr uv venv \"$INSTALL_DIR/venv\" --python=\"$PYTHON_MAJOR_MINOR\""; then
        show_message $RED "Failed to create Python virtual environment with uv"
        return 1
    fi
    
    # Get the Python executable from the created venv
    export PYTHON_EXECUTABLE="$INSTALL_DIR/venv/bin/python"
    
    if [ ! -f "$PYTHON_EXECUTABLE" ]; then
        show_message $RED "Python executable not found in created venv"
        return 1
    fi
    
    PYTHON_VERSION_CHECK=$("$PYTHON_EXECUTABLE" --version 2>&1 | awk '{print $2}')
    show_message $GREEN "Python environment ready: $PYTHON_VERSION_CHECK at $PYTHON_EXECUTABLE"
    log_to_file "Python venv created successfully with version $PYTHON_VERSION_CHECK"
    return 0
}

# Main function
main() {
    log_to_file "========== Python Installation Process Started =========="

    show_temp_message "Setting up Python $PYTHON_VERSION+ environment"

    # Install uv first as we'll need it either way for dependency management
    if ! install_uv; then
        show_message $RED "Failed to install uv package manager"
        end_message $RED "uv installation failed"
        exit 1
    fi

    # Check if we already have the right Python version
    if check_system_python; then
        log_to_file "Using system Python: $PYTHON_EXECUTABLE"
    else
        # Use uv to setup Python environment
        show_temp_message "Setting up Python $PYTHON_MAJOR_MINOR environment with uv"
        if ! setup_python_with_uv; then
            show_message $RED "Failed to setup Python environment with uv"
            log_to_file "ERROR: Python environment setup failed"
            end_message $RED "Python environment setup failed"
            exit 1
        fi
    fi
    
    show_message $GREEN "Python setup complete!"
    
    log_to_file "========== Python Installation Process Completed =========="
}

# Call main function
main "$@"