#!/bin/sh

# Set TimeZone based on env variable
# Print date time before 
echo "Current date time: $(date)"
echo "Setting TimeZone to ${TZ}"
echo $TZ > /etc/timezone && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata
echo "Current date time after tzdate: $(date)"

# Create data folder for storing database and other config files
mkdir -p /data/logs && chmod -R 755 /data
chmod -R 755 /app/assets

# Run Alembic migrations
echo "Running Alembic migrations"
cd /app/backend
alembic upgrade head && echo "Alembic migrations ran successfully"

# Start FastAPI application
echo "Starting FastAPI application"
cd /app
exec gunicorn --bind 0.0.0.0:7889 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api

