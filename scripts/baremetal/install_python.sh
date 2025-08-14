#!/bin/bash

# Python 3.13.5 Installation Script for Trailarr Bare Metal Installation
# This script checks for Python 3.13.5 and installs it if not available

set -e

# Source the common functions - first try baremetal logging, fallback to box_echo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/logging.sh" ]; then
    source "$SCRIPT_DIR/logging.sh"
    # If we're in a sub-script, we need to reuse the existing log file
    if [ -z "$INSTALL_LOG_FILE" ]; then
        INSTALL_LOG_FILE="/tmp/trailarr_install.log"
        export INSTALL_LOG_FILE
    fi
else
    source "$SCRIPT_DIR/../box_echo.sh"
    # Define print_message and start_message/end_message for compatibility
    print_message() { echo -e "$1$2\033[0m"; }
    start_message() { echo -e "$1$2\033[0m"; }
    end_message() { echo -e "$1$2\033[0m"; }
    log_to_file() { echo "$1"; }
    run_logged_command() { eval "$2"; }
    update_env_var() { 
        local var_name="$1"
        local var_value="$2"
        local env_file="$3"
        touch "$env_file"
        grep -v "^${var_name}=" "$env_file" > "${env_file}.tmp" 2>/dev/null || touch "${env_file}.tmp"
        echo "${var_name}=${var_value}" >> "${env_file}.tmp"
        mv "${env_file}.tmp" "$env_file"
    }
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
    show_temp_status "$BLUE" "Checking for system Python $PYTHON_VERSION..."
    log_to_file "Starting system Python check for version $PYTHON_VERSION"
    
    # List of python commands to check
    PYTHON_COMMANDS=(python3.13 python3 python)
    for CMD in "${PYTHON_COMMANDS[@]}"; do
        if command -v "$CMD" &> /dev/null; then
            SYSTEM_PYTHON_VERSION=$("$CMD" --version 2>&1 | awk '{print $2}')
            log_to_file "Found $CMD with version $SYSTEM_PYTHON_VERSION"
            # Compare major.minor.patch
            if [ "$SYSTEM_PYTHON_VERSION" = "$PYTHON_VERSION" ]; then
                show_temp_status "$GREEN" "✓ Found system Python $PYTHON_VERSION at $(which $CMD)"
                export PYTHON_EXECUTABLE="$(which $CMD)"
                log_to_file "Using system Python: $PYTHON_EXECUTABLE"
                return 0
            else
                # Check if version is greater than required
                # Use sort -V for version comparison
                if printf '%s\n%s\n' "$PYTHON_VERSION" "$SYSTEM_PYTHON_VERSION" | sort -V -C; then
                    show_temp_status "$GREEN" "✓ Found system Python $SYSTEM_PYTHON_VERSION (>= $PYTHON_VERSION) at $(which $CMD)"
                    export PYTHON_EXECUTABLE="$(which $CMD)"
                    log_to_file "Using newer system Python: $PYTHON_EXECUTABLE"
                    return 0
                else
                    log_to_file "Found $CMD but version is $SYSTEM_PYTHON_VERSION, need >= $PYTHON_VERSION"
                fi
            fi
        fi
    done
    show_temp_status "$YELLOW" "System Python $PYTHON_VERSION or newer not found, will install locally"
    log_to_file "No suitable system Python found, proceeding with local installation"
    return 1
}

