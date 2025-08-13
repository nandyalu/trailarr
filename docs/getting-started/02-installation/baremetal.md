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
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/scripts/baremetal/install.sh | sudo bash
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

The installer will guide you through installation process.


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
└── python/                 # Local Python installation (if needed)

/var/lib/trailarr/          # Application data
├── logs/                   # Application logs
├── backups/                # Automatic database backups
├── web/images/             # Image files used in Trailarr
├── .env                    # Configuration Environment Variables
└── trailarr.db             # SQLite database

/var/log/trailarr/          # System logs
└── trailarr.log            # Service logs

/etc/systemd/system/        # Service configuration
└── trailarr.service        # Systemd service file
```

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

Most of the options can be changed from the web UI after installation.

!!! warning
   `APP_DATA_DIR` cannot be changed as installer depends on that!

Main Configuration File is located in `/var/lib/trailarr/.env` if you want to modify later.

!!! note 
   Restart Trailarr service after configuration change.

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

yt-dlp is automatically updated during startup (if enabled), or manually using below command:

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

## Uninstallation

### Quick Uninstall

```bash
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/uninstall.sh | bash
```

The uninstaller will prompt you to preserve data for future reinstallations.

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

# Remove data (optional - will lose all trailarr logs and configuration)
sudo rm -rf /var/lib/trailarr
sudo rm -rf /var/log/trailarr

# Remove user
sudo userdel trailarr
```

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