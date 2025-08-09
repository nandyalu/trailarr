#!/bin/bash

# Python 3.13.5 Installation Script for Trailarr Bare Metal Installation
# This script checks for Python 3.13.5 and installs it if not available

set -e

# Source the common functions
source "$(dirname "$0")/../box_echo.sh"

# Python version required
PYTHON_VERSION="3.13.5"
PYTHON_MAJOR_MINOR="3.13"

# Installation directory
INSTALL_DIR="/opt/trailarr"
PYTHON_DIR="$INSTALL_DIR/python"
PYTHON_BIN="$PYTHON_DIR/bin/python3"

# Function to check if system Python 3.13.5 is available
check_system_python() {
    box_echo "Checking for system Python $PYTHON_VERSION..."
    
    # Check if python3.13 is available
    if command -v python3.13 &> /dev/null; then
        SYSTEM_PYTHON_VERSION=$(python3.13 --version 2>&1 | cut -d' ' -f2)
        if [ "$SYSTEM_PYTHON_VERSION" = "$PYTHON_VERSION" ]; then
            box_echo "✓ Found system Python $PYTHON_VERSION at $(which python3.13)"
            export PYTHON_EXECUTABLE="$(which python3.13)"
            return 0
        else
            box_echo "Found python3.13 but version is $SYSTEM_PYTHON_VERSION, need $PYTHON_VERSION"
        fi
    fi
    
    # Check if python3 points to 3.13.5
    if command -v python3 &> /dev/null; then
        SYSTEM_PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        if [ "$SYSTEM_PYTHON_VERSION" = "$PYTHON_VERSION" ]; then
            box_echo "✓ Found system Python $PYTHON_VERSION at $(which python3)"
            export PYTHON_EXECUTABLE="$(which python3)"
            return 0
        else
            box_echo "Found python3 but version is $SYSTEM_PYTHON_VERSION, need $PYTHON_VERSION"
        fi
    fi
    
    box_echo "System Python $PYTHON_VERSION not found, will install locally"
    return 1
}

# Function to install Python 3.13.5 locally
install_python_locally() {
    box_echo "Installing Python $PYTHON_VERSION locally in $PYTHON_DIR..."
    
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
            box_echo "Unsupported architecture: $ARCH"
            box_echo "Please install Python $PYTHON_VERSION manually"
            return 1
            ;;
    esac
    
    # Download URL for standalone Python build
    PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-${PYTHON_VERSION}+20241016-${PYTHON_ARCH}-install_only.tar.gz"
    
    box_echo "Downloading Python $PYTHON_VERSION for $ARCH..."
    box_echo "URL: $PYTHON_URL"
    
    # Download and extract Python
    cd /tmp
    curl -L -o python.tar.gz "$PYTHON_URL"
    
    if [ ! -f python.tar.gz ]; then
        box_echo "Failed to download Python binary"
        return 1
    fi
    
    # Extract to installation directory
    box_echo "Extracting Python to $PYTHON_DIR..."
    tar -xzf python.tar.gz -C "$PYTHON_DIR" --strip-components=1
    
    # Clean up
    rm python.tar.gz
    
    # Verify installation
    if [ -f "$PYTHON_BIN" ]; then
        INSTALLED_VERSION=$("$PYTHON_BIN" --version 2>&1 | cut -d' ' -f2)
        box_echo "✓ Successfully installed Python $INSTALLED_VERSION at $PYTHON_BIN"
        export PYTHON_EXECUTABLE="$PYTHON_BIN"
        return 0
    else
        box_echo "Failed to install Python - binary not found at $PYTHON_BIN"
        return 1
    fi
}

# Function to ensure pip is available
ensure_pip() {
    box_echo "Ensuring pip is available for Python..."
    
    if ! "$PYTHON_EXECUTABLE" -m pip --version &> /dev/null; then
        box_echo "pip not found, installing..."
        "$PYTHON_EXECUTABLE" -m ensurepip --default-pip
    fi
    
    # Upgrade pip to latest version
    box_echo "Upgrading pip to latest version..."
    "$PYTHON_EXECUTABLE" -m pip install --upgrade pip
    
    PIP_VERSION=$("$PYTHON_EXECUTABLE" -m pip --version | cut -d' ' -f2)
    box_echo "✓ pip version $PIP_VERSION is ready"
}

# Main function
main() {
    box_echo "Python $PYTHON_VERSION Installation Check"
    box_echo "--------------------------------------------------------------------------"
    
    # Check if we already have the right Python version
    if check_system_python; then
        box_echo "Using system Python installation"
    else
        # Install Python locally
        if ! install_python_locally; then
            box_echo "Failed to install Python $PYTHON_VERSION"
            return 1
        fi
    fi
    
    # Ensure pip is available
    ensure_pip
    
    box_echo "Python setup complete!"
    box_echo "Python executable: $PYTHON_EXECUTABLE"
    box_echo "Python version: $($PYTHON_EXECUTABLE --version)"
    box_echo "--------------------------------------------------------------------------"
    
    # Export for use by other scripts
    export PYTHON_EXECUTABLE
    echo "PYTHON_EXECUTABLE=$PYTHON_EXECUTABLE" >> "$INSTALL_DIR/.env"
}

# Run main function
main "$@"