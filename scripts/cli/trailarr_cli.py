"""
Trailarr CLI — cross-platform service management tool.

Usage:
  trailarr run       — Start the Trailarr service
  trailarr stop      — Stop the Trailarr service
  trailarr restart   — Restart the Trailarr service
  trailarr status    — Show service status
  trailarr logs [N]  — Show last N log lines (default 50)
  trailarr update    — Update Trailarr to the latest release
  trailarr uninstall — Remove Trailarr from this machine
"""

import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"

# Paths mirror installer defaults
if _IS_LINUX:
    _INSTALL_DIR = Path("/opt/trailarr")
    _DATA_DIR = Path("/var/lib/trailarr")
    _SERVICE_NAME = "trailarr"
elif _IS_MACOS:
    _INSTALL_DIR = Path("/usr/local/opt/trailarr")
    _DATA_DIR = Path.home() / ".local" / "share" / "trailarr"
    _LAUNCHD_LABEL = "com.trailarr.app"
    _PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCHD_LABEL}.plist"
elif _IS_WINDOWS:
    _INSTALL_DIR = Path("C:/Program Files/Trailarr")
    _DATA_DIR = Path("C:/ProgramData/Trailarr")
    _SERVICE_NAME = "Trailarr"
    _NSSM = _INSTALL_DIR / "bin" / "nssm.exe"

_GITHUB_REPO = "nandyalu/trailarr"

# ---------------------------------------------------------------------------
# Rich console
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    def _ok(msg: str) -> None:
        console.print(f"[bold green]  ✓  {msg}[/bold green]")

    def _err(msg: str) -> None:
        console.print(f"[bold red]  ✗  {msg}[/bold red]")

    def _info(msg: str) -> None:
        console.print(f"[cyan]     {msg}[/cyan]")

    def _warn(msg: str) -> None:
        console.print(f"[yellow]  ⚠  {msg}[/yellow]")

except ImportError:
    def _ok(msg):  print(f"✓ {msg}")        # noqa: E704
    def _err(msg): print(f"✗ {msg}", file=sys.stderr)  # noqa: E704
    def _info(msg): print(f"  {msg}")       # noqa: E704
    def _warn(msg): print(f"⚠ {msg}")       # noqa: E704
    console = None


# ---------------------------------------------------------------------------
# Service control helpers
# ---------------------------------------------------------------------------

def _run(*cmd: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), capture_output=True, text=True, check=check)


def _service_start() -> None:
    if _IS_LINUX:
        r = _run("systemctl", "start", _SERVICE_NAME)
        if r.returncode == 0:
            _ok(f"Service '{_SERVICE_NAME}' started")
        else:
            _err(r.stderr.strip() or "Failed to start service")
    elif _IS_MACOS:
        r = _run("launchctl", "start", _LAUNCHD_LABEL)
        if r.returncode == 0:
            _ok(f"Service '{_LAUNCHD_LABEL}' started")
        else:
            _err(r.stderr.strip() or "Failed to start service")
    elif _IS_WINDOWS:
        r = _run("sc", "start", _SERVICE_NAME)
        if r.returncode == 0:
            _ok(f"Service '{_SERVICE_NAME}' started")
        else:
            _err(r.stderr.strip() or "Failed to start service")


def _service_stop() -> None:
    if _IS_LINUX:
        r = _run("systemctl", "stop", _SERVICE_NAME)
    elif _IS_MACOS:
        r = _run("launchctl", "stop", _LAUNCHD_LABEL)
    elif _IS_WINDOWS:
        r = _run("sc", "stop", _SERVICE_NAME)
    else:
        return
    if r.returncode == 0:
        _ok("Service stopped")
    else:
        _warn(r.stderr.strip() or "Service may already be stopped")


def _service_restart() -> None:
    _service_stop()
    _service_start()


def _service_status() -> None:
    if _IS_LINUX:
        result = subprocess.run(["systemctl", "status", _SERVICE_NAME, "--no-pager"], check=False)
    elif _IS_MACOS:
        result = subprocess.run(["launchctl", "list", _LAUNCHD_LABEL], check=False)
    elif _IS_WINDOWS:
        result = subprocess.run(["sc", "query", _SERVICE_NAME], check=False)


