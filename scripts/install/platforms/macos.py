"""macOS-specific installer: creates launchd service, installs to /usr/local/opt/trailarr."""

import os
import subprocess
from pathlib import Path

from common.display import print_info, print_success, print_warning, step_context
from platforms.base import BaseInstaller

_INSTALL_DIR = Path("/usr/local/opt/trailarr")
_DATA_DIR = Path.home() / ".local" / "share" / "trailarr"
_LOG_DIR = Path.home() / "Library" / "Logs" / "trailarr"
_LAUNCHD_LABEL = "com.trailarr.app"
_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCHD_LABEL}.plist"


class MacOSInstaller(BaseInstaller):
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
                "Please re-run with:  sudo bash install.sh"
            )

    def create_dirs(self) -> None:
        with step_context("Creating directories"):
            for directory in [
                _INSTALL_DIR,
                _DATA_DIR,
                _LOG_DIR,
                _DATA_DIR / "logs",
                _DATA_DIR / "backups",
                _DATA_DIR / "web" / "images",
                _DATA_DIR / "tmp",
                _PLIST_PATH.parent,
            ]:
                directory.mkdir(parents=True, exist_ok=True)

    def copy_files(self) -> None:
        super().copy_files()
        # The installer runs as root (sudo), but the launchd service runs as
        # SUDO_USER. Transfer ownership of the browser directory and index.html
        # so that user can write them at runtime — setup_url_base_folder()
        # creates a URL_BASE subfolder inside browser/, and update_base_href()
        # patches <base href> for URL_BASE.
        sudo_user = os.environ.get("SUDO_USER", "")
        browser_dir = _INSTALL_DIR / "frontend-build" / "browser"
        index_html = browser_dir / "index.html"
        if sudo_user and browser_dir.exists():
            import pwd as _pwd
            try:
                pw = _pwd.getpwnam(sudo_user)
                os.chown(browser_dir, pw.pw_uid, pw.pw_gid)
                if index_html.exists():
                    os.chown(index_html, pw.pw_uid, pw.pw_gid)
            except (KeyError, OSError) as e:
                print_warning(f"Could not set ownership of browser directory: {e}")

    def create_service(self, port: int) -> None:
        with step_context("Creating launchd service"):
            python_exec = str(self._python_exec())
            start_script = str(_INSTALL_DIR / "scripts" / "start" / "start.py")
            log_out = str(_LOG_DIR / "trailarr.log")

            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exec}</string>
        <string>{start_script}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{_INSTALL_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>APP_DATA_DIR</key>
        <string>{_DATA_DIR}</string>
        <key>PYTHONPATH</key>
        <string>{_INSTALL_DIR / "backend"}</string>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_out}</string>
    <key>StandardErrorPath</key>
    <string>{log_out}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
            _PLIST_PATH.write_text(plist, encoding="utf-8")

            # Load the service
            result = subprocess.run(
                ["launchctl", "load", "-w", str(_PLIST_PATH)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print_warning(f"Could not auto-start service: {result.stderr.strip()}")
                print_warning(f"Start manually: launchctl load -w {_PLIST_PATH}")
            else:
                print_success(f"launchd service loaded: {_LAUNCHD_LABEL}")

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


def _print_cli_hints() -> None:
    print_info("trailarr run       — Start Trailarr")
    print_info("trailarr stop      — Stop Trailarr")
    print_info("trailarr status    — Show service status")
    print_info("trailarr logs      — View logs")
    print_info("trailarr update    — Update to latest version")
    print_info("trailarr uninstall — Remove Trailarr")
