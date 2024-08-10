#!/bin/sh

# THIS SCRIPT WILL BE RUN AS THE NON-ROOT USER 'appuser' IN THE CONTAINER

echo "Running application as user: $(whoami)"

# Run Alembic migrations
echo "Backing up database before running migrations..."
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"
mkdir -p "${BACKUPS_DIR}" && cp $OLD_DB $new_db && echo "Database backup created successfully!"

# Keep only the most recent 30 backups and delete the rest
echo "Deleting older backups if more than 30 exist..."
BACKUP_COUNT=$(find "$BACKUPS_DIR" -type f -name "trailarr_*.db" | wc -l)
if [ "$BACKUP_COUNT" -gt 30 ]; then
    ls -t "$BACKUPS_DIR"/trailarr_*.db | tail -n +31 | xargs rm -f
    echo "Old backups deleted successfully!"
else
    echo "Less than 30 backups exist, no backups deleted."
fi

echo "Running database migrations with Alembic"
cd /app/backend
if alembic upgrade head; then
    echo "Database migrations ran successfully!"
else
    echo "Database migrations failed! Restoring backup!"
    cp $NEW_DB $OLD_DB
    echo "Backup restored successfully! Sleeping indefinitely to prevent container exit"
    while :; do sleep 10000000; done
fi

# Start FastAPI application
echo "Starting Trailarr application"
cd /app
exec uvicorn backend.main:trailarr_api --host 0.0.0.0 --port ${APP_PORT:-7889}