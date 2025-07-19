#!/bin/bash

# Trailarr Bare Metal Start Script
# This script starts the main Trailarr application for bare metal installations

set -e

# Source the box_echo function
source /opt/trailarr/scripts/box_echo.sh

# Set environment variables
export APP_DATA_DIR=${APP_DATA_DIR:-"/var/lib/trailarr"}
export APP_PORT=${APP_PORT:-7889}
export PYTHONPATH="/opt/trailarr/backend"

box_echo "Running application as user: $(whoami)"

# Load environment variables from .env file if it exists
ENV_FILE="${APP_DATA_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

box_echo "--------------------------------------------------------------------------";
# Backup database before running migrations
box_echo "Backing up database before running migrations..."
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"

if [ -f "$OLD_DB" ]; then
    mkdir -p "${BACKUPS_DIR}"
    cp "$OLD_DB" "$NEW_DB"
    box_echo "Database backup created successfully!"
    
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
box_echo "--------------------------------------------------------------------------";

# Run Alembic migrations
box_echo "Running database migrations with Alembic"
box_echo "  "
cd /opt/trailarr/backend

if /opt/trailarr/venv/bin/alembic upgrade head; then
    box_echo "  "
    box_echo "Database migrations ran successfully!"
else
    box_echo "  "
    box_echo "Database migrations failed!"
    if [ -f "$NEW_DB" ] && [ -f "$OLD_DB" ]; then
        box_echo "Restoring backup..."
        cp "$NEW_DB" "$OLD_DB"
        box_echo "Backup restored successfully!"
    fi
    box_echo "Check logs for details and fix the issue before restarting"
    exit 1
fi
box_echo "--------------------------------------------------------------------------";

# Start FastAPI application
box_echo "Starting Trailarr application..."
echo "+==============================================================================+";
echo ""
cd /opt/trailarr/backend
exec /opt/trailarr/venv/bin/uvicorn main:trailarr_api --host 0.0.0.0 --port ${APP_PORT:-7889}