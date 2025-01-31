#!/bin/sh

# Set TimeZone based on env variable
echo "Setting TimeZone to $TZ"
echo $TZ > /etc/timezone && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

# Create data folder for storing database and other config files
mkdir -p /config/logs && chown -R vscode:vscode /config

echo "Checking for GPU availability..."
# Check for NVIDIA GPU
export NVIDIA_GPU_AVAILABLE="false"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi > /dev/null 2>&1; then
        echo "NVIDIA GPU is available."
        export NVIDIA_GPU_AVAILABLE="true"
    else
        echo "NVIDIA GPU is not available."
    fi
else
    echo "nvidia-smi command not found."
fi

# Check if /dev/dri exists
export QSV_GPU_AVAILABLE="false"
if [ -d /dev/dri ]; then
    # Check for Intel GPU
    if ls /dev/dri | grep -q "renderD"; then
        # Intel QSV might be available. Further check for Intel-specific devices
        if lspci | grep -iE 'Display|VGA' | grep -i 'Intel'; then
            export QSV_GPU_AVAILABLE="true"
            echo "Intel GPU detected. Intel QSV is likely available."
        else
            echo "No Intel GPU detected. Intel QSV is not available."
        fi
    else
        echo "Intel QSV not detected. No renderD devices found in /dev/dri."
    fi
else
    echo "Intel QSV is not available. /dev/dri does not exist."
fi

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