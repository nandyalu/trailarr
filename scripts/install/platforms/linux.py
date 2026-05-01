"""Linux-specific installer: creates trailarr system user, systemd service."""

import grp
import os
import pwd
import subprocess
from pathlib import Path

from common.display import console, print_section, print_success, print_warning, step_context
from platforms.base import BaseInstaller

_INSTALL_DIR = Path("/opt/trailarr")
_DATA_DIR = Path("/var/lib/trailarr")
_LOG_DIR = Path("/var/log/trailarr")


class LinuxInstaller(BaseInstaller):
    def __init__(self, source_dir: Path, version: str) -> None:
        super().__init__(
            source_dir=source_dir,
            install_dir=_INSTALL_DIR,
            data_dir=_DATA_DIR,
            log_dir=_LOG_DIR,
            version=version,
        )

    def check_prerequisites(self) -> None:
        if os.geteuid() != 0:
            raise RuntimeError(
                "This installer must be run with root privileges.\n"
                "Please re-run with sudo:  sudo bash install.sh"
            )

    def create_dirs(self) -> None:
        with step_context("Creating user and directories"):
            # Create system user if not exists
            try:
                pwd.getpwnam("trailarr")
                print_warning("User 'trailarr' already exists, skipping creation")
            except KeyError:
                subprocess.run(
                    ["useradd", "-r", "-d", str(_INSTALL_DIR), "-s", "/bin/false", "-m", "trailarr"],
                    check=True,
                )
                print_success("Created system user 'trailarr'")

            for directory in [_INSTALL_DIR, _DATA_DIR, _LOG_DIR, _DATA_DIR / "logs", _DATA_DIR / "backups", _DATA_DIR / "web" / "images", _DATA_DIR / "tmp"]:
                directory.mkdir(parents=True, exist_ok=True)

            # Set ownership
            uid = pwd.getpwnam("trailarr").pw_uid
            gid = pwd.getpwnam("trailarr").pw_gid
            for directory in [_INSTALL_DIR, _DATA_DIR, _LOG_DIR]:
                _chown_recursive(directory, uid, gid)

    def copy_files(self) -> None:
        super().copy_files()
        # Re-apply ownership after copy
        uid = pwd.getpwnam("trailarr").pw_uid
        gid = pwd.getpwnam("trailarr").pw_gid
        _chown_recursive(_INSTALL_DIR, uid, gid)
        _chown_recursive(_DATA_DIR, uid, gid)

    def setup_python(self) -> None:
        super_run = super().setup_python

        def _as_trailarr() -> None:
            uid = pwd.getpwnam("trailarr").pw_uid
            gid = pwd.getpwnam("trailarr").pw_gid

            import shutil
            import subprocess as sp

            uv = shutil.which("uv")
            if not uv:
                raise RuntimeError("uv not found in PATH.")
            result = sp.run(
                [uv, "sync", "--no-cache-dir"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                preexec_fn=lambda: (os.setgid(gid), os.setuid(uid)),
            )
            if result.returncode != 0:
                raise RuntimeError(f"uv sync failed:\n{result.stderr}")

        with step_context("Setting up Python environment (uv sync)"):
            _as_trailarr()

    def create_service(self, port: int) -> None:
        with step_context("Creating systemd service"):
            python_exec = str(self._python_exec())
            start_script = str(_INSTALL_DIR / "scripts" / "start" / "start.py")

            unit = f"""\
[Unit]
Description=Trailarr - Trailer downloader for Radarr and Sonarr
Documentation=https://github.com/nandyalu/trailarr
After=network.target

[Service]
Type=simple
User=trailarr
Group=trailarr
WorkingDirectory={_INSTALL_DIR}
Environment=PYTHONPATH={_INSTALL_DIR / "backend"}
Environment=PATH={_INSTALL_DIR / "backend" / ".venv" / "bin"}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EnvironmentFile={_DATA_DIR / ".env"}
ExecStart={python_exec} {start_script}
Restart=always
RestartSec=60
TimeoutStopSec=30

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths={_DATA_DIR} {_LOG_DIR} {_INSTALL_DIR}
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
"""
            service_path = Path("/etc/systemd/system/trailarr.service")
            service_path.write_text(unit, encoding="utf-8")
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "trailarr"], check=True)
            subprocess.run(["systemctl", "start", "trailarr"], check=False)
            print_success("Systemd service created and enabled (trailarr.service)")

    def install_cli(self) -> None:
        with step_context("Installing trailarr CLI"):
            cli_src = _INSTALL_DIR / "scripts" / "cli" / "trailarr_cli.py"
            wrapper = Path("/usr/local/bin/trailarr")
            python_exec = self._python_exec()
            wrapper.write_text(
                f"#!/bin/sh\nexec {python_exec} {cli_src} \"$@\"\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            print_success("CLI installed: /usr/local/bin/trailarr")
            _print_cli_hints()


def _chown_recursive(path: Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    if path.is_dir():
        for child in path.rglob("*"):
            try:
                os.chown(child, uid, gid)
            except OSError:
                pass


def _print_cli_hints() -> None:
    from common.display import print_info
    print_info("trailarr run       — Start Trailarr")
    print_info("trailarr stop      — Stop Trailarr")
    print_info("trailarr status    — Show service status")
    print_info("trailarr logs      — View logs")
    print_info("trailarr update    — Update to latest version")
    print_info("trailarr uninstall — Remove Trailarr")
