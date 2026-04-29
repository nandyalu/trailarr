# Self Installation

This page is for users who want to install Trailarr manually — step by step, without running the automated installer script. This is useful when:

- The installer script fails or doesn't support your distribution/environment
- You want full control over where files are placed
- You're setting up in a non-standard environment (NAS, container, custom path, etc.)
- You want to understand exactly what the installer does

---

## Prerequisites

| Tool | Install |
|---|---|
| `uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (Linux/macOS)  ·  `irm https://astral.sh/uv/install.ps1 \| iex` (Windows) |
| `curl` or browser | For downloading the release archive |

---

## Step 1 — Get the application files

Choose one option:

### Option A: Download the release archive (recommended)

Download the latest pre-built release from GitHub — this includes the compiled web interface
so you don't need Node.js.

```bash
# Find the latest release URL (Linux / macOS)
curl -s https://api.github.com/repos/nandyalu/trailarr/releases/latest \
  | grep browser_download_url \
  | grep release.tar.gz \
  | cut -d'"' -f4
```

Then download and extract it:

```bash
# Replace the URL with the one from the command above
curl -L -o trailarr-release.tar.gz "https://github.com/nandyalu/trailarr/releases/download/vX.Y.Z/trailarr-vX.Y.Z-release.tar.gz"
tar -xzf trailarr-release.tar.gz
cd trailarr-vX.Y.Z
```

