#!/bin/bash

# Development container startup script
# Reuses production entrypoint components where possible

# Source the box_echo function for consistent logging
source /app/scripts/box_echo.sh

# Ensure Node.js and npm are in the PATH
export PATH=$PATH:/usr/local/bin:/usr/local/share/nvm/current/bin
box_echo "PATH: $PATH"

# Source production scripts for reuse
source /app/scripts/entrypoint/timezone.sh
source /app/scripts/entrypoint/gpu_detection.sh
source /app/scripts/entrypoint/directories.sh
source /app/scripts/entrypoint/env_file.sh

# Set development-specific environment variables
export APPUSER="vscode"
export APPGROUP="vscode"

# Configure timezone (reuse production function)
configure_timezone

# Create development data directories (reuse production logic)
box_echo "Creating '$APP_DATA_DIR' folder for storing database and other config files"
# Remove trailing slash from APP_DATA_DIR if it exists
export APP_DATA_DIR=$(echo $APP_DATA_DIR | sed 's:/*$::')

# Set APP_DATA_DIR env to /app/config if empty
if [ -z "$APP_DATA_DIR" ]; then
  APP_DATA_DIR="/app/config"
  export APP_DATA_DIR
fi

# Create appdata folder for storing database and other config files
mkdir -p "${APP_DATA_DIR}/logs" && chmod -R 755 $APP_DATA_DIR
mkdir -p /app/tmp && chmod -R 755 /app/tmp
chown -R "$APPUSER":"$APPGROUP" "$APP_DATA_DIR"

# GPU Detection (reuse production functions)
setup_gpu_detection

# Generate environment file with GPU detection results (reuse production function)
generate_env_file

# Check the version of yt-dlp and store it in a global environment variable
box_echo "Checking yt-dlp version..."
YTDLP_VERSION=$(yt-dlp --version)
export YTDLP_VERSION
box_echo "yt-dlp version: $YTDLP_VERSION"

# Run Alembic migrations
box_echo "Running Alembic migrations"
cd /app/backend
alembic upgrade head && box_echo "Alembic migrations ran successfully"

# Install Angular & dependencies
box_echo "Installing Angular and it's dependencies"
npm install -g @angular/cli
cd ../frontend && npm install
ng completion

# Start Angular application
# box_echo "Building Angular application"
# cd /app/frontend && nohup ng serve &

# Start FastAPI application
# box_echo "Starting FastAPI application"
# cd /app
# exec gunicorn --bind 0.0.0.0:7888 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api
chown -R "$APPUSER":"$APPGROUP" "$APP_DATA_DIR"

box_echo "Dev container started successfully!"