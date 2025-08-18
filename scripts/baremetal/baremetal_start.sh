#!/bin/bash

# Trailarr Bare Metal Start Script
# This script starts the main Trailarr application for bare metal installations

set -e

# Installation directories
INSTALL_DIR="/opt/trailarr"
SCRIPTS_DIR="$INSTALL_DIR/scripts"

# Source the logging functions
source "$SCRIPTS_DIR/baremetal/logging.sh"

# Initialize logging for runtime  
INSTALL_LOG_FILE="/var/log/trailarr/start.log"
mkdir -p "$(dirname "$INSTALL_LOG_FILE")"
touch "$INSTALL_LOG_FILE"
export INSTALL_LOG_FILE

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

show_message "Running application as user: $(whoami)"
show_message "Python path: $PYTHONPATH"
show_message "App data directory: $APP_DATA_DIR"

show_message "--------------------------------------------------------------------------"
# Backup database before running migrations
start_message "Backing up database before running migrations"
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"

if [ -f "$OLD_DB" ]; then
    show_temp_message "Creating database backup"
    mkdir -p "${BACKUPS_DIR}"
    cp "$OLD_DB" "$NEW_DB"
    show_message $GREEN "✓ Database backup created successfully!"
    
    # Keep only the most recent 30 backups and delete the rest
    show_temp_message "Cleaning up old backups (keeping most recent 30)"
    BACKUP_COUNT=$(find "$BACKUPS_DIR" -type f -name "trailarr_*.db" 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 30 ]; then
        find "$BACKUPS_DIR" -type f -name "trailarr_*.db" -exec ls -t {} + | tail -n +31 | xargs rm -f
        DEL_COUNT=$((BACKUP_COUNT - 30))
        show_message $GREEN "$DEL_COUNT old backups deleted successfully!"
    else
        show_message "Less than 30 backups exist ($BACKUP_COUNT), no backups deleted."
    fi
else
    show_message $YELLOW "No existing database found, skipping backup"
fi
end_message "Database backup complete"

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
start_message "Running database migrations with Alembic"
show_message "Using Python: $PYTHON_EXEC"
cd "$INSTALL_DIR/backend"

if [ -f "$INSTALL_DIR/venv/bin/alembic" ]; then
    ALEMBIC_CMD="$INSTALL_DIR/venv/bin/alembic"
else
    ALEMBIC_CMD="$PYTHON_EXEC -m alembic"
fi

show_temp_message "Running Alembic migrations"
if $ALEMBIC_CMD upgrade head; then
    show_message $GREEN "✓ Database migrations ran successfully!"
    end_message "Database migrations complete"
else
    show_message $RED "✗ Database migrations failed!"
    if [ -f "$NEW_DB" ] && [ -f "$OLD_DB" ]; then
        show_temp_message "Restoring backup"
        cp "$NEW_DB" "$OLD_DB"
        show_message $GREEN "✓ Backup restored successfully!"
    fi
    show_message $RED "Check logs for details and fix the issue before restarting"
    end_message $RED "Database migration failed"
    exit 1
fi

# Start FastAPI application
show_message "Starting Trailarr application on port $APP_PORT..."
show_message "Web interface will be available at: http://localhost:$APP_PORT"
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