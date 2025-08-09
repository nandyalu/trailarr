# Bare Metal Installation

Trailarr can be installed directly on Debian-based systems without Docker. This installation method provides optimal performance with native GPU hardware acceleration support, making it ideal for environments where Docker GPU passthrough is complex (such as Proxmox LXC containers).

!!! info "System Requirements"
    - Debian-based Linux distribution (Ubuntu 20.04+, Debian 11+, etc.)
    - User account with sudo privileges
    - curl, wget, and git
    - At least 4GB of free disk space
    - Internet connection for downloading dependencies

!!! warning "Python Version"
    The application requires Python 3.13.5. The installer will automatically detect and install this version if not available on your system.

## Quick Installation

### One-Command Installation

Run this single command to download and install Trailarr:

```bash
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/install.sh | bash
```

This command will:

1. Download the latest Trailarr release
2. Extract the installation scripts
3. Run the interactive installation process
4. Set up GPU hardware acceleration (if available)
5. Configure the systemd service

### Alternative: Clone and Install

If you prefer to review the code first:

```bash
git clone https://github.com/nandyalu/trailarr.git
cd trailarr
./scripts/baremetal/install.sh
```

## Installation Process

The installer will guide you through the following steps:

### 1. System Verification
- Checks for Debian-based distribution
- Verifies user has sudo privileges
- Installs required system dependencies

### 2. Python 3.13.5 Setup
- Detects if Python 3.13.5 is already installed
- Downloads and installs Python locally if needed
- Creates isolated virtual environment

### 3. GPU Hardware Detection
- Automatically detects NVIDIA, Intel, and AMD GPUs
- Tests hardware acceleration capabilities
- Identifies required drivers and groups

### 4. Interactive Configuration

The installer will prompt you for:

#### Monitor Interval
How often Trailarr checks for new content:
- **3600** (1 hour) - High responsiveness, higher system load
- **10800** (3 hours) - **Recommended** balance
- **21600** (6 hours) - Lower system load, slower detection

#### Wait for Media Files
- **Yes** (recommended) - Download trailers only after media files exist
- **No** - Download trailers immediately when added to Radarr/Sonarr

#### Hardware Acceleration
If GPUs are detected, you can:
- Enable/disable hardware acceleration
- Select which GPU to use (if multiple available)
- Configure driver installation

#### Network Configuration
- Set web interface port (default: 7889)
- Configure timezone

### 5. Media Tools Installation
- Installs ffmpeg and yt-dlp in application directory
- Sets up environment variables for local binaries
- Creates update scripts for maintenance

### 6. GPU Driver Installation
Based on your selections:
- **NVIDIA**: Installs CUDA drivers and runtime
- **Intel**: Installs VAAPI drivers and libraries  
- **AMD**: Installs VAAPI drivers for AMD GPUs
- Adds user to required groups for GPU access

### 7. Service Configuration
- Creates systemd service with security hardening
- Sets up automatic startup
- Configures logging and restart policies

## Directory Structure

After installation, files are organized as follows:

```
/opt/trailarr/              # Application installation
├── backend/                # Python application code
├── frontend-build/         # Web interface files
├── assets/                 # Static assets and images
├── scripts/                # Maintenance and startup scripts
├── bin/                    # Local binaries (ffmpeg, yt-dlp)
├── venv/                   # Python virtual environment
├── python/                 # Local Python installation (if needed)
└── .env                    # Configuration file

/var/lib/trailarr/          # Application data
├── logs/                   # Application logs
├── backups/                # Automatic database backups
├── web/images/             # Downloaded trailer files
├── config/                 # Configuration files
└── trailarr.db            # SQLite database

/var/log/trailarr/          # System logs
└── trailarr.log           # Service logs

/etc/systemd/system/        # Service configuration
└── trailarr.service       # Systemd service file
```

## Hardware Acceleration

### GPU Support

The installer automatically detects and configures:

#### NVIDIA GPUs
- **Requirements**: NVIDIA graphics card with CUDA support
- **Drivers**: Automatically installs nvidia-driver and CUDA runtime
- **Acceleration**: Uses NVENC/NVDEC for video processing
- **Note**: Reboot may be required after driver installation

#### Intel GPUs  
- **Requirements**: Intel integrated graphics or Arc GPUs
- **Drivers**: Installs Intel Media Driver and VAAPI libraries
- **Acceleration**: Uses Intel Quick Sync Video (QSV)
- **Formats**: H.264, HEVC, VP8, VP9, AV1 (depending on hardware)

#### AMD GPUs
- **Requirements**: AMD Radeon graphics cards
- **Drivers**: Installs Mesa VAAPI drivers
- **Acceleration**: Uses VAAPI for hardware encoding/decoding
- **Formats**: H.264, HEVC, AV1 (depending on hardware)

