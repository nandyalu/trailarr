# Bare Metal Installation

Trailarr can be installed directly on Debian-based systems without Docker. This installation method is ideal for users who prefer bare metal installations or have hardware acceleration requirements that are difficult to achieve with Docker (such as GPU passthrough in Proxmox LXC environments).

!!! info "System Requirements"
    - Debian-based Linux distribution (Ubuntu, Debian, etc.)
    - Python 3.8 or higher
    - curl and wget
    - sudo privileges
    - At least 2GB of free disk space

## Installation

### Quick Installation

1. Download or clone the Trailarr source code:
   ```bash
   git clone https://github.com/nandyalu/trailarr.git
   cd trailarr
   ```

2. Run the installation script:
   ```bash
   ./install.sh
   ```

3. Follow the prompts to complete the installation.

4. Start Trailarr:
   ```bash
   sudo systemctl enable trailarr
   sudo systemctl start trailarr
   ```

### Manual Installation

If you prefer to install manually or need to customize the installation:

#### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv curl wget xz-utils git sqlite3 pciutils tzdata ca-certificates
```

#### 2. Install ffmpeg

The installation script will automatically download and install the latest ffmpeg build for your architecture. If you prefer to install manually:

```bash
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