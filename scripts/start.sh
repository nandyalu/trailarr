#!/bin/bash

# THIS SCRIPT WILL BE RUN AS THE NON-ROOT USER 'appuser' IN THE CONTAINER

# Source the box_echo and load_env_file functions
source /app/scripts/box_echo.sh
source /app/scripts/load_env.sh

box_echo "Running application as user: $(whoami)"

box_echo "--------------------------------------------------------------------------";
# Load .env file from APP_DATA_DIR if it exists.
# This runs BEFORE the backup, because the backup reads the retention settings
# (BACKUP_KEEP_COUNT, BACKUP_KEEP_DAYS) that a user can store in this file.
ENV_FILE="${APP_DATA_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    box_echo "Loading environment variables from $ENV_FILE"
    # A variable set for the container wins over the stored value.
    load_env_file "$ENV_FILE"
    box_echo "Environment variables loaded successfully!"
    box_echo "--------------------------------------------------------------------------";
else
    box_echo "No .env file found at $ENV_FILE, skipping environment variable loading."
    box_echo "--------------------------------------------------------------------------";
fi

# Run Alembic migrations
box_echo "Backing up database before running migrations..."
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"
mkdir -p "${BACKUPS_DIR}" && cp $OLD_DB $NEW_DB && box_echo "Database backup created successfully!"
box_echo "--------------------------------------------------------------------------";

# Apply the retention policy. The rule lives in one Python module, which the
# direct install, the CLI updater and the dev launcher use too, so the four
# cannot disagree about what to delete. The backup taken above is the newest
# and is zero days old, so it is never a candidate.
box_echo "Applying the backup retention policy..."
if RETENTION_OUTPUT=$(python3 /app/scripts/backup_retention.py "$BACKUPS_DIR" 2>&1); then
    box_echo "$RETENTION_OUTPUT"
else
    # Retention must never stop the container from starting.
    box_echo "Could not apply the retention policy: $RETENTION_OUTPUT"
    box_echo "Trailarr starts anyway. The backups folder was not changed."
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

# Start FastAPI application
box_echo "Starting Trailarr application..."
echo "+==============================================================================+";
echo ""
cd /app/backend
if [ -n "$URL_BASE" ]; then
    exec uvicorn main:trailarr_api --host 0.0.0.0 --port ${APP_PORT:-7889} --root-path ${URL_BASE:-}
else
    exec uvicorn main:trailarr_api --host 0.0.0.0 --port ${APP_PORT:-7889}
fi