#!/bin/bash

# Trailarr Bare Metal Start Script
# This script starts the main Trailarr application for bare metal installations

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
SCRIPTS_DIR="$INSTALL_DIR/scripts"

# Source the box_echo function
source "$SCRIPTS_DIR/box_echo.sh"

# Set environment variables
export APP_DATA_DIR=${APP_DATA_DIR:-"/var/lib/trailarr"}
export APP_PORT=${APP_PORT:-7889}
export PYTHONPATH="$INSTALL_DIR/backend"

# Load environment variables from .env file if it exists
if [ -f "$INSTALL_DIR/.env" ]; then
    source "$INSTALL_DIR/.env"
fi

# Update PATH for local binaries
if [ -d "$INSTALL_DIR/bin" ]; then
    export PATH="$INSTALL_DIR/bin:$PATH"
fi

box_echo "Running application as user: $(whoami)"
box_echo "Python path: $PYTHONPATH"
box_echo "App data directory: $APP_DATA_DIR"

box_echo "--------------------------------------------------------------------------"
# Backup database before running migrations
box_echo "Backing up database before running migrations..."
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"

if [ -f "$OLD_DB" ]; then
    mkdir -p "${BACKUPS_DIR}"
    cp "$OLD_DB" "$NEW_DB"
    box_echo "✓ Database backup created successfully!"
    
    # Keep only the most recent 30 backups and delete the rest
    box_echo "Cleaning up old backups (keeping most recent 30)..."
    BACKUP_COUNT=$(find "$BACKUPS_DIR" -type f -name "trailarr_*.db" 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 30 ]; then
        find "$BACKUPS_DIR" -type f -name "trailarr_*.db" -exec ls -t {} + | tail -n +31 | xargs rm -f
        DEL_COUNT=$((BACKUP_COUNT - 30))
        box_echo "$DEL_COUNT old backups deleted successfully!"
    else
        box_echo "Less than 30 backups exist ($BACKUP_COUNT), no backups deleted."
    fi
else
    box_echo "No existing database found, skipping backup"
fi
box_echo "--------------------------------------------------------------------------"

# Determine Python executable
PYTHON_EXEC="$INSTALL_DIR/venv/bin/python"
if [ ! -f "$PYTHON_EXEC" ]; then
    # Fallback to system Python if virtual environment doesn't exist
    if [ -n "$PYTHON_EXECUTABLE" ] && [ -f "$PYTHON_EXECUTABLE" ]; then
        PYTHON_EXEC="$PYTHON_EXECUTABLE"
    else
        PYTHON_EXEC="python3"
    fi
fi

# Run Alembic migrations
box_echo "Running database migrations with Alembic"
box_echo "Using Python: $PYTHON_EXEC"
cd "$INSTALL_DIR/backend"

if [ -f "$INSTALL_DIR/venv/bin/alembic" ]; then
    ALEMBIC_CMD="$INSTALL_DIR/venv/bin/alembic"
else
    ALEMBIC_CMD="$PYTHON_EXEC -m alembic"
fi

if $ALEMBIC_CMD upgrade head; then
    box_echo "✓ Database migrations ran successfully!"
else
    box_echo "✗ Database migrations failed!"
    if [ -f "$NEW_DB" ] && [ -f "$OLD_DB" ]; then
        box_echo "Restoring backup..."
        cp "$NEW_DB" "$OLD_DB"
        box_echo "✓ Backup restored successfully!"
    fi
    box_echo "Check logs for details and fix the issue before restarting"
    exit 1
fi
box_echo "--------------------------------------------------------------------------"

# Start FastAPI application
box_echo "Starting Trailarr application on port $APP_PORT..."
box_echo "Web interface will be available at: http://localhost:$APP_PORT"
echo "+==============================================================================+"
echo ""

cd "$INSTALL_DIR/backend"

# Determine uvicorn executable
if [ -f "$INSTALL_DIR/venv/bin/uvicorn" ]; then
    UVICORN_CMD="$INSTALL_DIR/venv/bin/uvicorn"
else
    UVICORN_CMD="$PYTHON_EXEC -m uvicorn"
fi

exec $UVICORN_CMD main:trailarr_api --host 0.0.0.0 --port "${APP_PORT}"