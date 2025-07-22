#!/bin/sh


# Ensure Node.js and npm are in the PATH
export PATH=$PATH:/usr/local/bin:/usr/local/share/nvm/current/bin
echo $PATH

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
        # Intel GPU might be available. Check for Intel-specific devices
        if lspci | grep -iE 'Display|VGA|3D' | grep -iE 'Intel|ARC' > /dev/null 2>&1; then
            export GPU_AVAILABLE_INTEL="true"
            echo "Intel GPU detected. Intel hardware acceleration (VAAPI) is available."
        else
            echo "No Intel GPU detected. Intel QSV is not available."
        fi
    else
        echo "Intel QSV not detected. No renderD devices found in /dev/dri."
    fi
else
    echo "Intel GPU is not available. /dev/dri does not exist."
fi

echo "Checking for AMD GPU availability..."
export GPU_AVAILABLE_AMD="false"
if [ -d /dev/dri ]; then
    # Check for AMD GPU
    if ls /dev/dri | grep -q "renderD"; then
        # AMD GPU might be available. Check for AMD-specific devices
        if lspci | grep -iE 'Display|VGA|3D' | grep -iE 'AMD|ATI|Radeon' > /dev/null 2>&1; then
            export GPU_AVAILABLE_AMD="true"
            echo "AMD GPU detected. AMD hardware acceleration (AMF) is available."
        else
            echo "No AMD GPU detected. AMD hardware acceleration not available."
        fi
    else
        echo "AMD GPU not detected. No renderD devices found in /dev/dri."
    fi
else
    echo "AMD GPU is not available. /dev/dri does not exist."
fi

# Check the version of yt-dlp and store it in a global environment variable
YTDLP_VERSION=$(yt-dlp --version)
export YTDLP_VERSION

# Run Alembic migrations
echo "Running Alembic migrations"
cd backend
alembic upgrade head && echo "Alembic migrations ran successfully"

# Install Angular & dependencies
echo "Installing Angular and it's dependencies"
npm install -g @angular/cli@19.2.10
cd ../frontend && npm install
ng completion

# Start Angular application
# echo "Building Angular application"
# cd /app/frontend && nohup ng serve &

# Start FastAPI application
# echo "Starting FastAPI application"
# cd /app
# exec gunicorn --bind 0.0.0.0:7888 -k uvicorn.workers.UvicornWorker backend.main:trailarr_api

echo "Dev container started successfully!"