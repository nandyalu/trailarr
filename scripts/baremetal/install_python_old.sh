#!/bin/bash

# Python 3.13.5 Installation Script for Trailarr Bare Metal Installation
# This script checks for Python 3.13.5 and installs it if not available

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
PYTHON_DIR="$INSTALL_DIR/python"
PYTHON_BIN="$PYTHON_DIR/bin/python3"

# Function to check if system Python 3.13.5 is available
check_system_python() {
    show_temp_message "Checking for system Python $PYTHON_VERSION"
    
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
    show_message $YELLOW "System Python $PYTHON_VERSION or newer not found, will install locally"
    log_to_file "No suitable system Python found, proceeding with local installation"
    return 1
}

# Function to install Python 3.13.5 locally
install_python_locally() {
    log_to_file "Starting local Python installation to $PYTHON_DIR"
    
    # Create python directory
    show_temp_message "Creating Python directory"
    mkdir -p "$PYTHON_DIR"
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            PYTHON_ARCH="x86_64-unknown-linux-gnu"
            ;;
        aarch64|arm64)
            PYTHON_ARCH="aarch64-unknown-linux-gnu"
            ;;
        *)
            show_message $RED "Unsupported architecture: $ARCH"
            show_message $YELLOW "Install Python 3.13.5 manually or use a different install method."
            log_to_file "ERROR: Unsupported architecture $ARCH for Python installation"
            return 1
            ;;
    esac
    
    # Download URL for standalone Python build
    PYTHON_URL="https://www.python.org/ftp/python/3.13.5/Python-${PYTHON_VERSION}.tar.xz"
    
    log_to_file "Using Python URL: $PYTHON_URL for architecture $ARCH"
    
    # Download and extract Python with proper logging
    cd /tmp
    
    show_temp_message "Downloading Python source code"
    if ! run_logged_command "Download Python source" "curl -L -o python.tar.xz \"$PYTHON_URL\""; then
        show_message $RED "Failed to download Python source"
        return 1
    fi

    if [ ! -f python.tar.xz ]; then
        show_message $RED "Python download file not found"
        return 1
    fi
    
    # Extract to installation directory
    log_to_file "Extracting Python to $PYTHON_DIR"
    show_temp_message "Extracting Python source code"
    if ! run_logged_command "Extract Python source" "tar -xJf python.tar.xz -C \"$PYTHON_DIR\" --strip-components=1"; then
        show_message $RED "Failed to extract Python source"
        return 1
    fi

    # Clean up
    show_temp_message "Cleaning up downloaded files"
    rm -f python.tar.xz

    # Verify installation
    if [ -f "$PYTHON_BIN" ]; then
        INSTALLED_VERSION=$("$PYTHON_BIN" --version 2>&1 | cut -d' ' -f2)
        log_to_file "Python installation verified: $INSTALLED_VERSION at $PYTHON_BIN"
        show_message $GREEN "Successfully installed Python $INSTALLED_VERSION"
        export PYTHON_EXECUTABLE="$PYTHON_BIN"
        return 0
    else
        show_message $RED "Python installation failed - binary not found"
        log_to_file "ERROR: Python binary not found at expected location $PYTHON_BIN"
        return 1
    fi
}

# Function to ensure pip is available
ensure_pip() {
    log_to_file "Checking pip availability for Python executable: $PYTHON_EXECUTABLE"
    
    show_temp_message "Checking pip availability"
    if ! "$PYTHON_EXECUTABLE" -m pip --version &> /dev/null; then
        log_to_file "pip not found, installing ensurepip"
        show_temp_message "Installing pip via ensurepip"
        if ! run_logged_command "Install pip via ensurepip" "\"$PYTHON_EXECUTABLE\" -m ensurepip --default-pip"; then
            show_message $RED "Failed to install pip"
            end_message $RED "Pip installation failed"
            exit 1
        fi
    fi
    
    # Upgrade pip to latest version
    show_temp_message "Upgrading pip to latest version"
    if ! run_logged_command "Upgrade pip" "\"$PYTHON_EXECUTABLE\" -m pip install --upgrade pip"; then
        show_message $YELLOW "Failed to upgrade pip, but continuing..."
    fi
    
    PIP_VERSION=$("$PYTHON_EXECUTABLE" -m pip --version | cut -d' ' -f2)
    show_message $GREEN "pip version $PIP_VERSION is ready"
}

# Main function
main() {
    log_to_file "========== Python Installation Process Started =========="

    show_temp_message "Setting up Python $PYTHON_VERSION environment"

    # Check if we already have the right Python version
    if check_system_python; then
        log_to_file "Using system Python: $PYTHON_EXECUTABLE"
    else
        # Install Python locally
        show_temp_message "Installing Python $PYTHON_VERSION locally"
        if ! install_python_locally; then
            show_message $RED "Failed to install Python $PYTHON_VERSION"
            log_to_file "ERROR: Python installation failed"
            end_message $RED "Python installation failed"
            exit 1
        fi
    fi
    
    # Ensure pip is available
    ensure_pip
    
    show_message $GREEN "Python setup complete!"
    
    log_to_file "Python setup completed successfully"
    log_to_file "Final Python executable: $PYTHON_EXECUTABLE"
    log_to_file "Final Python version: $($PYTHON_EXECUTABLE --version)"
    
    # Export for use by other scripts and save to .env
    export PYTHON_EXECUTABLE
    
    # Save to .env file using the new function
    update_env_var "PYTHON_EXECUTABLE" "$PYTHON_EXECUTABLE" "$INSTALL_DIR/.env"
    
    log_to_file "========== Python Installation Process Completed =========="
    
    show_message "Python environment ready"
}

# Run main function
main "$@"