### GPU Selection

If multiple GPUs are detected:
- The installer will list all available options
- You can choose which GPU to use for acceleration
- Only one GPU can be used at a time
- Configuration can be changed later in `/opt/trailarr/.env`

## Service Management

### Starting and Stopping

```bash
# Start Trailarr
sudo systemctl start trailarr

# Stop Trailarr  
sudo systemctl stop trailarr

# Restart Trailarr
sudo systemctl restart trailarr

# Enable auto-start on boot
sudo systemctl enable trailarr

# Disable auto-start
sudo systemctl disable trailarr
```

### Checking Status

```bash
# Check service status
sudo systemctl status trailarr

# View recent logs
sudo journalctl -u trailarr -n 50

# Follow logs in real-time
sudo journalctl -u trailarr -f

# View application logs
tail -f /var/lib/trailarr/logs/app.log
```

## Configuration

### Main Configuration File

Edit `/opt/trailarr/.env` to modify settings:

```bash
# Application Settings
APP_PORT=7889
APP_DATA_DIR=/var/lib/trailarr
MONITOR_INTERVAL=10800
WAIT_FOR_MEDIA=true

# Hardware Acceleration
ENABLE_HWACCEL=true
HWACCEL_TYPE=nvidia

# Python Environment
PYTHONPATH=/opt/trailarr/backend
PYTHON_EXECUTABLE=/opt/trailarr/venv/bin/python

# Local Binaries
PATH=/opt/trailarr/bin:$PATH
FFMPEG_PATH=/opt/trailarr/bin/ffmpeg
YTDLP_PATH=/opt/trailarr/bin/yt-dlp
```

### Applying Configuration Changes

After editing configuration:

```bash
sudo systemctl restart trailarr
```

## Maintenance

### Updating Trailarr

```bash
# Stop the service
sudo systemctl stop trailarr

# Backup current installation
sudo cp -r /opt/trailarr /opt/trailarr.backup

# Download and run the installer again
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/install.sh | bash

# Start the service
sudo systemctl start trailarr
```

### Updating yt-dlp

yt-dlp is automatically updated during startup, or manually:

```bash
sudo -u trailarr /opt/trailarr/scripts/update_ytdlp_local.sh
```

### Database Backups

Automatic backups are created before each application start:
- Location: `/var/lib/trailarr/backups/`
- Retention: 30 most recent backups
- Format: `trailarr_YYYYMMDDHHMMSS.db`

### Log Rotation

Logs are automatically managed by systemd journald. To configure retention:

```bash
# Edit journald configuration
sudo nano /etc/systemd/journald.conf

# Set log retention (e.g., 7 days)
MaxRetentionSec=7d
SystemMaxUse=500M

# Restart journald
sudo systemctl restart systemd-journald
```

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check service status and logs
sudo systemctl status trailarr
sudo journalctl -u trailarr -n 50

# Common causes:
# - Port already in use
# - Database corruption
# - Missing dependencies
# - Permission issues
```

#### GPU Acceleration Not Working

```bash
# Check GPU status
lspci | grep -i vga
lspci | grep -i nvidia

# Check drivers
nvidia-smi  # For NVIDIA
vainfo      # For Intel/AMD

# Check user groups
groups trailarr
ls -la /dev/dri/
```

#### Permission Errors

```bash
# Fix ownership
sudo chown -R trailarr:trailarr /opt/trailarr
sudo chown -R trailarr:trailarr /var/lib/trailarr

# Check service user
sudo systemctl show trailarr | grep User
```

#### Port Conflicts

```bash
# Check what's using the port
sudo netstat -tlnp | grep :7889
sudo lsof -i :7889

# Change port in configuration
sudo nano /opt/trailarr/.env
# Edit APP_PORT=7889 to different port
sudo systemctl restart trailarr
```

### Getting Help

- **GitHub Issues**: [Report bugs and get support](https://github.com/nandyalu/trailarr/issues)
- **Documentation**: [Complete documentation](https://github.com/nandyalu/trailarr/docs)
- **Logs**: Always include logs when reporting issues

## Uninstallation

### Quick Uninstall

```bash
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/uninstall.sh | bash
```

### Manual Uninstall

```bash
# Stop and disable service
sudo systemctl stop trailarr
sudo systemctl disable trailarr

# Remove service file
sudo rm /etc/systemd/system/trailarr.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/trailarr

# Remove data (optional - will lose all trailers and configuration)
sudo rm -rf /var/lib/trailarr
sudo rm -rf /var/log/trailarr

