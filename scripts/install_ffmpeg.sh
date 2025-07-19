#!/bin/bash

set -e

# Function to install ffmpeg with hardware acceleration support for Debian-based systems
install_ffmpeg_debian() {
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture)
    
    echo "Installing ffmpeg with hardware acceleration support for $ARCH"
    
    # Install required dependencies and runtime libraries for hardware acceleration
    apt-get update && apt-get install -y \
        curl \
        xz-utils \
        libva2 \
        libva-drm2 \
        intel-media-va-driver \
        i965-va-driver \
        mesa-va-drivers \
        vainfo \
        libdrm2 \
        libmfx1 \
        || echo "Warning: Some GPU acceleration packages could not be installed"
    
    if [ "$ARCH" == "amd64" ]; then
        # Use johnvansickle static builds which include hardware acceleration support
        FFMPEG_URL="https://www.johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
    elif [ "$ARCH" == "arm64" ] || [ "$ARCH" == "aarch64" ]; then
        # Use johnvansickle static builds for arm64
        FFMPEG_URL="https://www.johnvansickle.com/ffmpeg/builds/ffmpeg-git-arm64-static.tar.xz"
    else
        # Fallback to distribution ffmpeg with additional packages
        echo "Architecture $ARCH not supported by static builds, using distribution ffmpeg"
        apt-get install -y ffmpeg
        
        # Verify hardware acceleration support
        if command -v ffmpeg &> /dev/null; then
            echo "Installed distribution ffmpeg version:"
            ffmpeg -version | head -n 1
            echo "Checking hardware acceleration codecs:"
            ffmpeg -encoders 2>/dev/null | grep -E "(vaapi|nvenc|amf)" || echo "No hardware encoders found"
        fi
        exit 0
    fi

    # Download and install static ffmpeg build
    echo "Downloading static ffmpeg build from johnvansickle.com for $ARCH"
    curl -L -o /tmp/ffmpeg.tar.xz "$FFMPEG_URL"
    
    # Extract and install
    mkdir -p /tmp/ffmpeg
    tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
    
    # Install ffmpeg binaries
    cp /tmp/ffmpeg/ffmpeg /usr/local/bin/ffmpeg
    cp /tmp/ffmpeg/ffprobe /usr/local/bin/ffprobe
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
    
    # Clean up
    rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg
    
    # Verify installation and hardware acceleration support
    if command -v ffmpeg &> /dev/null; then
        echo "Successfully installed ffmpeg version:"
        ffmpeg -version | head -n 1
        echo "Checking hardware acceleration codecs:"
        ffmpeg -encoders 2>/dev/null | grep -E "(vaapi|nvenc|amf)" || echo "No hardware encoders found in build"
    else
        echo "Error: ffmpeg installation failed"
        exit 1
    fi
}

# Detect the OS and install ffmpeg accordingly
if [ -f /etc/debian_version ]; then
    install_ffmpeg_debian
else
    echo "Unsupported OS"
    exit 1
fi