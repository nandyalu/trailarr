FROM mcr.microsoft.com/devcontainers/python:1-3.13-bullseye
# Install the xz-utils package
RUN apt-get update && apt-get install -y curl xz-utils tzdata \
    git gnupg2 pciutils libva2 libva-drm2 intel-media-va-driver \
    libdrm2 pinentry-curses \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python Packages
COPY dev-requirements.txt .
RUN python -m pip install --no-cache-dir --disable-pip-version-check \
    --upgrade -r /app/dev-requirements.txt

# Download and extract the custom FFmpeg build from yt-dlp
RUN curl -L -o /tmp/ffmpeg.tar.xz "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz" \
    && mkdir /tmp/ffmpeg \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1 \
    && mv /tmp/ffmpeg/bin/* /usr/local/bin/ \
    && rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ="America/New_York" \
    APP_NAME="Trailarr" \
    APP_VERSION="0.4.4" \
    NVIDIA_VISIBLE_DEVICES="all" \
    NVIDIA_DRIVER_CAPABILITIES="all"

# Set the python path
ENV PYTHON_PATH="${PYTHON_PATH}:/app/backend"

# Copy startup script
COPY dev-start.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Expose the port the app runs on
EXPOSE 7888
