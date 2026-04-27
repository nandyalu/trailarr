# Direct Installation

Trailarr supports native direct installation on **Linux, macOS, and Windows** — no Docker required.
The only prerequisite is [`uv`](https://docs.astral.sh/uv/), a fast Python package manager that also manages Python versions.

!!! tip "Need more control?"
    See the [Self Install](self-install.md) guide if the installer script doesn't work in your
    environment, or if you want to set up each step manually.

!!! info "System Requirements"
    - Linux (Ubuntu 20.04+ / Debian 11+ / Fedora 38+ / Arch), macOS 13+, or Windows 10/11
    - Internet connection
    - At least 2 GB of free disk space
    - For GPU hardware acceleration: NVIDIA, Intel, or AMD GPU (optional)

---

## Step 1 — Install uv

=== "Linux / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    Then restart your shell (or run `source ~/.bashrc` / `source ~/.zshrc`).

=== "Windows"

    Open PowerShell and run:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
    Restart PowerShell after installation.

---

## Step 2 — Install Trailarr

=== "Linux / macOS"

    ```bash
    curl -LsSf https://raw.githubusercontent.com/nandyalu/trailarr/main/install.sh | sudo sh
    ```

=== "Windows"

    Download [install.ps1](https://raw.githubusercontent.com/nandyalu/trailarr/main/install.ps1),
    then right-click it and choose **Run with PowerShell** (it will self-elevate to Administrator).

    Or from an elevated PowerShell:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force
    irm https://raw.githubusercontent.com/nandyalu/trailarr/main/install.ps1 | iex
    ```

The installer will:

1. Download the latest release (includes pre-built web interface)
2. Set up an isolated Python environment with `uv sync`
3. Download the correct ffmpeg static binary for your OS and CPU architecture
4. Ask you to choose a port (default `7889`)
5. Create and start a system service (systemd / launchd / Windows Service)
6. Detect GPU hardware and display driver installation instructions

---

## Directory Structure

=== "Linux"

    ```
    /opt/trailarr/              # Application
    ├── backend/                # Python source + .venv/
    ├── frontend-build/         # Web interface
    ├── bin/                    # ffmpeg, ffprobe
    └── scripts/                # start.py, cli/

    /var/lib/trailarr/          # Data (persists across updates)
    ├── trailarr.db             # SQLite database
    ├── .env                    # Configuration
    ├── backups/                # Automatic DB backups (30 kept)
    ├── logs/                   # Application logs
    └── web/images/             # Downloaded images

    /etc/systemd/system/trailarr.service
    ```

=== "macOS"

    ```
    /usr/local/opt/trailarr/    # Application
    ├── backend/                # Python source + .venv/
    ├── frontend-build/         # Web interface
    ├── bin/                    # ffmpeg, ffprobe
    └── scripts/                # start.py, cli/

    ~/.local/share/trailarr/    # Data (persists across updates)
    ├── trailarr.db
    ├── .env
    ├── backups/
    ├── logs/
    └── web/images/

    ~/Library/LaunchAgents/com.trailarr.app.plist
    ```

=== "Windows"

    ```
    C:\Program Files\Trailarr\  # Application
    ├── backend\                # Python source + .venv\
    ├── frontend-build\         # Web interface
    ├── bin\                    # ffmpeg.exe, ffprobe.exe, nssm.exe
    └── scripts\                # start.py, cli\

    C:\ProgramData\Trailarr\    # Data (persists across updates)
    ├── trailarr.db
    ├── .env
    ├── backups\
    ├── logs\
    └── web\images\

    Windows Service: "Trailarr"
    ```

---

## Service Management

Use the `trailarr` CLI that is installed automatically:

```bash
trailarr run        # Start the service
trailarr stop       # Stop the service
trailarr restart    # Restart the service
trailarr status     # Show current status
trailarr logs       # Show last 50 log lines
trailarr logs 200   # Show last 200 log lines
trailarr update     # Update to the latest version
trailarr uninstall  # Remove Trailarr
```

!!! note "Windows"
    On Windows, open a PowerShell with Administrator rights before running `trailarr` commands
    that affect the service (run, stop, restart, update, uninstall).

You can also use OS-native tools directly:

=== "Linux"

    ```bash
    sudo systemctl start trailarr
    sudo systemctl stop trailarr
    sudo systemctl status trailarr
    sudo journalctl -u trailarr -f          # Follow live logs
    ```

=== "macOS"

    ```bash
    launchctl start com.trailarr.app
    launchctl stop com.trailarr.app
    launchctl list com.trailarr.app
    tail -f ~/Library/Logs/trailarr/trailarr.log
    ```

=== "Windows"

    ```powershell
    Start-Service Trailarr
    Stop-Service Trailarr
    Get-Service Trailarr
    Get-Content "C:\ProgramData\Trailarr\logs\trailarr.log" -Tail 50 -Wait
    ```

---

## GPU Hardware Acceleration

At the end of installation, Trailarr detects your GPU hardware and displays the exact
commands needed to install drivers.  **Drivers are not installed automatically** — you
review and run the commands yourself.

After installing drivers, restart Trailarr and enable hardware acceleration in
**Settings → Video Processing**.

### Supported acceleration

| GPU | Linux | macOS | Windows |
|---|---|---|---|
| NVIDIA | CUDA / NVENC | — | NVENC |
| Intel | VAAPI | Metal (built-in) | DirectX |
| AMD | VAAPI | Metal (built-in) | DirectX |

### Common driver commands

=== "NVIDIA (Linux)"

    ```bash
    # Ubuntu / Debian
    sudo apt install nvidia-driver-535

    # Fedora
    sudo dnf install akmod-nvidia

    # Arch
    sudo pacman -S nvidia
    ```

=== "Intel (Linux)"

    ```bash
    # Ubuntu / Debian
    sudo apt install intel-media-va-driver intel-media-va-driver-non-free libva-drm2

    # Fedora
    sudo dnf install intel-media-driver libva

    # Arch
    sudo pacman -S intel-media-driver libva
    ```

=== "AMD (Linux)"

    ```bash
    # Ubuntu / Debian
    sudo apt install mesa-va-drivers libva-drm2

    # Fedora
    sudo dnf install mesa-va-drivers libva

    # Arch
    sudo pacman -S mesa libva
    ```

=== "Windows"

    - **NVIDIA** — [GeForce Experience](https://www.nvidia.com/en-us/geforce/geforce-experience/) or [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx)
    - **AMD** — [AMD Adrenalin Software](https://www.amd.com/en/support)
    - **Intel** — [Intel Graphics Driver](https://www.intel.com/content/www/us/en/download-center/home.html)

!!! note "macOS"
    Metal hardware acceleration is built-in — no extra drivers are needed.

---

## Configuration

All settings can be changed from the **Trailarr web interface** after installation.
The configuration file is at:

| OS | Path |
|---|---|
| Linux | `/var/lib/trailarr/.env` |
| macOS | `~/.local/share/trailarr/.env` |
| Windows | `C:\ProgramData\Trailarr\.env` |

!!! note ""
    Restart the Trailarr service after editing `.env` manually.

---

## Updating

```bash
trailarr update
```

This will:

1. Stop the service
2. Back up your database and `.env` to the `backups/` folder
3. Download the latest release
4. Run `uv sync` to update Python dependencies
5. Restart the service

Your data directory is **never modified** during an update.

---

## Uninstalling

```bash
trailarr uninstall
```

You will be asked to confirm before anything is removed.
This removes the application, service, and CLI.
The data directory is also removed — back it up first if needed.

---

## Troubleshooting

### Service won't start

```bash
# Linux
sudo journalctl -u trailarr -n 100

# macOS
cat ~/Library/Logs/trailarr/trailarr.log

# Windows (PowerShell)
Get-Content "C:\ProgramData\Trailarr\logs\trailarr.log" -Tail 100
```

Common causes: port already in use, database corruption, missing `uv` or ffmpeg.

### Port conflict

Edit the `.env` file and change `APP_PORT`, then restart the service.

```bash
# Check what's on port 7889
# Linux / macOS
lsof -i :7889
# Windows
netstat -ano | findstr :7889
```

### Permission errors (Linux)

```bash
sudo chown -R trailarr:trailarr /opt/trailarr /var/lib/trailarr
```

### GPU acceleration not working

Verify drivers are installed and detected at startup:

```bash
# NVIDIA
nvidia-smi

# Intel / AMD (Linux)
vainfo

# Check Trailarr logs for "GPU detected" lines
trailarr logs 100
```

Then confirm hardware acceleration is enabled in **Settings → Video Processing**.

---

## Comparison: Direct vs Docker

| | Docker | Direct |
|---|---|---|
| **Setup complexity** | Easy | Moderate (uv required) |
| **GPU support** | Complex in LXC/Proxmox | Native (direct driver access) |
| **Performance** | Good | Optimal (no container overhead) |
| **Resource usage** | Higher | Lower |
| **Updates** | `docker pull` | `trailarr update` |
| **System integration** | Isolated | Native service (systemd / launchd / SCM) |
| **Best for** | Quick setup, isolated environments | Maximum performance, complex GPU setups |

Choose direct installation when you need full GPU hardware access, run in an
environment where Docker GPU passthrough is difficult (e.g., Proxmox LXC), or
simply prefer a native system service.