def _service_logs(lines: int) -> None:
    if _IS_LINUX:
        subprocess.run(["journalctl", "-u", _SERVICE_NAME, "-n", str(lines), "--no-pager"])
    elif _IS_MACOS:
        log_file = Path.home() / "Library" / "Logs" / "trailarr" / "trailarr.log"
        if log_file.exists():
            subprocess.run(["tail", "-n", str(lines), str(log_file)])
        else:
            _warn(f"Log file not found: {log_file}")
    elif _IS_WINDOWS:
        log_file = _DATA_DIR / "logs" / "trailarr.log"
        if log_file.exists():
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Get-Content '{log_file}' -Tail {lines}"]
            )
        else:
            _warn(f"Log file not found: {log_file}")


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def _update() -> None:
    _info("Fetching latest release information...")
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "trailarr-cli"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            release = json.load(resp)
    except Exception as exc:
        _err(f"Failed to fetch release info: {exc}")
        sys.exit(1)

    tag = release.get("tag_name", "unknown")
    asset_url = next(
        (a["browser_download_url"] for a in release.get("assets", []) if a["name"].endswith("-release.tar.gz")),
        None,
    )
    if not asset_url:
        _err(f"No release asset found for version {tag}. Cannot update.")
        sys.exit(1)

    _info(f"Updating to {tag}...")
    _service_stop()

    # Back up current data
    _info("Backing up configuration...")
    backup_dir = _DATA_DIR / "backups" / f"update_{tag.lstrip('v')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for fname in (".env", "trailarr.db"):
        src = _DATA_DIR / fname
        if src.exists():
            shutil.copy2(src, backup_dir / fname)
    _ok(f"Backup saved to {backup_dir}")

    # Download release asset
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / "release.tar.gz"
        _info(f"Downloading {asset_url}...")
        urllib.request.urlretrieve(asset_url, archive)  # noqa: S310
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(tmp_path)

        extracted = next(tmp_path.glob("trailarr-*/"), None)
        if not extracted:
            _err("Failed to find extracted release directory")
            sys.exit(1)

        # Update application files (preserve data dir)
        for name in ("backend", "frontend-build", "assets", "scripts"):
            src = extracted / name
            dst = _INSTALL_DIR / name
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    # Re-run uv sync for updated Python dependencies
    _info("Updating Python dependencies...")
    uv = shutil.which("uv")
    if uv:
        r = subprocess.run([uv, "sync", "--no-cache-dir"], cwd=str(_INSTALL_DIR / "backend"),
                           capture_output=True, text=True)
        if r.returncode == 0:
            _ok("Python dependencies updated")
        else:
            _warn(f"uv sync warning: {r.stderr[:200]}")

    # Update CLI wrapper to latest version
    _reinstall_cli()

    _ok(f"Update to {tag} complete — restarting service")
    _service_start()


def _reinstall_cli() -> None:
    """Re-write the CLI wrapper after an update (scripts may have changed)."""
    cli_src = _INSTALL_DIR / "scripts" / "cli" / "trailarr_cli.py"
    if _IS_LINUX or _IS_MACOS:
        venv_python = _INSTALL_DIR / "backend" / ".venv" / "bin" / "python"
        wrapper = Path("/usr/local/bin/trailarr")
        wrapper.write_text(f"#!/bin/sh\nexec {venv_python} {cli_src} \"$@\"\n", encoding="utf-8")
        wrapper.chmod(0o755)
    elif _IS_WINDOWS:
        venv_python = _INSTALL_DIR / "backend" / ".venv" / "Scripts" / "python.exe"
        wrapper = _INSTALL_DIR / "trailarr.cmd"
        wrapper.write_text(f'@echo off\n"{venv_python}" "{cli_src}" %*\n', encoding="utf-8")


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def _uninstall() -> None:
    if console:
        from rich.prompt import Confirm
        confirmed = Confirm.ask(
            "  [bold red]This will remove Trailarr and all its data. Continue?[/bold red]",
            default=False,
            console=console,
        )
    else:
        answer = input("Remove Trailarr and all data? (y/N): ").strip().lower()
        confirmed = answer in ("y", "yes")

    if not confirmed:
        _info("Uninstall cancelled.")
        return

    _service_stop()

    if _IS_LINUX:
        _run("systemctl", "disable", _SERVICE_NAME)
        service_file = Path(f"/etc/systemd/system/{_SERVICE_NAME}.service")
        service_file.unlink(missing_ok=True)
        _run("systemctl", "daemon-reload")
        _run("userdel", "-r", "trailarr")
        wrapper = Path("/usr/local/bin/trailarr")
        wrapper.unlink(missing_ok=True)
    elif _IS_MACOS:
        _run("launchctl", "unload", "-w", str(_PLIST_PATH))
        _PLIST_PATH.unlink(missing_ok=True)
        Path("/usr/local/bin/trailarr").unlink(missing_ok=True)
    elif _IS_WINDOWS:
        if _NSSM.exists():
            _run(str(_NSSM), "remove", _SERVICE_NAME, "confirm")

    if _INSTALL_DIR.exists():
        shutil.rmtree(_INSTALL_DIR, ignore_errors=True)
    if _DATA_DIR.exists():
        shutil.rmtree(_DATA_DIR, ignore_errors=True)

    _ok("Trailarr has been removed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _usage() -> None:
    if console:
        from rich.panel import Panel
        console.print(
            Panel(
                "  [bold]trailarr run[/bold]         — Start the service\n"
                "  [bold]trailarr stop[/bold]        — Stop the service\n"
                "  [bold]trailarr restart[/bold]     — Restart the service\n"
                "  [bold]trailarr status[/bold]      — Show service status\n"
                "  [bold]trailarr logs [N][/bold]    — Show last N lines (default 50)\n"
                "  [bold]trailarr update[/bold]      — Update to latest version\n"
                "  [bold]trailarr uninstall[/bold]   — Remove Trailarr",
                title="[bold cyan]Trailarr CLI[/bold cyan]",
                border_style="blue",
            )
        )
    else:
        print(__doc__)


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0].lower() if args else ""

    match cmd:
        case "run" | "start":
            _service_start()
        case "stop":
            _service_stop()
        case "restart":
            _service_restart()
        case "status":
            _service_status()
        case "logs":
            lines = int(args[1]) if len(args) > 1 else 50
            _service_logs(lines)
        case "update":
            _update()
        case "uninstall":
            _uninstall()
        case "help" | "--help" | "-h" | "":
            _usage()
        case _:
            _err(f"Unknown command: '{cmd}'")
            _usage()
            sys.exit(1)


if __name__ == "__main__":
    main()