# Remove user
sudo userdel trailarr
```

The uninstaller will prompt you to preserve data for future reinstallations.

## Comparison with Docker

| Feature | Docker | Bare Metal |
|---------|--------|------------|
| **Setup Complexity** | Easy | Moderate |
| **Resource Usage** | Higher (container overhead) | Lower (native) |
| **Hardware Access** | Limited (requires passthrough) | Full (direct access) |
| **GPU Support** | Complex in LXC environments | Native support |
| **Performance** | Good | Optimal |
| **Updates** | Container replacement | File-based updates |
| **System Integration** | Isolated | Native systemd service |
| **Troubleshooting** | Container logs | System logs |
| **Best For** | Quick setup, isolated environments | Performance, complex GPU setups |

Choose bare metal installation when you need maximum performance, have complex GPU requirements, or are running in environments where Docker GPU passthrough is challenging.
# For amd64
curl -L -o /tmp/ffmpeg.tar.xz "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"

# For arm64
curl -L -o /tmp/ffmpeg.tar.xz "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"

# Extract and install
mkdir -p /tmp/ffmpeg
tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
sudo cp /tmp/ffmpeg/bin/* /usr/local/bin/
rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg
```

#### 3. Create User and Directories

```bash
# Create trailarr user
sudo useradd -r -d /opt/trailarr -s /bin/bash -m trailarr

# Create directories
sudo mkdir -p /opt/trailarr /var/lib/trailarr /var/log/trailarr

# Set ownership
sudo chown -R trailarr:trailarr /opt/trailarr /var/lib/trailarr /var/log/trailarr
```

#### 4. Install Trailarr

```bash
# Copy application files
sudo cp -r backend/ /opt/trailarr/
sudo cp -r frontend-build/ /opt/trailarr/
sudo cp -r scripts/ /opt/trailarr/
sudo cp -r assets/ /opt/trailarr/

# Create Python virtual environment
sudo -u trailarr python3 -m venv /opt/trailarr/venv

# Install Python dependencies
sudo -u trailarr /opt/trailarr/venv/bin/pip install --upgrade pip
sudo -u trailarr /opt/trailarr/venv/bin/pip install -r /opt/trailarr/backend/requirements.txt

# Make scripts executable
sudo chmod +x /opt/trailarr/scripts/*.sh

# Set proper ownership
sudo chown -R trailarr:trailarr /opt/trailarr
```

#### 5. Create Configuration

Create `/var/lib/trailarr/.env`:

```bash
sudo -u trailarr cat > /var/lib/trailarr/.env << 'EOF'
# Trailarr Configuration
APP_NAME="Trailarr"
APP_PORT=7889
APP_DATA_DIR="/var/lib/trailarr"
TZ="America/New_York"

# Application settings
LOG_LEVEL="INFO"
MONITOR_ENABLED=true
MONITOR_INTERVAL=60

# Trailer settings
TRAILER_RESOLUTION="1080"
TRAILER_AUDIO_FORMAT="aac"
TRAILER_VIDEO_FORMAT="h264"
TRAILER_FILE_FORMAT="mkv"
TRAILER_SUBTITLES_ENABLED=true
TRAILER_EMBED_METADATA=true
TRAILER_WEB_OPTIMIZED=true
TRAILER_HARDWARE_ACCELERATION=true

# Authentication (default: admin/trailarr)
WEBUI_USERNAME="admin"
WEBUI_PASSWORD="$2b$12$CU7h.sOkBp5RFRJIYEwXU.1LCUTD2pWE4p5nsW3k1iC9oZEGVWeum"
EOF
```

#### 6. Create Systemd Service

Create `/etc/systemd/system/trailarr.service`:

```ini
[Unit]
Description=Trailarr - Trailer downloader for Radarr and Sonarr
After=network.target

[Service]
Type=simple
User=trailarr
Group=trailarr
WorkingDirectory=/opt/trailarr
Environment=PYTHONPATH=/opt/trailarr/backend
Environment=APP_DATA_DIR=/var/lib/trailarr
ExecStartPre=/opt/trailarr/scripts/baremetal_pre_start.sh
ExecStart=/opt/trailarr/scripts/baremetal_start.sh
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/trailarr /var/log/trailarr /opt/trailarr/tmp

[Install]
WantedBy=multi-user.target
```

#### 7. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable trailarr
sudo systemctl start trailarr
```

## Configuration

### Default Settings

After installation, Trailarr will be configured with these defaults:

- **URL**: `http://localhost:7889`
- **Username**: `admin`
- **Password**: `trailarr`
- **Data Directory**: `/var/lib/trailarr`
- **Log Directory**: `/var/log/trailarr`

### Configuration File

The main configuration file is located at `/var/lib/trailarr/.env`. You can edit this file to customize Trailarr's behavior:

```bash
sudo -u trailarr nano /var/lib/trailarr/.env
```

