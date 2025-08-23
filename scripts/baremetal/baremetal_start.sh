#!/bin/bash

# Trailarr Bare Metal Start Script
# This script starts the main Trailarr application for bare metal installations

set -e
echo "+==============================================================================+"

# Installation directories
INSTALL_DIR="/opt/trailarr"
SCRIPTS_DIR="$INSTALL_DIR/scripts"
DATA_DIR="/var/lib/trailarr"

# Initialize logging for runtime  
INSTALL_LOG_FILE="/var/log/trailarr/start.log"
mkdir -p "$(dirname "$INSTALL_LOG_FILE")"
touch "$INSTALL_LOG_FILE"
export INSTALL_LOG_FILE

# Set environment variables
export APP_DATA_DIR=${APP_DATA_DIR:-"/var/lib/trailarr"}
export APP_PORT=${APP_PORT:-7889}
export PYTHONPATH="$INSTALL_DIR/backend"

# Load environment variables from .env file if it exists
if [ -f "$DATA_DIR/.env" ]; then
    source "$DATA_DIR/.env"
fi

# Update PATH for local binaries
if [ -d "$INSTALL_DIR/.local/bin" ]; then
    export PATH="$INSTALL_DIR/.local/bin:$PATH"
fi
if [ -d "$INSTALL_DIR/backend/.venv/bin" ]; then
    export PATH="$INSTALL_DIR/backend/.venv/bin:$PATH"
fi

echo "Running application as user: $(whoami)"
echo "App data directory: $APP_DATA_DIR"

echo "--------------------------------------------------------------------------"
# GPU Detection for runtime environment variables
echo "Detecting GPU hardware for runtime configuration"

# Function to detect GPU devices and set environment variables
detect_gpu_runtime() {
    # Initialize GPU environment variables
    export GPU_AVAILABLE_NVIDIA="false"
    export GPU_AVAILABLE_INTEL="false" 
    export GPU_AVAILABLE_AMD="false"
    export GPU_DEVICE_NVIDIA=""
    export GPU_DEVICE_INTEL=""
    export GPU_DEVICE_AMD=""

    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi > /dev/null 2>&1; then
            export GPU_AVAILABLE_NVIDIA="true"
            GPU_INFO=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | head -1)
            echo "✓ NVIDIA GPU detected: $GPU_INFO"
            echo "  CUDA hardware acceleration available"
        fi
    elif lspci | grep -i nvidia &> /dev/null; then
        echo "⚠ NVIDIA GPU hardware detected but drivers not installed"
        echo "  Install NVIDIA drivers: sudo apt install nvidia-driver-xxx"
        echo "  Then reboot and restart Trailarr"
    fi

    # Check for Intel GPU
    if lspci | grep -i "vga.*intel\|display.*intel" &> /dev/null; then
        export GPU_AVAILABLE_INTEL="true"
        echo "✓ Intel GPU detected"
        echo "  Install Intel GPU tools: sudo apt install intel-media-va-driver vainfo"
        
        # Find Intel GPU device
        for device in /dev/dri/renderD*; do
            if [ -e "$device" ]; then
                syspath=$(udevadm info --query=path --name="$device" 2>/dev/null || echo "")
                if [ -n "$syspath" ]; then
                    fullpath="/sys$syspath/device"
                    if [ -f "$fullpath/vendor" ]; then
                        vendor=$(cat "$fullpath/vendor")
                        if [ "$vendor" = "0x8086" ]; then
                            export GPU_DEVICE_INTEL="$device"
                            break
                        fi
                    fi
                fi
            fi
        done
    fi

    # Check for AMD GPU  
    if lspci | grep -i "vga.*amd\|display.*amd\|vga.*ati\|display.*ati" &> /dev/null; then
        export GPU_AVAILABLE_AMD="true"
        echo "✓ AMD GPU detected"
        echo "  Install AMD GPU tools: sudo apt install mesa-va-drivers vainfo"
        
        # Find AMD GPU device
        for device in /dev/dri/renderD*; do
            if [ -e "$device" ]; then
                syspath=$(udevadm info --query=path --name="$device" 2>/dev/null || echo "")
                if [ -n "$syspath" ]; then
                    fullpath="/sys$syspath/device"
                    if [ -f "$fullpath/vendor" ]; then
                        vendor=$(cat "$fullpath/vendor")
                        if [ "$vendor" = "0x1002" ] || [ "$vendor" = "0x1022" ]; then
                            export GPU_DEVICE_AMD="$device"
                            break
                        fi
                    fi
                fi
            fi
        done
    fi

    # Update .env file with GPU detection results
    if [ -f "$DATA_DIR/.env" ]; then
        # Use a simple approach to update .env file
        sed -i '/^GPU_AVAILABLE_NVIDIA=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_AVAILABLE_INTEL=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_AVAILABLE_AMD=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_DEVICE_NVIDIA=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_DEVICE_INTEL=/d' "$DATA_DIR/.env" 2>/dev/null || true
        sed -i '/^GPU_DEVICE_AMD=/d' "$DATA_DIR/.env" 2>/dev/null || true
        
        echo "GPU_AVAILABLE_NVIDIA=$GPU_AVAILABLE_NVIDIA" >> "$DATA_DIR/.env"
        echo "GPU_AVAILABLE_INTEL=$GPU_AVAILABLE_INTEL" >> "$DATA_DIR/.env"
        echo "GPU_AVAILABLE_AMD=$GPU_AVAILABLE_AMD" >> "$DATA_DIR/.env"
        echo "GPU_DEVICE_NVIDIA=$GPU_DEVICE_NVIDIA" >> "$DATA_DIR/.env"
        echo "GPU_DEVICE_INTEL=$GPU_DEVICE_INTEL" >> "$DATA_DIR/.env"
        echo "GPU_DEVICE_AMD=$GPU_DEVICE_AMD" >> "$DATA_DIR/.env"
    fi
}