Or you can browse to [github.com/nandyalu/trailarr/releases](https://github.com/nandyalu/trailarr/releases) and download the `*-release.tar.gz` asset manually.

### Option B: Clone the git repository

If you want the very latest code (or to build from source), clone the repo and build the frontend yourself.
This requires **Node.js 24+**.

```bash
git clone https://github.com/nandyalu/trailarr.git
cd trailarr

# Build the Angular frontend (outputs to frontend-build/)
cd frontend
npm ci
npm run build
cd ..
```

---

## Step 2 — Choose your directories

Decide where you want to install Trailarr. The examples below use the same defaults as
the automated installer, but you can use any paths you prefer.

=== "Linux"

    ```bash
    INSTALL_DIR="/opt/trailarr"
    DATA_DIR="/var/lib/trailarr"
    LOG_DIR="/var/log/trailarr"
    ```

=== "macOS"

    ```bash
    INSTALL_DIR="/usr/local/opt/trailarr"
    DATA_DIR="$HOME/.local/share/trailarr"
    LOG_DIR="$HOME/Library/Logs/trailarr"
    ```

=== "Windows"

    ```powershell
    $InstallDir = "C:\Program Files\Trailarr"
    $DataDir    = "C:\ProgramData\Trailarr"
    $LogDir     = "C:\ProgramData\Trailarr\logs"
    ```

---

## Step 3 — Copy application files

=== "Linux / macOS"

    ```bash
    # Create directories
    sudo mkdir -p "$INSTALL_DIR" "$DATA_DIR/logs" "$DATA_DIR/backups" "$DATA_DIR/web/images" "$DATA_DIR/tmp" "$LOG_DIR"

    # Copy files
    sudo cp -r backend        "$INSTALL_DIR/"
    sudo cp -r frontend-build "$INSTALL_DIR/"
    sudo cp -r assets         "$INSTALL_DIR/"
    sudo cp -r scripts        "$INSTALL_DIR/"
    ```

    On Linux, create a dedicated system user (optional but recommended):
    ```bash
    sudo useradd -r -d "$INSTALL_DIR" -s /bin/false trailarr
    sudo chown -R trailarr:trailarr "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
    ```

=== "Windows"

    ```powershell
    New-Item -ItemType Directory -Force -Path $InstallDir, $DataDir, $LogDir,
        "$DataDir\backups", "$DataDir\web\images", "$DataDir\tmp" | Out-Null

    Copy-Item -Recurse backend, frontend-build, assets, scripts -Destination $InstallDir
    ```

---

## Step 4 — Install Python dependencies

=== "Linux"

    If you created a `trailarr` system user in Step 3, run `uv sync` as that user so the
    virtual environment is owned correctly:

    ```bash
    cd "$INSTALL_DIR/backend"
    sudo -u trailarr uv sync --no-cache-dir
    ```

    !!! note "uv not found when using sudo?"
        `sudo -u trailarr` starts a minimal shell that does not inherit your `PATH`, so `uv`
        may not be found even though `which uv` shows it for your own account.
        Pick one fix:

        **Option A — install uv system-wide (recommended):**
        ```bash
        sudo cp "$(which uv)" /usr/local/bin/uv
        sudo chmod +x /usr/local/bin/uv
        # now retry:
        sudo -u trailarr uv sync --no-cache-dir
        ```

        **Option B — pass the full path to uv:**
        ```bash
        sudo -u trailarr "$(which uv)" sync --no-cache-dir
        ```

=== "macOS"

    ```bash
    cd "$INSTALL_DIR/backend"
    uv sync --no-cache-dir
    ```

=== "Windows"

    ```powershell
    cd "$InstallDir\backend"
    uv sync --no-cache-dir
    ```

This creates a `.venv/` directory inside `backend/` and installs all Python dependencies
(including `yt-dlp` and `rich`).

---

## Step 5 — Download ffmpeg

Trailarr needs `ffmpeg` and `ffprobe` binaries. Download the static build for your platform:

| Platform | URL |
|---|---|
| Linux x86_64 | `https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz` |
| Linux arm64 | `https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz` |
| Windows x64 | `https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip` |
| Windows arm64 | `https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-winarm64-gpl.zip` |
| macOS | `https://evermeet.cx/ffmpeg/get/ffmpeg/zip` and `https://evermeet.cx/ffmpeg/get/ffprobe/zip` |

Place the extracted `ffmpeg` and `ffprobe` (or `ffmpeg.exe` / `ffprobe.exe`) binaries somewhere accessible.
The default location the installer uses is `$INSTALL_DIR/bin/`:

=== "Linux"

    ```bash
    sudo mkdir -p "$INSTALL_DIR/bin"

    curl -L -o /tmp/ffmpeg.tar.xz \
      "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"

    tar -xf /tmp/ffmpeg.tar.xz -C /tmp/
    sudo cp /tmp/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg  "$INSTALL_DIR/bin/"
    sudo cp /tmp/ffmpeg-master-latest-linux64-gpl/bin/ffprobe "$INSTALL_DIR/bin/"
    sudo chmod +x "$INSTALL_DIR/bin/ffmpeg" "$INSTALL_DIR/bin/ffprobe"

    # Verify
    "$INSTALL_DIR/bin/ffmpeg" -version
    ```

=== "macOS"

    ```bash
    mkdir -p "$INSTALL_DIR/bin"

    # ffmpeg
    curl -L -o /tmp/ffmpeg.zip "https://evermeet.cx/ffmpeg/get/ffmpeg/zip"
    unzip -o /tmp/ffmpeg.zip -d "$INSTALL_DIR/bin/"

    # ffprobe
    curl -L -o /tmp/ffprobe.zip "https://evermeet.cx/ffmpeg/get/ffprobe/zip"
    unzip -o /tmp/ffprobe.zip -d "$INSTALL_DIR/bin/"

    chmod +x "$INSTALL_DIR/bin/ffmpeg" "$INSTALL_DIR/bin/ffprobe"
    "$INSTALL_DIR/bin/ffmpeg" -version
    ```

    Alternatively, if you have Homebrew:
    ```bash
    brew install ffmpeg
    # Then set FFMPEG_PATH and FFPROBE_PATH in your .env to the brew paths:
    which ffmpeg    # e.g. /opt/homebrew/bin/ffmpeg
    which ffprobe
    ```

=== "Windows"

    ```powershell
    New-Item -ItemType Directory -Force -Path "$InstallDir\bin" | Out-Null

    Invoke-WebRequest -Uri "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" `
        -OutFile "$env:TEMP\ffmpeg.zip"

    Expand-Archive "$env:TEMP\ffmpeg.zip" -DestinationPath "$env:TEMP\ffmpeg_extract" -Force

    $ffBin = Get-ChildItem "$env:TEMP\ffmpeg_extract" -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    Copy-Item $ffBin.FullName "$InstallDir\bin\ffmpeg.exe"
    $fpBin = Get-ChildItem "$env:TEMP\ffmpeg_extract" -Recurse -Filter "ffprobe.exe" | Select-Object -First 1
    Copy-Item $fpBin.FullName "$InstallDir\bin\ffprobe.exe"

    & "$InstallDir\bin\ffmpeg.exe" -version
    ```

---

## Step 6 — Create the .env configuration file

Create `$DATA_DIR/.env` with at minimum these values. Adjust paths to match your choices above.

=== "Linux"

    ```bash
    sudo tee /var/lib/trailarr/.env > /dev/null << 'EOF'
    APP_VERSION=vX.Y.Z
    APP_DATA_DIR=/var/lib/trailarr
    APP_PORT=7889
    APP_MODE="Direct Linux"
    TZ=America/New_York

    FFMPEG_PATH=/opt/trailarr/bin/ffmpeg
    FFPROBE_PATH=/opt/trailarr/bin/ffprobe
    YTDLP_PATH=/opt/trailarr/backend/.venv/bin/yt-dlp
    PYTHON_EXECUTABLE=/opt/trailarr/backend/.venv/bin/python
    PYTHONPATH=/opt/trailarr/backend

    LOG_LEVEL=INFO
    MONITOR_INTERVAL=60
    WAIT_FOR_MEDIA=true
    UPDATE_YTDLP=false
    EOF

    sudo chown trailarr:trailarr /var/lib/trailarr/.env
    ```

=== "macOS"

    ```bash
    cat > "$DATA_DIR/.env" << EOF
    APP_VERSION=vX.Y.Z
    APP_DATA_DIR=$DATA_DIR
    APP_PORT=7889
    APP_MODE="Direct macOS"
    TZ=$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')

    FFMPEG_PATH=$INSTALL_DIR/bin/ffmpeg
    FFPROBE_PATH=$INSTALL_DIR/bin/ffprobe
    YTDLP_PATH=$INSTALL_DIR/backend/.venv/bin/yt-dlp
    PYTHON_EXECUTABLE=$INSTALL_DIR/backend/.venv/bin/python
    PYTHONPATH=$INSTALL_DIR/backend

    LOG_LEVEL=INFO
    MONITOR_INTERVAL=60
    WAIT_FOR_MEDIA=true
    UPDATE_YTDLP=false
    EOF
    ```

=== "Windows"

    ```powershell
    @"
    APP_VERSION=vX.Y.Z
    APP_DATA_DIR=C:\ProgramData\Trailarr
    APP_PORT=7889
    APP_MODE="Direct Windows"
    TZ=America/New_York

    FFMPEG_PATH=C:\Program Files\Trailarr\bin\ffmpeg.exe
    FFPROBE_PATH=C:\Program Files\Trailarr\bin\ffprobe.exe
    YTDLP_PATH=C:\Program Files\Trailarr\backend\.venv\Scripts\yt-dlp.exe
    PYTHON_EXECUTABLE=C:\Program Files\Trailarr\backend\.venv\Scripts\python.exe
    PYTHONPATH=C:\Program Files\Trailarr\backend

    LOG_LEVEL=INFO
    MONITOR_INTERVAL=60
    WAIT_FOR_MEDIA=true
    UPDATE_YTDLP=false
    "@ | Set-Content "$DataDir\.env" -Encoding UTF8
    ```

!!! tip "All settings"
    All other settings (connections, profiles, etc.) can be configured from the web UI.
    See [Environment Variables](../../05-reference/environment-variables.md) for a full reference.

---

## Step 7 — Run database migrations

Before starting for the first time, apply the database migrations:

=== "Linux"

    Run as the `trailarr` user so it can write to `$DATA_DIR`:

    ```bash
    sudo -u trailarr env \
      APP_DATA_DIR="$DATA_DIR" \
      PYTHONPATH="$INSTALL_DIR/backend" \
      "$INSTALL_DIR/backend/.venv/bin/alembic" -c "$INSTALL_DIR/backend/alembic.ini" upgrade head
    ```

=== "macOS"

    ```bash
    cd "$INSTALL_DIR/backend"
    APP_DATA_DIR="$DATA_DIR" PYTHONPATH="$INSTALL_DIR/backend" .venv/bin/alembic upgrade head
    ```

=== "Windows"

    ```powershell
    cd "$InstallDir\backend"
    $env:APP_DATA_DIR = $DataDir
    $env:PYTHONPATH   = "$InstallDir\backend"
    & ".venv\Scripts\alembic.exe" upgrade head
    ```

---

## Step 8 — Test the application

Run Trailarr directly to confirm everything works before setting up a service:

=== "Linux"

    Run as the `trailarr` user so it can write logs and the database to `$DATA_DIR`:

    ```bash
    sudo -u trailarr env \
      APP_DATA_DIR="$DATA_DIR" \
      PYTHONPATH="$INSTALL_DIR/backend" \
      "$INSTALL_DIR/backend/.venv/bin/uvicorn" main:trailarr_api --host 0.0.0.0 --port 7889
    ```

=== "macOS"

    ```bash
    cd "$INSTALL_DIR/backend"
    APP_DATA_DIR="$DATA_DIR" PYTHONPATH="$INSTALL_DIR/backend" .venv/bin/uvicorn main:trailarr_api --host 0.0.0.0 --port 7889
    ```

=== "Windows"

    ```powershell
    cd "$InstallDir\backend"
    $env:APP_DATA_DIR = $DataDir
    $env:PYTHONPATH   = "$InstallDir\backend"
    & ".venv\Scripts\uvicorn.exe" main:trailarr_api --host 0.0.0.0 --port 7889
    ```

Open `http://localhost:7889` in your browser. If you see the Trailarr interface, the setup is working.
Press `Ctrl+C` to stop it before continuing.

---

## Step 9 — Set up a system service

=== "Linux (systemd)"

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
    Environment=PATH=/opt/trailarr/backend/.venv/bin:/usr/local/bin:/usr/bin:/bin
    EnvironmentFile=/var/lib/trailarr/.env
    ExecStart=/opt/trailarr/backend/.venv/bin/python /opt/trailarr/scripts/start/start.py
    Restart=always
    RestartSec=60
    TimeoutStopSec=30

    [Install]
    WantedBy=multi-user.target
    ```

    Enable and start:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable trailarr
    sudo systemctl start trailarr
    sudo systemctl status trailarr
    ```

=== "macOS (launchd)"

    Create `~/Library/LaunchAgents/com.trailarr.app.plist`:

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.trailarr.app</string>
        <key>ProgramArguments</key>
        <array>
            <string>/usr/local/opt/trailarr/backend/.venv/bin/python</string>
            <string>/usr/local/opt/trailarr/scripts/start/start.py</string>
        </array>
        <key>WorkingDirectory</key>
        <string>/usr/local/opt/trailarr</string>
        <key>EnvironmentVariables</key>
        <dict>
            <key>APP_DATA_DIR</key>
            <string>/Users/YOUR_USERNAME/.local/share/trailarr</string>
            <key>PYTHONPATH</key>
            <string>/usr/local/opt/trailarr/backend</string>
        </dict>
        <key>StandardOutPath</key>
        <string>/Users/YOUR_USERNAME/Library/Logs/trailarr/trailarr.log</string>
        <key>StandardErrorPath</key>
        <string>/Users/YOUR_USERNAME/Library/Logs/trailarr/trailarr.log</string>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
    </dict>
    </plist>
    ```

    !!! note ""
        Replace `YOUR_USERNAME` with the output of `whoami`.

    Load the service:
    ```bash
    launchctl load -w ~/Library/LaunchAgents/com.trailarr.app.plist
    launchctl list com.trailarr.app
    ```

=== "Windows (Task Scheduler)"

    Open a **regular PowerShell** (not "Run as Administrator") and run the
    setup script bundled with Trailarr:

    ```powershell
    & "C:\Program Files\Trailarr\scripts\windows\setup-startup.ps1"
    ```

    This registers a Task Scheduler task that starts Trailarr automatically
    when **you** log in, running as your user account so mapped network drives
    and UNC shares are fully accessible.

    Start it immediately without rebooting:

    ```powershell
    Start-ScheduledTask -TaskName "Trailarr"
    ```

    Check that it is running:

    ```powershell
    (Get-ScheduledTask -TaskName "Trailarr").State   # should print "Running"
    ```

    !!! note "Non-default install paths"
        If you installed to a different directory, edit
        `scripts\windows\trailarr-start.ps1` and update the `$InstallDir` and
        `$DataDir` variables before running the setup script.

=== "Run manually (any OS)"

    If you don't want a system service, you can just start Trailarr in a terminal or
    add it to your shell's startup (`.bashrc`, `~/.profile`, etc.):

    **Linux** — run as the `trailarr` user (e.g. add to a `@reboot` cron entry via `sudo -u trailarr crontab -e`):
    ```bash
    sudo -u trailarr env \
      APP_DATA_DIR=/var/lib/trailarr \
      PYTHONPATH=/opt/trailarr/backend \
      /opt/trailarr/backend/.venv/bin/uvicorn main:trailarr_api --host 0.0.0.0 --port 7889
    ```

    **macOS** — add to `~/.profile` or a `@reboot` cron entry:
    ```bash
    cd /usr/local/opt/trailarr/backend
    APP_DATA_DIR="$HOME/.local/share/trailarr" PYTHONPATH=/usr/local/opt/trailarr/backend \
      exec .venv/bin/uvicorn main:trailarr_api --host 0.0.0.0 --port 7889
    ```

---

## Step 10 — (Optional) Install the CLI

The `trailarr` CLI is a convenience wrapper around the Python script at
`scripts/cli/trailarr_cli.py`. Installing it is optional.

=== "Linux / macOS"

    ```bash
    PYTHON="$INSTALL_DIR/backend/.venv/bin/python"
    CLI_SCRIPT="$INSTALL_DIR/scripts/cli/trailarr_cli.py"

    sudo tee /usr/local/bin/trailarr > /dev/null << EOF
    #!/bin/sh
    exec $PYTHON $CLI_SCRIPT "\$@"
    EOF
    sudo chmod +x /usr/local/bin/trailarr

    trailarr status
    ```

=== "Windows"

    ```powershell
    $python    = "C:\Program Files\Trailarr\backend\.venv\Scripts\python.exe"
    $cliScript = "C:\Program Files\Trailarr\scripts\cli\trailarr_cli.py"

    "@echo off`n`"$python`" `"$cliScript`" %*" | `
        Set-Content "C:\Program Files\Trailarr\trailarr.cmd" -Encoding ASCII

    # Add to PATH (run in elevated shell, then restart)
    $path = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($path -notlike "*Program Files\Trailarr*") {
        [Environment]::SetEnvironmentVariable("Path", "$path;C:\Program Files\Trailarr", "Machine")
    }
    ```

---

## GPU Hardware Acceleration

If you have a compatible GPU, install the appropriate drivers and then set the corresponding
environment variables in your `.env` before starting Trailarr:

```ini
# Detected automatically by start.py — set manually if auto-detection fails
GPU_AVAILABLE_NVIDIA=true
GPU_DEVICE_NVIDIA=/dev/dri/renderD128    # Linux only

GPU_AVAILABLE_INTEL=false
GPU_AVAILABLE_AMD=false
```

See [Hardware Acceleration](hardware-acceleration.md) for the full driver installation guide
and supported codec details.

---

## Troubleshooting self-installs

**`uv sync` fails** — Make sure you're running it from the `backend/` directory (where
`pyproject.toml` lives). Check that Python 3.13+ is available: `uv python list`.

**`ffmpeg -version` doesn't work** — The binary may not be executable: `chmod +x ffmpeg ffprobe`.
On macOS, you may need to allow it: **System Settings → Privacy & Security → Allow**.

**"Module not found" errors** — Confirm `PYTHONPATH` points to `$INSTALL_DIR/backend` and that
you're running Python from the `.venv`.

**Database errors on first start** — Run `alembic upgrade head` from `$INSTALL_DIR/backend`
before starting uvicorn.

**Web UI doesn't load (404)** — Check that `frontend-build/` exists inside `$INSTALL_DIR`.
If you cloned the repo, you need to run the Angular build first (Step 1, Option B).

---

## Uninstall

=== "Linux"

    **1. Stop and remove the systemd service:**
    ```bash
    sudo systemctl stop trailarr
    sudo systemctl disable trailarr
    sudo rm /etc/systemd/system/trailarr.service
    sudo systemctl daemon-reload
    ```

    **2. Remove the CLI wrapper** (if installed in Step 10):
    ```bash
    sudo rm -f /usr/local/bin/trailarr
    ```

    **3. Remove application files:**
    ```bash
    sudo rm -rf /opt/trailarr
    ```

    **4. Remove the system user:**
    ```bash
    sudo userdel trailarr
    ```

    **5. Remove data and logs** (optional — skip if you want to keep your config and database):
    ```bash
    sudo rm -rf /var/lib/trailarr /var/log/trailarr
    ```

=== "macOS"

    **1. Unload and remove the launchd service** (if installed in Step 9):
    ```bash
    launchctl unload -w ~/Library/LaunchAgents/com.trailarr.app.plist
    rm ~/Library/LaunchAgents/com.trailarr.app.plist
    ```

    **2. Remove the CLI wrapper** (if installed in Step 10):
    ```bash
    sudo rm -f /usr/local/bin/trailarr
    ```

    **3. Remove application files:**
    ```bash
    sudo rm -rf /usr/local/opt/trailarr
    ```

    **4. Remove data and logs** (optional — skip if you want to keep your config and database):
    ```bash
    rm -rf "$HOME/.local/share/trailarr" "$HOME/Library/Logs/trailarr"
    ```

=== "Windows"

    **1. Remove the startup task** (if installed in Step 9):
    ```powershell
    & "C:\Program Files\Trailarr\scripts\windows\remove-startup.ps1"
    ```

    **2. Remove application files:**
    ```powershell
    Remove-Item -Recurse -Force "C:\Program Files\Trailarr"
    ```

    **3. Remove from PATH** (if added in Step 10):
    ```powershell
    $path = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $newPath = ($path -split ";") -notlike "*Program Files\Trailarr*" -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    ```

    **4. Remove data and logs** (optional — skip if you want to keep your config and database):
    ```powershell
    Remove-Item -Recurse -Force "C:\ProgramData\Trailarr"
    ```
