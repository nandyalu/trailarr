# Trailarr Direct Installation Scripts

Cross-platform native installation for Linux, macOS, and Windows.
The only prerequisite is [`uv`](https://docs.astral.sh/uv/).

---

## Architecture

```
Bootstrap (OS-specific, minimal):
├── install.sh        (Linux / macOS)  — checks uv, downloads release, runs Python installer
└── install.ps1       (Windows)        — checks uv, downloads release, runs Python installer

Python installer  scripts/install/
├── install.py                    # Entry point — detects OS, delegates to platform module
├── common/
│   ├── display.py                # Rich Panel / Progress helpers
│   ├── ffmpeg.py                 # Downloads platform-specific ffmpeg static binary
│   ├── gpu.py                    # GPU detection + per-distro driver instructions
│   ├── config.py                 # Interactive config (port, .env)
│   └── env_file.py               # .env read / write helpers
└── platforms/
    ├── base.py                   # Shared: copy files, uv sync, write config
    ├── linux.py                  # trailarr user, systemd service
    ├── macos.py                  # launchd plist
    └── windows.py                # NSSM Windows service

Runtime   scripts/start/
└── start.py                      # Cross-platform: GPU → .env, DB backup, alembic, uvicorn

CLI  scripts/cli/
└── trailarr_cli.py               # run / stop / restart / status / logs / update / uninstall
```

---

## Install flow

1. User installs `uv` (one command, see below)
2. User runs `install.sh` or `install.ps1`
3. Bootstrap fetches latest `trailarr-{version}-release.tar.gz` from GitHub Releases
   (this asset is built by `.github/workflows/release.yml` and contains the pre-built Angular frontend)
4. Bootstrap calls: `uv run --python 3.13 --with rich scripts/install/install.py --source-dir … --version …`
5. Python installer handles everything: dirs, uv sync, ffmpeg, config, service, GPU report

---

## Release asset

The release workflow (`.github/workflows/release.yml`) triggers on `v*` tags and:
- Builds the Angular frontend (`npm run build` → outputs to `frontend-build/`)
- Packages: `backend/`, `frontend-build/`, `assets/`, `scripts/`, `install.sh`, `install.ps1`
- Publishes `trailarr-{version}-release.tar.gz` as a GitHub Release asset

The bootstrap requires this asset — it **does not** fall back to the source zipball.

---

## Installation directories

| | Linux | macOS | Windows |
|---|---|---|---|
| Install dir | `/opt/trailarr` | `/usr/local/opt/trailarr` | `C:\Program Files\Trailarr` |
| Data dir | `/var/lib/trailarr` | `~/.local/share/trailarr` | `C:\ProgramData\Trailarr` |
| Log dir | `/var/log/trailarr` | `~/Library/Logs/trailarr` | `C:\ProgramData\Trailarr\logs` |
| ffmpeg | `<install>/bin/ffmpeg` | `<install>/bin/ffmpeg` | `<install>\bin\ffmpeg.exe` |
| Service | systemd | launchd | Windows Service (NSSM) |

---

## ffmpeg sources

| Platform | Source |
|---|---|
| Linux x86_64 | [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds) `linux64-gpl` |
| Linux arm64 | yt-dlp/FFmpeg-Builds `linuxarm64-gpl` |
| Windows x64 | yt-dlp/FFmpeg-Builds `win64-gpl` |
| Windows arm64 | yt-dlp/FFmpeg-Builds `winarm64-gpl` |
| macOS | [evermeet.cx](https://evermeet.cx/ffmpeg/) static builds |

These static GPL builds support VAAPI (Intel/AMD) and NVENC (NVIDIA) — hardware acceleration
works once the appropriate drivers are installed.

---

## GPU detection

At the end of installation, `gpu.py` detects available GPU hardware and prints a rich panel
showing per-distro driver install commands.  **No drivers are installed automatically.**

After the user installs drivers and restarts Trailarr, hardware acceleration can be enabled
in **Settings → Video Processing**.

---

## Legacy scripts (`scripts/baremetal/`)

The Bash-based scripts in this directory are kept for reference and are still used by
any existing Debian-specific deployments.  New installations use the Python-based system
described above.

---

## Development / testing

```bash
# Run the installer locally (from repo root) without downloading a release:
uv run --python 3.13 --with rich scripts/install/install.py \
    --source-dir "$(pwd)" \
    --version dev

# Run just the startup script directly:
APP_DATA_DIR=/tmp/trailarr-test \
  /opt/trailarr/backend/.venv/bin/python scripts/start/start.py

# Test the CLI:
python scripts/cli/trailarr_cli.py status
```
