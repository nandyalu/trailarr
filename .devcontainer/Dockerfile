FROM mcr.microsoft.com/devcontainers/python:1-3.13-bullseye
# Install the xz-utils package and GPU hardware acceleration libraries
RUN apt-get update && apt-get install -y curl xz-utils tzdata \
    git gnupg2 pciutils libva2 libva-drm2 intel-media-va-driver \
    libdrm2 pinentry-curses \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install HW Acceleration drivers and libraries
COPY scripts/install_drivers.sh /tmp/install_drivers.sh
RUN chmod +x /tmp/install_drivers.sh && \
    /tmp/install_drivers.sh

# Set the working directory
WORKDIR /app

# Copy backend with pyproject.toml for dependency installation
COPY backend /app/backend

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies using uv pip install with all dev dependencies
WORKDIR /app/backend
RUN uv pip install --no-cache --native-tls --system -r pyproject.toml --group dev --group docs --group testing

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
    APP_VERSION="0.6.0" \
    NVIDIA_VISIBLE_DEVICES="all" \
    NVIDIA_DRIVER_CAPABILITIES="all"

# Set the python path
ENV PYTHON_PATH="${PYTHON_PATH}:/app/backend"

# Copy required scripts for development container
COPY scripts/box_echo.sh /app/scripts/box_echo.sh
COPY scripts/entrypoint/ /app/scripts/entrypoint/
RUN find /app/scripts -name "*.sh" -type f -exec chmod +x {} \;

# Copy startup script
COPY .devcontainer/dev-start.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Expose the port the app runs on
EXPOSE 7888
