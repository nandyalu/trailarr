"""Linux-specific installer: creates trailarr system user, systemd service."""

import grp
import os
import pwd
import subprocess
from pathlib import Path

from common.display import print_info, print_warning, step_context
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
                print_warning(
                    "User 'trailarr' already exists, skipping creation"
                )
            except KeyError:
                subprocess.run(
                    [
                        "useradd",
                        "-r",
                        "-d",
                        str(_INSTALL_DIR),
                        "-s",
                        "/bin/false",
                        "-m",
                        "trailarr",
                    ],
                    check=True,
                )
                print_info("Created system user 'trailarr'")

            for directory in [
                _INSTALL_DIR,
                _DATA_DIR,
                _LOG_DIR,
                _DATA_DIR / "logs",
                _DATA_DIR / "backups",
                _DATA_DIR / "web" / "images",
                _DATA_DIR / "tmp",
            ]:
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

    def write_config(self, port: int) -> None:
        super().write_config(port)
        # .env is written by root after create_dirs chowned data_dir; fix it.
        uid = pwd.getpwnam("trailarr").pw_uid
        gid = pwd.getpwnam("trailarr").pw_gid
        if self.env_path.exists():
            os.chown(self.env_path, uid, gid)

    def setup_python(self) -> None:
        with step_context("Setting up Python environment (uv sync)"):
            import shutil as _shutil

            uv = _shutil.which("uv")
            if not uv:
                raise RuntimeError("uv not found in PATH.")

            # Install Python into the install dir so the trailarr service user owns
            # the stdlib. Without this, uv reuses root's ~/.local/share/uv/python which
            # trailarr cannot read, causing "Failed to import encodings" at service start.
            uv_python_dir = self.backend_dir / ".uv-python"
            uv_python_dir.mkdir(parents=True, exist_ok=True)

            # Clear VIRTUAL_ENV to avoid conflicts with the outer `uv run` environment.
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in ("VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT")
            }
            env["UV_PYTHON_INSTALL_DIR"] = str(uv_python_dir)

            # Explicitly install Python 3.13 into our directory so uv doesn't fall
            # back to root's existing managed Python at the default location.
            subprocess.run(
                [uv, "python", "install", "cpython-3.13"],
                capture_output=True,
                text=True,
                env=env,
            )

            # Locate the installed binary to pass explicitly to `uv sync`, ensuring
            # the venv's pyvenv.cfg points to our Python, not root's.
            python_bins = sorted(
                uv_python_dir.glob("cpython-3.13*/bin/python3*")
            )
            python_bin = next(
                (
                    p
                    for p in python_bins
                    if not p.name.endswith(("-config", ".1"))
                ),
                None,
            )
            if not python_bin:
                raise RuntimeError(
                    f"Python 3.13 not found in {uv_python_dir} after install"
                )

            result = subprocess.run(
                [uv, "sync", "--no-cache", "--python", str(python_bin)],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                env=env,
            )
            if result.returncode != 0:
                raise RuntimeError(f"uv sync failed:\n{result.stderr}")

        # Re-apply ownership so the trailarr service user can use the venv and
        # the Python installation (both now live under backend_dir).
        uid = pwd.getpwnam("trailarr").pw_uid
        gid = pwd.getpwnam("trailarr").pw_gid
        _chown_recursive(self.backend_dir, uid, gid)

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
            subprocess.run(
                ["systemctl", "daemon-reload"], check=True, capture_output=True
            )
            subprocess.run(
                ["systemctl", "enable", "trailarr"],
                check=True,
                capture_output=True,
            )
            start_result = subprocess.run(
                ["systemctl", "start", "trailarr"],
                check=False,
                capture_output=True,
            )
            if start_result.returncode != 0:
                error_details: list[str] = [
                    "Failed to start trailarr service."
                ]
                if start_result.stderr:
                    error_details.append(
                        f"stderr:\n{start_result.stderr.strip()}"
                    )
                if start_result.stdout:
                    error_details.append(
                        f"stdout:\n{start_result.stdout.strip()}"
                    )
                raise RuntimeError("\n".join(error_details))

    def install_cli(self) -> None:
        with step_context("Installing trailarr CLI"):
            cli_src = _INSTALL_DIR / "scripts" / "cli" / "trailarr_cli.py"
            wrapper = Path("/usr/local/bin/trailarr")
            python_exec = self._python_exec()
            wrapper.write_text(
                f'#!/bin/sh\nexec {python_exec} {cli_src} "$@"\n',
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
        print_info("CLI installed: /usr/local/bin/trailarr")


def _chown_recursive(path: Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    if path.is_dir():
        for child in path.rglob("*"):
            try:
                os.chown(child, uid, gid)
            except OSError:
                pass
