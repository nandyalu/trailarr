#!/bin/sh

# THIS SCRIPT WILL BE RUN AS THE NON-ROOT USER 'appuser' IN THE CONTAINER

echo "Running application as user: $(whoami)"

# Run Alembic migrations
echo "Backing up database before running migrations..."
new_db=/data/backups/trailarr_$(date +%Y%m%d%H%M%S).db
old_db=/data/trailarr.db
mkdir -p /data/backups && cp $old_db $new_db && echo "Database backup created successfully!"


echo "Running database migrations with Alembic"
cd /app/backend
if alembic upgrade head; then
    echo "Database migrations ran successfully!"
else
    echo "Database migrations failed! Restoring backup!"
    cp $new_db $old_db
    echo "Backup restored successfully! Sleeping indefinitely to prevent container exit"
    while :; do sleep 10000000; done
fi

# Start FastAPI application
echo "Starting Trailarr application"
cd /app
exec uvicorn backend.main:trailarr_api --host 0.0.0.0 --port 7889