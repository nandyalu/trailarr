# Trailarr Bare Metal Installation Scripts

This directory contains all the scripts and components needed for bare metal installation of Trailarr on Debian-based systems.

## Overview

The bare metal installation provides native system integration with optimal performance for GPU hardware acceleration, especially useful in environments where Docker GPU passthrough is complex (like Proxmox LXC containers).

## Script Architecture

### Main Installation Scripts

- **`install.sh`** - Main installation script with comprehensive setup
- **`uninstall.sh`** - Complete uninstallation with data preservation options

### Modular Components

- **`install_python.sh`** - Python 3.13.5 installation and setup
- **`gpu_setup.sh`** - GPU detection and driver installation
- **`install_media_tools.sh`** - yt-dlp and ffmpeg installation in app directory
- **`interactive_config.sh`** - Interactive configuration prompts
- **`baremetal_pre_start.sh`** - Pre-start environment setup
- **`baremetal_start.sh`** - Application startup script

## Installation Process

### Quick Install Command

Users can install Trailarr by running:

```bash
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/install.sh | bash
```

### Installation Steps

1. **System Checks** - Verifies Debian-based OS and user permissions
2. **Dependencies** - Installs required system packages
3. **User Setup** - Creates `trailarr` user and directory structure
4. **Python Installation** - Installs Python 3.13.5 (system or local)
5. **GPU Detection** - Detects and configures GPU hardware acceleration
6. **Media Tools** - Installs ffmpeg and yt-dlp locally in app directory
7. **Interactive Config** - Prompts for application settings and GPU preferences
8. **Driver Installation** - Installs required GPU drivers system-wide
9. **Service Creation** - Creates and configures systemd service

### Directory Structure

```
/opt/trailarr/              # Application installation
├── backend/                # Python application
├── frontend-build/         # Web interface
├── assets/                 # Static assets
├── scripts/                # All scripts including modular ones
├── bin/                    # Local binaries (ffmpeg, yt-dlp)
├── venv/                   # Python virtual environment
├── tmp/                    # Temporary files
└── .env                    # Configuration file

/var/lib/trailarr/          # Data directory
├── logs/                   # Application logs
├── backups/                # Database backups
├── web/images/             # Downloaded trailers
└── trailarr.db            # SQLite database

/var/log/trailarr/          # System logs
```

## Features

### GPU Hardware Acceleration

- **Auto-detection** of NVIDIA, Intel, and AMD GPUs
- **Driver installation** for system-wide GPU support
- **User group setup** for GPU access permissions
- **Interactive selection** when multiple GPUs are available
- **Fallback support** when no GPU hardware is detected

### Python Management

- **Version checking** for Python 3.13.5 system installation
- **Local installation** if system version not available
- **Virtual environment** isolation for dependencies
- **Cross-architecture** support (amd64, arm64)

### Media Tools

- **Local installation** of ffmpeg and yt-dlp in app directory
- **Environment variables** to prioritize local versions
- **Auto-update** mechanism for yt-dlp
- **Architecture detection** for optimal ffmpeg builds

### Interactive Configuration

- **Monitor interval** setting (how often to check for new content)
- **Wait for media** option (download trailers immediately or wait for files)
- **GPU selection** when multiple hardware acceleration options available
- **Port configuration** for web interface

### Service Integration

- **Systemd service** with security hardening
- **Auto-start** capability with `systemctl enable`
- **Proper shutdown** handling and restart policies
- **Environment isolation** and protection

## Usage

### Installation

```bash
# Download and run installer
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/install.sh | bash

# Or download source and run locally
git clone https://github.com/nandyalu/trailarr.git
cd trailarr
./scripts/baremetal/install.sh
```

### Service Management

```bash
# Start the service
sudo systemctl start trailarr

# Enable auto-start
sudo systemctl enable trailarr

# Check status
sudo systemctl status trailarr

# View logs
sudo journalctl -u trailarr -f

# Stop the service
sudo systemctl stop trailarr
```

### Uninstallation

```bash
# Download and run uninstaller
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/uninstall.sh | bash

# Or run from source
./scripts/baremetal/uninstall.sh
```

## Configuration

The main configuration is stored in `/opt/trailarr/.env`:

```bash
# Application Settings
APP_PORT=7889
APP_DATA_DIR=/var/lib/trailarr
MONITOR_INTERVAL=10800
WAIT_FOR_MEDIA=true

# Hardware Acceleration
ENABLE_HWACCEL=true
HWACCEL_TYPE=nvidia

# Installation Mode
INSTALLATION_MODE=baremetal
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure user has sudo privileges
2. **GPU Not Detected**: Check hardware drivers and /dev/dri permissions
3. **Service Won't Start**: Check logs with `journalctl -u trailarr`
4. **Port Conflicts**: Change APP_PORT in .env file and restart

### Log Locations

- **Service logs**: `sudo journalctl -u trailarr`
- **Application logs**: `/var/lib/trailarr/logs/`
- **System logs**: `/var/log/trailarr/`

### Reset Configuration

```bash
# Stop service
sudo systemctl stop trailarr

# Edit configuration
sudo nano /opt/trailarr/.env

# Restart service
sudo systemctl start trailarr
```

## Comparison with Docker

| Feature | Docker | Bare Metal |
|---------|--------|------------|
| Setup Complexity | Easy | Moderate |
| Resource Usage | Higher | Lower |
| Hardware Access | Limited | Full |
| GPU Passthrough | Complex in LXC | Native |
| Updates | Container replacement | File-based |
| System Integration | Isolated | Native |
| Performance | Good | Optimal |

## Support

For issues and support:
- [GitHub Issues](https://github.com/nandyalu/trailarr/issues)
- [Documentation](https://github.com/nandyalu/trailarr/docs)
- [Discord Community](https://discord.gg/trailarr)