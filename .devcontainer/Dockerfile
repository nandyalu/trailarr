FROM mcr.microsoft.com/devcontainers/python:1-3.13-bullseye
# Install the xz-utils package and GPU hardware acceleration libraries
RUN apt-get update && apt-get install -y curl xz-utils tzdata \
    git gnupg2 pciutils pinentry-curses udev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install GPU hardware acceleration runtime libraries in separate commands to prevent build failures
RUN echo "Installing GPU hardware acceleration runtime libraries..." && \
    apt-get update && \
    # Core VAAPI libraries (most important for Intel/AMD)
    (apt-get install -y libva2 || echo "Warning: libva2 could not be installed") && \
    (apt-get install -y libva-drm2 || echo "Warning: libva-drm2 could not be installed") && \
    # Intel GPU drivers
    (apt-get install -y intel-media-va-driver || echo "Warning: intel-media-va-driver could not be installed") && \
    (apt-get install -y i965-va-driver || echo "Warning: i965-va-driver could not be installed") && \
    # AMD GPU drivers
    (apt-get install -y mesa-va-drivers || echo "Warning: mesa-va-drivers could not be installed") && \
    # Additional utilities and libraries
    (apt-get install -y vainfo || echo "Warning: vainfo could not be installed") && \
    (apt-get install -y libdrm2 || echo "Warning: libdrm2 could not be installed") && \
    (apt-get install -y libmfx1 || echo "Warning: libmfx1 could not be installed") && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
