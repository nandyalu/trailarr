#!/bin/sh

# Set TimeZone based on env variable
echo "Setting TimeZone to $TZ"
echo $TZ > /etc/timezone && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

# Create data folder for storing database and other config files
mkdir -p /data/logs && chown -R vscode:vscode /data

# Run Alembic migrations
echo "Running Alembic migrations"
cd backend
alembic upgrade head && echo "Alembic migrations ran successfully"

# Install Angular dependencies
echo "Installing Angular dependencies"
cd ../frontend && npm install

# Start Angular application
# echo "Building Angular application"
# cd /app/frontend && nohup ng serve &

# Start FastAPI application
# echo "Starting FastAPI application"
# cd /app
# exec gunicorn --bind 0.0.0.0:7888 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api

echo "Dev container started successfully!"