#!/bin/bash

# THIS SCRIPT WILL BE RUN AS THE NON-ROOT USER 'appuser' IN THE CONTAINER

# Source the box_echo function
source /app/scripts/box_echo.sh

box_echo "Running application as user: $(whoami)"

box_echo "--------------------------------------------------------------------------";
# Run Alembic migrations
box_echo "Backing up database before running migrations..."
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"
mkdir -p "${BACKUPS_DIR}" && cp $OLD_DB $NEW_DB && box_echo "Database backup created successfully!"
box_echo "--------------------------------------------------------------------------";

# Keep only the most recent 30 backups and delete the rest
box_echo "Deleting older backups if more than 30 exist..."
BACKUP_COUNT=$(find "$BACKUPS_DIR" -type f -name "trailarr_*.db" | wc -l)
if [ "$BACKUP_COUNT" -gt 30 ]; then
    ls -t "$BACKUPS_DIR"/trailarr_*.db | tail -n +31 | xargs rm -f
    DEL_COUNT=$((BACKUP_COUNT - 30))
    box_echo "$DEL_COUNT Old backups deleted successfully!"
else
    box_echo "Less than 30 backups exist ($BACKUP_COUNT), no backups deleted."
fi
box_echo "--------------------------------------------------------------------------";

box_echo "Running database migrations with Alembic"
box_echo "  "
cd /app/backend
if alembic upgrade head; then
    box_echo "  "
    box_echo "Database migrations ran successfully!"
else
    box_echo "  "
    box_echo "Database migrations failed! Restoring backup!"
    cp $NEW_DB $OLD_DB
    box_echo "Backup restored successfully! Sleeping indefinitely to prevent container exit"
    while :; do sleep 10000000; done
fi
box_echo "--------------------------------------------------------------------------";

# Load .env file from APP_DATA_DIR if it exists
ENV_FILE="${APP_DATA_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    box_echo "Loading environment variables from $ENV_FILE"
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
    box_echo "Environment variables loaded successfully!"
    box_echo "--------------------------------------------------------------------------";
else
    box_echo "No .env file found at $ENV_FILE, skipping environment variable loading."
    box_echo "--------------------------------------------------------------------------";
fi
# Start FastAPI application
box_echo "Starting Trailarr application..."
echo "+==============================================================================+";
echo ""
cd /app/backend
exec uvicorn main:trailarr_api --host 0.0.0.0 --port ${APP_PORT:-7889} --root-path ${URL_BASE:-/}