# Function to install Python 3.13.5 locally
install_python_locally() {
    start_message "$BLUE" "Installing Python $PYTHON_VERSION locally..."
    log_to_file "Starting local Python installation to $PYTHON_DIR"
    
    # Create python directory
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
            end_message "$RED" "✗ Unsupported architecture: $ARCH"
            log_to_file "ERROR: Unsupported architecture $ARCH for Python installation"
            return 1
            ;;
    esac
    
    # Download URL for standalone Python build
    PYTHON_URL="https://www.python.org/ftp/python/3.13.5/Python-${PYTHON_VERSION}.tar.xz"
    
    log_to_file "Using Python URL: $PYTHON_URL for architecture $ARCH"
    
    # Download and extract Python with proper logging
    cd /tmp
    
    if ! run_logged_command "Download Python source" "curl -L -o python.tar.xz \"$PYTHON_URL\""; then
        end_message "$RED" "✗ Failed to download Python source"
        return 1
    fi

    if [ ! -f python.tar.xz ]; then
        end_message "$RED" "✗ Python download file not found"
        return 1
    fi
    
    # Extract to installation directory
    log_to_file "Extracting Python to $PYTHON_DIR"
    if ! run_logged_command "Extract Python source" "tar -xJf python.tar.xz -C \"$PYTHON_DIR\" --strip-components=1"; then
        end_message "$RED" "✗ Failed to extract Python source"
        return 1
    fi

    # Clean up
    rm -f python.tar.xz

    # Verify installation
    if [ -f "$PYTHON_BIN" ]; then
        INSTALLED_VERSION=$("$PYTHON_BIN" --version 2>&1 | cut -d' ' -f2)
        log_to_file "Python installation verified: $INSTALLED_VERSION at $PYTHON_BIN"
        end_message "$GREEN" "✓ Successfully installed Python $INSTALLED_VERSION"
        export PYTHON_EXECUTABLE="$PYTHON_BIN"
        return 0
    else
        end_message "$RED" "✗ Python installation failed - binary not found"
        log_to_file "ERROR: Python binary not found at expected location $PYTHON_BIN"
        return 1
    fi
}

# Function to ensure pip is available
ensure_pip() {
    start_message "$BLUE" "Setting up pip..."
    log_to_file "Checking pip availability for Python executable: $PYTHON_EXECUTABLE"
    
    if ! "$PYTHON_EXECUTABLE" -m pip --version &> /dev/null; then
        log_to_file "pip not found, installing ensurepip"
        if ! run_logged_command "Install pip via ensurepip" "\"$PYTHON_EXECUTABLE\" -m ensurepip --default-pip"; then
            end_message "$RED" "✗ Failed to install pip"
            return 1
        fi
    fi
    
    # Upgrade pip to latest version
    log_to_file "Upgrading pip to latest version"
    if ! run_logged_command "Upgrade pip" "\"$PYTHON_EXECUTABLE\" -m pip install --upgrade pip"; then
        end_message "$YELLOW" "! Failed to upgrade pip, but continuing..."
    fi
    
    PIP_VERSION=$("$PYTHON_EXECUTABLE" -m pip --version | cut -d' ' -f2)
    end_message "$GREEN" "✓ pip version $PIP_VERSION is ready"
}

# Main function
main() {
    show_temp_status "$BLUE" "Python $PYTHON_VERSION Installation Check"
    log_to_file "========== Python Installation Process Started =========="
    
    # Check if we already have the right Python version
    if check_system_python; then
        print_message "$GREEN" "Using system Python installation"
        log_to_file "Using system Python: $PYTHON_EXECUTABLE"
    else
        # Install Python locally
        if ! install_python_locally; then
            print_message "$RED" "Failed to install Python $PYTHON_VERSION"
            log_to_file "ERROR: Python installation failed"
            return 1
        fi
    fi
    
    # Ensure pip is available
    ensure_pip
    
    print_message "$GREEN" "→ Python executable: $PYTHON_EXECUTABLE"
    print_message "$GREEN" "→ Python version: $($PYTHON_EXECUTABLE --version)"
    print_message "$GREEN" "✓ Python setup complete!"
    
    log_to_file "Python setup completed successfully"
    log_to_file "Final Python executable: $PYTHON_EXECUTABLE"
    log_to_file "Final Python version: $($PYTHON_EXECUTABLE --version)"
    
    # Export for use by other scripts and save to .env
    export PYTHON_EXECUTABLE
    
    # Save to .env file using the new function
    update_env_var "PYTHON_EXECUTABLE" "$PYTHON_EXECUTABLE" "$INSTALL_DIR/.env"
    
    log_to_file "========== Python Installation Process Completed =========="
}

# Run main function
main "$@"