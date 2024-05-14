#!/bin/sh

# Create data folder for storing database and other config files
mkdir -p /data/logs && chmod -R 755 /data

# Run Alembic migrations
echo "Running Alembic migrations"
cd /app/backend
alembic upgrade head && echo "Alembic migrations ran successfully"

# Start Angular application
# echo "Starting Angular application"
# cd /app/frontend && nohup ng serve &

# Start FastAPI application
echo "Starting FastAPI application"
cd /app
exec gunicorn --bind 0.0.0.0:7889 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api

