# Stage 1 - Python dependencies
FROM python:3.12-slim AS python-deps

# PYTHONDONTWRITEBYTECODE=1 -> Keeps Python from generating .pyc files in the container
# PYTHONUNBUFFERED=1 -> Turns off buffering for easier container logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install pip requirements
COPY ./backend/requirements.txt .
RUN python -m pip install --disable-pip-version-check --no-cache-dir --upgrade -r requirements.txt

# Install ffmpeg
RUN apt-get update && apt-get install -y curl xz-utils

# Download and extract the appropriate ffmpeg build
RUN curl -L -o /tmp/ffmpeg.tar.xz "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz" \
    && mkdir /tmp/ffmpeg \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1 \
    && mv /tmp/ffmpeg/bin/* /usr/local/bin/ \
    && rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg

# Stage 2 - Final image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ="America/New_York" \
    APP_NAME="Trailarr" \
    APP_VERSION="0.0.4-beta"

# Install tzdata, gosu and set timezone
RUN apt update && apt install -y tzdata gosu && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

# Create a directory for the app
RUN mkdir /app

# Set the working directory
WORKDIR /app

# Copy the assets folder
COPY ./assets /app/assets

# Copy the backend
COPY ./backend /app/backend

# Copy the frontend built files
COPY ./frontend-build/browser /app/frontend-build

# Copy the installed Python dependencies and ffmpeg
COPY --from=python-deps /usr/local/ /usr/local/

# Set the python path
ENV PYTHONPATH="${PYTHONPATH}:/app/backend"

# Create a volume for data directory
VOLUME ["/data"]

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy startup script and make it executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE 7889

# Set permissions for appuser on /app directory
RUN chown -R appuser:appuser /app && chmod -R 750 /app

# Run entrypoint script to create directories, set permissions and timezone \
# and start the application as appuser
ENTRYPOINT /app/entrypoint.sh