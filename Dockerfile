# Stage 1 - gosu builder
FROM golang:1.24.5-bookworm AS gosu-builder
RUN apt-get update && apt-get install -y --no-install-recommends git
RUN git clone https://github.com/harshitsidhwa/gosu.git /gosu
WORKDIR /gosu
RUN go build -o /usr/local/bin/gosu .

# Stage 1 - Python dependencies
FROM python:3.13-slim AS python-deps

# For bare metal installation, see install.sh script in the repository root

# PYTHONDONTWRITEBYTECODE=1 -> Keeps Python from generating .pyc files in the container
# PYTHONUNBUFFERED=1 -> Turns off buffering for easier container logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install ca-certificates for SSL
RUN apt-get update && apt-get install -y ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy backend with pyproject.toml for dependency installation
COPY ./backend /app/backend

# Install Python dependencies using uv pip install
WORKDIR /app/backend
RUN uv pip install --no-cache --native-tls --system -r pyproject.toml

# Install ffmpeg using install_ffmpeg.sh script
COPY ./scripts/install_ffmpeg.sh /tmp/install_ffmpeg.sh
RUN chmod +x /tmp/install_ffmpeg.sh && \
    /tmp/install_ffmpeg.sh

# Stage 2 - Final image
FROM python:3.13-slim

# Copy gosu from builder stage
COPY --from=gosu-builder /usr/local/bin/gosu /usr/local/bin/gosu
RUN chmod +x /usr/local/bin/gosu

# Copy uv, ffmpeg and Python dependencies from python-deps stage to make it available in final image
COPY --from=python-deps /usr/local/ /usr/local/

# Install HW Acceleration drivers and libraries
COPY ./scripts/install_drivers.sh /tmp/install_drivers.sh
RUN chmod +x /tmp/install_drivers.sh && \
    /tmp/install_drivers.sh

    
# ARG APP_VERSION, will be set during build by github actions
ARG APP_VERSION=0.0.0-dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ="America/New_York" \
    APP_NAME="Trailarr" \
    APP_MODE="Docker" \
    APP_PORT=7889 \
    APP_DATA_DIR="/config" \
    PUID=1000 \
    PGID=1000 \
    APP_VERSION=${APP_VERSION} \
    NVIDIA_VISIBLE_DEVICES="all" \
    NVIDIA_DRIVER_CAPABILITIES="all"

# Install tzdata and pciutils, set timezone
RUN apt-get update && apt-get install -y \
    curl p7zip-full \
    tzdata \
    pciutils \
    udev \
    && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

# Install Deno for use with yt-dlp - install globally for all users
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh && \
    chmod +x /usr/local/bin/deno && \
    /usr/local/bin/deno --version

# Set the working directory
WORKDIR /app

# Copy the assets folder
COPY ./assets /app/assets

# Copy the backend
COPY ./backend /app/backend

# # Copy the installed Python virtual environment from python-deps stage
# COPY --from=python-deps /app/backend/.venv /app/backend/.venv

# Copy the frontend built files
COPY ./frontend-build /app/frontend-build

# # Copy the installed Python dependencies and ffmpeg
# COPY --from=python-deps /usr/local/ /usr/local/

# Set the python path
ENV PYTHONPATH=/app/backend

# Copy the scripts folder, and make all scripts executable (including subdirectories)
COPY ./scripts /app/scripts
RUN find /app/scripts -name "*.sh" -type f -exec chmod +x {} \;

# Expose the port the app runs on
EXPOSE ${APP_PORT}

# Set permissions for appuser on /app directory
RUN chmod -R 750 /app

# Define a healthcheck command
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python /app/scripts/healthcheck.py ${APP_PORT}

# Run entrypoint script to create directories, set permissions and timezone \
# and start the application as appuser
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
