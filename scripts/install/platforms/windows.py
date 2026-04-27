"""Windows-specific installer: installs to Program Files, creates NSSM Windows service."""

import io
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path, WindowsPath

from common.display import console, print_info, print_success, print_warning, step_context
from platforms.base import BaseInstaller

_INSTALL_DIR = Path("C:/Program Files/Trailarr")
_DATA_DIR = Path("C:/ProgramData/Trailarr")
_LOG_DIR = _DATA_DIR / "logs"
_SERVICE_NAME = "Trailarr"
_NSSM_URL = "https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip"


class WindowsInstaller(BaseInstaller):
    def __init__(self, source_dir: Path, version: str) -> None:
        super().__init__(
            source_dir=source_dir,
            install_dir=_INSTALL_DIR,
            data_dir=_DATA_DIR,
            log_dir=_LOG_DIR,
            version=version,
        )

    def check_prerequisites(self) -> None:
        import ctypes

        if not ctypes.windll.shell32.IsUserAnAdmin():
            raise RuntimeError(
                "This installer must be run as Administrator.\n"
                "Right-click install.ps1 and choose 'Run as Administrator'."
            )

    def create_dirs(self) -> None:
        with step_context("Creating directories"):
            for directory in [
                _INSTALL_DIR,
                _DATA_DIR,
                _LOG_DIR,
                _DATA_DIR / "backups",
                _DATA_DIR / "web" / "images",
                _DATA_DIR / "tmp",
            ]:
                directory.mkdir(parents=True, exist_ok=True)

    def create_service(self, port: int) -> None:
        with step_context("Installing NSSM service wrapper"):
            nssm = self._get_nssm()

        with step_context("Creating Windows service"):
            python_exec = str(self._python_exec())
            start_script = str(_INSTALL_DIR / "scripts" / "start" / "start.py")
            log_file = str(_LOG_DIR / "trailarr.log")

            # Remove existing service if present
            subprocess.run([str(nssm), "stop", _SERVICE_NAME], capture_output=True)
            subprocess.run([str(nssm), "remove", _SERVICE_NAME, "confirm"], capture_output=True)

            # Install service
            subprocess.run([str(nssm), "install", _SERVICE_NAME, python_exec, start_script], check=True)
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "AppDirectory", str(_INSTALL_DIR)], check=True)
            subprocess.run(
                [str(nssm), "set", _SERVICE_NAME, "AppEnvironmentExtra",
                 f"APP_DATA_DIR={_DATA_DIR}",
                 f"PYTHONPATH={_INSTALL_DIR / 'backend'}",
                 f"PATH={_INSTALL_DIR / 'backend' / '.venv' / 'Scripts'};{_INSTALL_DIR / 'bin'};{os.environ.get('PATH', '')}"],
                check=True,
            )
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "AppStdout", log_file], check=True)
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "AppStderr", log_file], check=True)
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "AppRotateFiles", "1"], check=True)
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "AppRotateBytes", "10485760"], check=True)
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "Start", "SERVICE_AUTO_START"], check=True)
            subprocess.run([str(nssm), "set", _SERVICE_NAME, "DisplayName", "Trailarr"], check=True)
            subprocess.run(
                [str(nssm), "set", _SERVICE_NAME, "Description",
                 "Trailarr - Trailer downloader for Radarr and Sonarr"],
                check=True,
            )

            result = subprocess.run([str(nssm), "start", _SERVICE_NAME], capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"Windows service '{_SERVICE_NAME}' started")
            else:
                print_warning(f"Service installed but did not start automatically: {result.stderr.strip()}")
                print_warning(f"Start manually: Start-Service {_SERVICE_NAME}")

    def install_cli(self) -> None:
        with step_context("Installing trailarr CLI command"):
            cli_src = _INSTALL_DIR / "scripts" / "cli" / "trailarr_cli.py"
            python_exec = self._python_exec()

            # Create trailarr.cmd in the install dir
            cmd_wrapper = _INSTALL_DIR / "trailarr.cmd"
            cmd_wrapper.write_text(
                f'@echo off\n"{python_exec}" "{cli_src}" %*\n',
                encoding="utf-8",
            )

            # Add install dir to system PATH if not already present
            _add_to_system_path(str(_INSTALL_DIR))
            print_success(f"CLI installed: {cmd_wrapper}")
            _print_cli_hints()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_nssm(self) -> Path:
        nssm_dest = _INSTALL_DIR / "bin" / "nssm.exe"
        if nssm_dest.exists():
            return nssm_dest

        print_info("Downloading NSSM (Windows service wrapper)...")
        raw = urllib.request.urlopen(_NSSM_URL, timeout=60).read()  # noqa: S310
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            # Find nssm.exe for the appropriate architecture
            arch = "win64" if sys.maxsize > 2**32 else "win32"
            for name in zf.namelist():
                if arch in name and name.endswith("nssm.exe"):
                    nssm_dest.parent.mkdir(parents=True, exist_ok=True)
                    nssm_dest.write_bytes(zf.read(name))
                    break

        if not nssm_dest.exists():
            raise RuntimeError("Failed to extract nssm.exe from downloaded archive")

        print_success(f"NSSM installed: {nssm_dest}")
        return nssm_dest


def _add_to_system_path(new_path: str) -> None:
    """Add a directory to the Windows system PATH (machine-level) if not already present."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        )
        current, _ = winreg.QueryValueEx(key, "Path")
        if new_path.lower() not in current.lower():
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, current + ";" + new_path)
            print_success(f"Added {new_path} to system PATH (restart shell to take effect)")
        winreg.CloseKey(key)
    except Exception as e:
        print_warning(f"Could not update system PATH automatically: {e}")
        print_warning(f"Add manually: {new_path}")


def _print_cli_hints() -> None:
    print_info("trailarr run       — Start Trailarr")
    print_info("trailarr stop      — Stop Trailarr")
    print_info("trailarr status    — Show service status")
    print_info("trailarr logs      — View logs")
    print_info("trailarr update    — Update to latest version")
    print_info("trailarr uninstall — Remove Trailarr")
