#!/bin/bash

set -e

# Install drivers for Debian-based systems
install_drivers_debian() {
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture)

    # Only install drivers on amd64 architecture
    if [ "$ARCH" != "amd64" ]; then
        echo "Skipping driver installation on $ARCH architecture (drivers only supported on amd64)"
        return 0
    fi

    # Update package list
    sed -i 's/^Components: main$/& contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources || true
    apt-get update
    
    # Install GPU hardware acceleration runtime libraries in separate commands to prevent build failures
    echo "Installing GPU hardware acceleration runtime libraries for $ARCH ..."
    # Initialize an array to hold failed packages
    FAILED_PACKAGES=()
    # Core VAAPI libraries (most important for Intel/AMD)
    apt-get install -y libva2 || FAILED_PACKAGES+=("libva2")
    apt-get -yqq install git cmake pkg-config meson libdrm-dev automake libtool && \
    mkdir -p /tmp/libva && \
    cd /tmp/libva && \
    git clone https://github.com/intel/libva.git /tmp/libva && \
    git checkout 2.22.0 && \
    ./autogen.sh --prefix=/usr --libdir=/usr/lib/x86_64-linux-gnu && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    rm -rf /tmp/libva || FAILED_PACKAGES+=("libva build")

    apt-get install -y libva-drm2 || FAILED_PACKAGES+=("libva-drm2")

    # Intel GPU drivers
    apt-get install -y intel-media-va-driver || FAILED_PACKAGES+=("intel-media-va-driver")
    apt-get install -y intel-media-va-driver-non-free || FAILED_PACKAGES+=("intel-media-va-driver-non-free")
    apt-get install -y i965-va-driver || FAILED_PACKAGES+=("i965-va-driver")
    apt-get install -y i965-va-driver-shaders || FAILED_PACKAGES+=("i965-va-driver-shaders")

    # AMD GPU drivers
    apt-get install -y mesa-va-drivers || FAILED_PACKAGES+=("mesa-va-drivers")

    # Additional utilities and libraries
    apt-get install -y vainfo || FAILED_PACKAGES+=("vainfo")
    apt-get install -y libdrm2 || FAILED_PACKAGES+=("libdrm2")
    apt-get install -y libmfx1 || FAILED_PACKAGES+=("libmfx1")

    # Cleanup build dependencies and package cache to reduce image size
    echo "Cleaning up build dependencies and package cache..."
    apt-get remove -y git cmake pkg-config meson libdrm-dev automake libtool
    apt-get autoremove -y
    apt-get clean
    rm -rf /var/lib/apt/lists/*
    rm -rf /tmp/*
    rm -rf /var/tmp/*

    # Check if any packages failed to install
    if [ ${#FAILED_PACKAGES[@]} -ne 0 ]; then
        echo "Warning: [$ARCH] The following packages could not be installed: ${FAILED_PACKAGES[*]}"
    else
        echo "[$ARCH] All GPU hardware acceleration runtime libraries installed successfully."
    fi

    # Verify hardware acceleration support
    if command -v ffmpeg &> /dev/null; then
        echo "Successfully installed ffmpeg version:"
        ffmpeg -version | head -n 1
        echo "Checking hardware acceleration codecs:"
        ffmpeg -encoders 2>/dev/null | grep -E "(vaapi|nvenc|amf)" || echo "No hardware encoders found in build"
    fi
}

# Detect the OS and install drivers accordingly
if [ -f /etc/debian_version ]; then
    install_drivers_debian
else
    echo "Unsupported OS"
    exit 1
fi