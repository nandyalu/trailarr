#!/bin/sh

# THIS SCRIPT WILL BE RUN AS THE NON-ROOT USER 'appuser' IN THE CONTAINER

echo "Running application as user: $(whoami)"

# Run Alembic migrations
echo "Running database migrations with Alembic"
cd /app/backend
alembic upgrade head && echo "Database migrations ran successfully!"

# Start FastAPI application
echo "Starting Trailarr application"
cd /app
exec gunicorn --bind 0.0.0.0:7889 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api