"""Windows-specific installer: installs to Program Files, registers Task Scheduler startup task."""

import os
import subprocess
from pathlib import Path, WindowsPath

from common.display import console, print_info, print_success, print_warning, step_context
from platforms.base import BaseInstaller

_INSTALL_DIR = Path("C:/Program Files/Trailarr")
_DATA_DIR = Path("C:/ProgramData/Trailarr")
_LOG_DIR = _DATA_DIR / "logs"
_TASK_NAME = "Trailarr"


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

            # The installer runs as Administrator, so dirs under ProgramData
            # may inherit ACLs that deny write access to the normal user who
            # will run the app via Task Scheduler.  Grant the installing user
            # full control so dotenv and SQLite can write freely.
            username = os.environ.get("USERNAME", "")
            if username:
                result = subprocess.run(
                    ["icacls", str(_DATA_DIR), "/grant", f"{username}:(OI)(CI)F", "/T"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print_warning(f"Could not set data directory permissions: {result.stderr.strip()}")

    def create_service(self, port: int) -> None:
        with step_context("Registering Task Scheduler startup task"):
            start_script = _INSTALL_DIR / "scripts" / "windows" / "trailarr-start.ps1"
            username = os.environ.get("USERNAME", "")
            if not username:
                raise RuntimeError("Could not determine current Windows username")

            ps = f"""
$action   = New-ScheduledTaskAction -Execute 'powershell.exe' `
              -Argument '-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File "{start_script}"'
$trigger  = New-ScheduledTaskTrigger -AtLogon -User '{username}'
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 3 `
              -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId '{username}' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName '{_TASK_NAME}' `
  -Description 'Trailarr - Trailer downloader for Radarr and Sonarr' `
  -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName '{_TASK_NAME}'
"""
            result = subprocess.run(
                ["powershell.exe", "-NonInteractive", "-Command", ps],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to register task:\n{result.stderr.strip()}")
            print_success(f"Task Scheduler startup task registered for {username}")

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
