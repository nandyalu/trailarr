# Stage 1 - Python dependencies
FROM python:3.12-slim AS python-deps

# PYTHONDONTWRITEBYTECODE=1 -> Keeps Python from generating .pyc files in the container
# PYTHONUNBUFFERED=1 -> Turns off buffering for easier container logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install pip requirements
COPY ./backend/requirements.txt .
RUN python -m pip install --disable-pip-version-check --upgrade -r requirements.txt

# Install ffmpeg using install_ffmpeg.sh script
COPY ./scripts/install_ffmpeg.sh /tmp/install_ffmpeg.sh
RUN chmod +x /tmp/install_ffmpeg.sh && \
    /tmp/install_ffmpeg.sh

# Stage 2 - Final image
FROM python:3.12-slim

# ARG APP_VERSION, will be set during build by github actions
ARG APP_VERSION=0.0.0-dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ="America/New_York" \
    APP_NAME="Trailarr" \
    APP_PORT=7889 \
    APP_DATA_DIR="/data" \
    PUID=1000 \
    PGID=1000 \
    APP_VERSION=${APP_VERSION}

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
COPY ./frontend-build /app/frontend-build

# Copy the installed Python dependencies and ffmpeg
COPY --from=python-deps /usr/local/ /usr/local/

# Set the python path
ENV PYTHONPATH="${PYTHONPATH:-}:/app/backend"

# Copy the entrypoint script and make it executable
COPY ./scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy startup script and make it executable
COPY ./scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE ${APP_PORT}

# Set permissions for appuser on /app directory
RUN chmod -R 750 /app

# Define a healthcheck command
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:${APP_PORT}/status || exit 1

# Run entrypoint script to create directories, set permissions and timezone \
# and start the application as appuser
ENTRYPOINT ["/app/entrypoint.sh"]