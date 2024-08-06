#!/bin/bash

set -e

# Function to install ffmpeg for Debian-based systems
install_ffmpeg_debian() {
    # Get the architecture of the system
    ARCH=$(dpkg --print-architecture)
    if [ "$ARCH" == "amd64" ]; then
        # Download the latest ffmpeg build for amd64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [ "$ARCH" == "arm64" ] || [ "$ARCH" == "aarch64" ]; then
        # Download the latest ffmpeg build for arm64
        FFMPEG_URL="https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    else
        # If the architecture is not supported, install ffmpeg using apt
        echo "Unsupported architecture: $ARCH, Install ffmpeg manually"
        apt install ffmpeg
        mv /usr/bin/ff* /usr/local/bin/
        exit 0
    fi

    # Install the required dependencies
    apt update && apt install -y curl xz-utils
    # Download and install ffmpeg
    echo "Downloading ffmpeg for $ARCH"
    curl -L -o /tmp/ffmpeg.tar.xz "$FFMPEG_URL"
    mkdir /tmp/ffmpeg
    tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
    mv /tmp/ffmpeg/bin/* /usr/local/bin/
    rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg
}

# Detect the OS and install ffmpeg accordingly
if [ -f /etc/debian_version ]; then
    install_ffmpeg_debian
else
    echo "Unsupported OS"
    exit 1
fi