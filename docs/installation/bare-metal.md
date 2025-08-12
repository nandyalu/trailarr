# Bare Metal Installation

Trailarr supports native installation on Debian-based systems (Ubuntu, Debian) for users who prefer direct system installation over Docker containers.

## Quick Start

Run the one-line installation command:

```bash
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/scripts/baremetal/install.sh | bash
```

## Manual Installation

If you prefer to download and review the installation script first:

```bash
# Download the latest release
wget -O trailarr-latest.tar.gz https://github.com/nandyalu/trailarr/archive/refs/heads/main.tar.gz

# Extract the archive
tar -xzf trailarr-latest.tar.gz

# Run the installation
cd trailarr-main/scripts/baremetal
./install.sh
```

## Installation Features

- **Python 3.13.5 Management**: Automatically detects system Python or installs locally
- **GPU Hardware Acceleration**: Detects NVIDIA, Intel, and AMD GPUs with driver installation guidance
- **Interactive Configuration**: Prompts for app settings during installation
- **Local Media Tools**: Installs ffmpeg and yt-dlp locally (not system-wide)
- **Systemd Integration**: Creates and configures system service

## Hardware Acceleration

The installer will detect your GPU hardware and provide installation commands for necessary drivers:

### NVIDIA GPUs
```bash
sudo apt update && sudo apt install -y nvidia-driver-535
# Reboot required after installation
```

### Intel GPUs
```bash
sudo apt update && sudo apt install -y intel-media-va-driver i965-va-driver vainfo
```

### AMD GPUs
```bash
sudo apt update && sudo apt install -y mesa-va-drivers vainfo
```

**Note**: After installing GPU drivers, restart the Trailarr service to enable hardware acceleration.

## Service Management

After installation, manage Trailarr using systemctl:

```bash
# Start the service
sudo systemctl start trailarr

# Enable auto-start on boot
sudo systemctl enable trailarr

# Check service status
sudo systemctl status trailarr

# View logs
sudo journalctl -u trailarr -f

# Stop the service
sudo systemctl stop trailarr

# Restart the service
sudo systemctl restart trailarr
```

## File Locations

- **Application**: `/opt/trailarr/`
- **Configuration & Data**: `/var/lib/trailarr/`
- **Logs**: `/var/log/trailarr/`
- **Local Tools**: `/opt/trailarr/bin/` (ffmpeg, yt-dlp)

## Configuration

The application uses a `.env` file located in the data directory (`/var/lib/trailarr/.env`) for configuration. Key settings include:

- `APP_DATA_DIR`: Data directory path
- `MONITOR_INTERVAL`: How often to check for new content (minutes)
- `WAIT_FOR_MEDIA`: Whether to wait for media files before downloading trailers
- `FFMPEG_PATH`: Path to ffmpeg binary
- `YTDLP_PATH`: Path to yt-dlp binary
- `GPU_AVAILABLE_*`: GPU availability flags set during installation

## Web Interface

After installation, access the web interface at:
- Default: `http://localhost:7889`
- Custom port configured during installation

## Updating

To update Trailarr:

1. Stop the service: `sudo systemctl stop trailarr`
2. Download the latest release and run the installer again
3. The installer will preserve your configuration and data

## Uninstallation

To remove Trailarr:

```bash
curl -sSL https://raw.githubusercontent.com/nandyalu/trailarr/main/scripts/baremetal/uninstall.sh | bash
```

This will:
- Stop and remove the systemd service
- Remove application files from `/opt/trailarr/`
- Optionally preserve or remove configuration data in `/var/lib/trailarr/`

## Troubleshooting

### Service Won't Start
- Check logs: `sudo journalctl -u trailarr -f`
- Verify configuration: `cat /var/lib/trailarr/.env`
- Ensure data directory permissions: `sudo chown -R trailarr:trailarr /var/lib/trailarr`

### GPU Acceleration Not Working
- Verify drivers are installed
- Check GPU detection: `cat /var/lib/trailarr/.env | grep GPU_`
- Restart service after driver installation: `sudo systemctl restart trailarr`

### Permission Issues
- Ensure trailarr user has proper permissions
- Check that user is in video/render groups for GPU access

## Comparison with Docker

| Feature | Docker | Bare Metal |
|---------|--------|------------|
| Installation Complexity | Simple | Moderate |
| Resource Usage | Higher (container overhead) | Lower (native) |
| Hardware Access | Limited (requires passthrough) | Full (direct access) |
| GPU Support | Complex in virtualized environments | Native with auto-detection |
| Updates | Container replacement | File-based updates |
| System Integration | Isolated | Native systemd service |