# Run GPU detection
detect_gpu_runtime
echo "GPU detection complete"
echo "--------------------------------------------------------------------------"
# Backup database before running migrations
echo "Backing up database before running migrations"
BACKUPS_DIR="${APP_DATA_DIR}/backups"
NEW_DB="${BACKUPS_DIR}/trailarr_$(date +%Y%m%d%H%M%S).db"
OLD_DB="${APP_DATA_DIR}/trailarr.db"

if [ -f "$OLD_DB" ]; then
    echo "Creating database backup"
    mkdir -p "${BACKUPS_DIR}"
    cp "$OLD_DB" "$NEW_DB"
    echo "✓ Database backup created successfully!"
    
    # Keep only the most recent 30 backups and delete the rest
    echo "Cleaning up old backups (keeping most recent 30)"
    BACKUP_COUNT=$(find "$BACKUPS_DIR" -type f -name "trailarr_*.db" 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 30 ]; then
        find "$BACKUPS_DIR" -type f -name "trailarr_*.db" -exec ls -t {} + | tail -n +31 | xargs rm -f
        DEL_COUNT=$((BACKUP_COUNT - 30))
        echo "$DEL_COUNT old backups deleted successfully!"
    else
        echo "Less than 30 backups exist ($BACKUP_COUNT), no backups deleted."
    fi
else
    echo $YELLOW "No existing database found, skipping backup"
fi
echo "Database backup complete"
echo "--------------------------------------------------------------------------"

# Determine Python executable
PYTHON_EXEC="$INSTALL_DIR/backend/.venv/bin/python"
if [ ! -f "$PYTHON_EXEC" ]; then
    # Fallback to system Python if virtual environment doesn't exist
    if [ -n "$PYTHON_EXECUTABLE" ] && [ -f "$PYTHON_EXECUTABLE" ]; then
        PYTHON_EXEC="$PYTHON_EXECUTABLE"
    else
        PYTHON_EXEC="python3"
    fi
fi

# Run Alembic migrations
echo "Running database migrations with Alembic"
echo "Using Python: $PYTHON_EXEC"
cd "$INSTALL_DIR/backend"

if [ -f "$INSTALL_DIR/backend/.venv/bin/alembic" ]; then
    ALEMBIC_CMD="$INSTALL_DIR/backend/.venv/bin/alembic"
else
    ALEMBIC_CMD="$PYTHON_EXEC -m alembic"
fi

echo "Running Alembic migrations"
if $ALEMBIC_CMD upgrade head; then
    echo "✓ Database migrations ran successfully!"
    echo "Database migrations complete"
    echo "--------------------------------------------------------------------------"
else
    echo "✗ Database migrations failed!"
    if [ -f "$NEW_DB" ] && [ -f "$OLD_DB" ]; then
        echo "Restoring backup"
        cp "$NEW_DB" "$OLD_DB"
        echo "✓ Backup restored successfully!"
    fi
    echo "Check logs for details and fix the issue before restarting"
    echo "--------------------------------------------------------------------------"
    exit 1
fi

# Start FastAPI application
echo "+==============================================================================+"
echo "Starting Trailarr application on port $APP_PORT..."
echo "Web interface will be available at: http://localhost:$APP_PORT"
echo "+==============================================================================+"
echo ""

cd "$INSTALL_DIR/backend"

# Determine uvicorn executable
if [ -f "$INSTALL_DIR/backend/.venv/bin/uvicorn" ]; then
    UVICORN_CMD="$INSTALL_DIR/backend/.venv/bin/uvicorn"
else
    UVICORN_CMD="$PYTHON_EXEC -m uvicorn"
fi

exec $UVICORN_CMD main:trailarr_api --host 0.0.0.0 --port "${APP_PORT}"