After making changes, restart Trailarr:

```bash
sudo systemctl restart trailarr
```

### Environment Variables

All Docker environment variables are supported in bare metal installations. See the [environment variables reference](../references/environment-variables.md) for a complete list.

## Service Management

### Starting and Stopping

```bash
# Start Trailarr
sudo systemctl start trailarr

# Stop Trailarr
sudo systemctl stop trailarr

# Restart Trailarr
sudo systemctl restart trailarr

# Check status
sudo systemctl status trailarr
```

### Enabling Auto-start

```bash
# Enable auto-start on boot
sudo systemctl enable trailarr

# Disable auto-start
sudo systemctl disable trailarr
```

### Viewing Logs

```bash
# View live logs
sudo journalctl -u trailarr -f

# View recent logs
sudo journalctl -u trailarr -n 100

# View logs since boot
sudo journalctl -u trailarr -b
```

## Hardware Acceleration

Bare metal installations have better hardware acceleration support since there's no container layer. Trailarr will automatically detect and use available hardware acceleration:

### NVIDIA GPU

If you have an NVIDIA GPU with drivers installed:

1. Install NVIDIA drivers and CUDA if not already installed
2. Ensure the trailarr user can access GPU devices:
   ```bash
   sudo usermod -a -G video trailarr
   ```
3. Restart Trailarr:
   ```bash
   sudo systemctl restart trailarr
   ```

### Intel Quick Sync Video (QSV)

For Intel GPUs with QSV support:

1. Ensure `/dev/dri` devices exist and are accessible:
   ```bash
   sudo usermod -a -G video trailarr
   sudo usermod -a -G render trailarr
   ```
2. Restart Trailarr:
   ```bash
   sudo systemctl restart trailarr
   ```

## Updating

To update Trailarr on bare metal installations:

1. Stop the service:
   ```bash
   sudo systemctl stop trailarr
   ```

2. Download the new version:
   ```bash
   cd /tmp
   git clone https://github.com/nandyalu/trailarr.git trailarr-new
   cd trailarr-new
   ```

3. Update application files:
   ```bash
   sudo cp -r backend/ /opt/trailarr/
   sudo cp -r frontend-build/ /opt/trailarr/
   sudo cp -r scripts/ /opt/trailarr/
   sudo cp -r assets/ /opt/trailarr/
   sudo chown -R trailarr:trailarr /opt/trailarr
   ```

4. Update dependencies:
   ```bash
   sudo -u trailarr /opt/trailarr/venv/bin/pip install --upgrade -r /opt/trailarr/backend/requirements.txt
   ```

5. Start the service:
   ```bash
   sudo systemctl start trailarr
   ```

## Uninstallation

To uninstall Trailarr:

```bash
# From the Trailarr source directory
./uninstall.sh
```

Or manually:

```bash
# Stop and disable service
sudo systemctl stop trailarr
sudo systemctl disable trailarr

# Remove service file
sudo rm /etc/systemd/system/trailarr.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/trailarr

# Optionally remove user and data
sudo userdel trailarr
sudo rm -rf /var/lib/trailarr /var/log/trailarr
```

## Troubleshooting

### Service Won't Start

1. Check the service status:
   ```bash
   sudo systemctl status trailarr
   ```

2. Check logs for errors:
   ```bash
   sudo journalctl -u trailarr -n 50
   ```

3. Verify permissions:
   ```bash
   ls -la /opt/trailarr/
   ls -la /var/lib/trailarr/
   ```

### Permission Issues

If you encounter permission issues:

```bash
# Fix ownership
sudo chown -R trailarr:trailarr /opt/trailarr /var/lib/trailarr /var/log/trailarr

# Fix permissions
sudo chmod -R 755 /opt/trailarr
sudo chmod +x /opt/trailarr/scripts/*.sh
```

### Database Migration Issues

If database migrations fail:

1. Check the backup directory:
   ```bash
   ls -la /var/lib/trailarr/backups/
   ```

2. Restore from backup if needed:
   ```bash
   sudo -u trailarr cp /var/lib/trailarr/backups/trailarr_YYYYMMDDHHMMSS.db /var/lib/trailarr/trailarr.db
   ```

3. Restart the service:
   ```bash
   sudo systemctl restart trailarr
   ```

## Comparison with Docker

| Feature | Docker | Bare Metal |
|---------|--------|------------|
| Installation Complexity | Easy | Moderate |
| Resource Usage | Higher (container overhead) | Lower |
| Hardware Acceleration | Complex setup required | Native support |
| Updates | Simple (new container) | Manual file replacement |
| Isolation | Complete | Process-level |
| GPU Passthrough | Difficult in LXC | Native access |
| System Integration | Limited | Full access |