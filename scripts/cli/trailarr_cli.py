"""
Trailarr CLI — cross-platform service management tool.

Usage:
  trailarr run                    — Start the Trailarr service
  trailarr stop                   — Stop the Trailarr service
  trailarr restart                — Restart the Trailarr service
  trailarr status                 — Show service status
  trailarr logs [N]               — Show last N log lines (default 50)
  trailarr version                — Show installed and latest versions
  trailarr update [vX.Y.Z] [--force] — Update Trailarr (latest, or a specific version)
  trailarr uninstall              — Remove Trailarr from this machine
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"


def _resolve_home() -> Path:
    """Home of the user the service belongs to — the sudo invoker, not root.

    `sudo trailarr update` and plain `trailarr status` must agree on where
    the data dir and LaunchAgent live.
    """
    sudo_user = os.environ.get("SUDO_USER", "")
    if sudo_user and sudo_user != "root" and not _IS_WINDOWS:
        try:
            import pwd

            return Path(pwd.getpwnam(sudo_user).pw_dir)
        except KeyError:
            pass
    return Path.home()


# Paths mirror installer defaults
if _IS_LINUX:
    _INSTALL_DIR = Path("/opt/trailarr")
    _DATA_DIR = Path("/var/lib/trailarr")
    _LOG_DIR = _DATA_DIR / "logs"
    _SERVICE_NAME = "trailarr"
elif _IS_MACOS:
    _INSTALL_DIR = Path("/usr/local/opt/trailarr")
    _USER_HOME = _resolve_home()
    _DATA_DIR = _USER_HOME / ".local" / "share" / "trailarr"
    _LOG_DIR = _USER_HOME / "Library" / "Logs" / "trailarr"
    _LAUNCHD_LABEL = "com.trailarr.app"
    _PLIST_PATH = _USER_HOME / "Library" / "LaunchAgents" / f"{_LAUNCHD_LABEL}.plist"
elif _IS_WINDOWS:
    _INSTALL_DIR = Path("C:/Program Files/Trailarr")
    _DATA_DIR = Path("C:/ProgramData/Trailarr")
    _LOG_DIR = _DATA_DIR / "logs"
    _TASK_NAME = "Trailarr"

_GITHUB_REPO = "nandyalu/trailarr"

# The CLI ships inside scripts/cli/ next to scripts/install/ — reuse the
# installer's .env helpers instead of carrying local copies.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "install"))
from common.env_file import load_env, update_env_var  # noqa: E402

# ---------------------------------------------------------------------------
# Rich console
# ---------------------------------------------------------------------------

try:
    from rich.console import Console

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


def _macos_uid() -> int:
    """UID of the user whose launchd gui domain hosts the Trailarr agent."""
    sudo_user = os.environ.get("SUDO_USER", "")
    if sudo_user and sudo_user != "root":
        try:
            import pwd

            return pwd.getpwnam(sudo_user).pw_uid
        except KeyError:
            pass
    return os.getuid()


def _service_start() -> None:
    if _IS_LINUX:
        r = _run("systemctl", "start", _SERVICE_NAME)
        if r.returncode == 0:
            _ok(f"Service '{_SERVICE_NAME}' started")
        else:
            _err(r.stderr.strip() or "Failed to start service")
    elif _IS_MACOS:
        # The agent lives in the user's gui launchd domain (not root's) —
        # bootstrap it there; if already loaded, kickstart instead.
        uid = _macos_uid()
        r = _run("launchctl", "bootstrap", f"gui/{uid}", str(_PLIST_PATH))
        if r.returncode != 0:
            r = _run("launchctl", "kickstart", f"gui/{uid}/{_LAUNCHD_LABEL}")
        if r.returncode == 0:
            _ok(f"Service '{_LAUNCHD_LABEL}' started")
        else:
            _err(r.stderr.strip() or "Failed to start service")
    elif _IS_WINDOWS:
        r = _run("powershell", "-NonInteractive", "-Command",
                 f"Start-ScheduledTask -TaskName '{_TASK_NAME}'")
        if r.returncode == 0:
            _ok(f"Task '{_TASK_NAME}' started")
        else:
            _err(r.stderr.strip() or "Failed to start task")


def _service_stop() -> None:
    if _IS_LINUX:
        r = _run("systemctl", "stop", _SERVICE_NAME)
    elif _IS_MACOS:
        uid = _macos_uid()
        r = _run("launchctl", "bootout", f"gui/{uid}/{_LAUNCHD_LABEL}")
        if r.returncode != 0:
            r = _run("launchctl", "unload", str(_PLIST_PATH))
    elif _IS_WINDOWS:
        r = _run("powershell", "-NonInteractive", "-Command",
                 f"Stop-ScheduledTask -TaskName '{_TASK_NAME}'")
    else:
        return
    if r.returncode == 0:
        _ok("Service stopped")
    else:
        _warn(r.stderr.strip() or "Service may already be stopped")


def _service_restart() -> None:
    if _IS_LINUX:
        r = _run("systemctl", "restart", _SERVICE_NAME)
        if r.returncode == 0:
            _ok(f"Service '{_SERVICE_NAME}' restarted")
        else:
            _err(r.stderr.strip() or "Failed to restart service")
    elif _IS_MACOS:
        _service_stop()
        _service_start()
    elif _IS_WINDOWS:
        _service_stop()
        _service_start()


def _service_status() -> None:
    if _IS_LINUX:
        subprocess.run(["systemctl", "status", _SERVICE_NAME, "--no-pager"], check=False)
    elif _IS_MACOS:
        uid = _macos_uid()
        r = subprocess.run(
            ["launchctl", "print", f"gui/{uid}/{_LAUNCHD_LABEL}"], check=False
        )
        if r.returncode != 0:
            subprocess.run(["launchctl", "list", _LAUNCHD_LABEL], check=False)
    elif _IS_WINDOWS:
        subprocess.run(
            ["powershell", "-NonInteractive", "-Command",
             f"Get-ScheduledTask -TaskName '{_TASK_NAME}' | "
             f"Select-Object TaskName, State, Description"],
            check=False,
        )


def _service_logs(lines: int) -> None:
    if _IS_LINUX:
        log_file = _LOG_DIR / "trailarr.log"
        _info("=== Startup logs (journalctl) ===")
        subprocess.run(["journalctl", "-u", _SERVICE_NAME, "-n", str(lines), "--no-pager"])
        _info(f"=== Application logs ({log_file}) ===")
        if log_file.exists() and log_file.stat().st_size > 0:
            subprocess.run(["tail", "-n", str(lines), str(log_file)])
        else:
            _warn("Application log file not found or empty — service may have failed to start.")
    elif _IS_MACOS:
        log_file = _LOG_DIR / "trailarr.log"
        if log_file.exists():
            subprocess.run(["tail", "-n", str(lines), str(log_file)])
        else:
            _warn(f"Log file not found: {log_file}")
    elif _IS_WINDOWS:
        log_file = _DATA_DIR / "logs" / "trailarr.log"
        if log_file.exists():
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-Content '{log_file}' -Tail {lines} -Encoding utf8"]
            )
        else:
            _warn(f"Log file not found: {log_file}")


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def _fetch_release(tag: str | None) -> dict:
    """Fetch release metadata from GitHub (latest, or a specific tag)."""
    if tag:
        url = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/tags/{tag}"
    else:
        url = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "trailarr-cli"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        return json.load(resp)


def _find_uv() -> str | None:
    """Locate uv, probing the sudo invoker's install dirs when not in PATH."""
    uv = shutil.which("uv")
    if uv:
        return uv
    candidates: list[Path] = []
    sudo_user = os.environ.get("SUDO_USER", "")
    if sudo_user and sudo_user != "root" and not _IS_WINDOWS:
        try:
            import pwd

            candidates.append(Path(pwd.getpwnam(sudo_user).pw_dir) / ".local" / "bin" / "uv")
        except KeyError:
            pass
    candidates += [
        Path.home() / ".local" / "bin" / "uv",
        Path("/opt/homebrew/bin/uv"),
        Path("/usr/local/bin/uv"),
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return str(c)
    return None


def _verify_checksum(archive: Path, sha_url: str) -> None:
    req = urllib.request.Request(sha_url, headers={"User-Agent": "trailarr-cli"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        expected = resp.read().decode("utf-8").split()[0].strip().lower()
    h = hashlib.sha256()
    with open(archive, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if expected and actual != expected:
        raise RuntimeError(
            f"Checksum mismatch for downloaded archive: expected {expected}, got {actual}"
        )
    _ok("Checksum verified")


def _sync_python_deps() -> None:
    """Re-run uv sync for updated Python dependencies. Raises on failure."""
    _info("Updating Python dependencies...")
    uv = _find_uv()
    if not uv:
        raise RuntimeError(
            "uv not found — cannot update Python dependencies. "
            "Install uv (https://docs.astral.sh/uv/) and re-run the update."
        )

    backend_dir = _INSTALL_DIR / "backend"
    uv_python_dir = backend_dir / ".uv-python"
    uv_python_dir.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT")}
    env["UV_PYTHON_INSTALL_DIR"] = str(uv_python_dir)

    subprocess.run(
        [uv, "python", "install", "cpython-3.13"],
        capture_output=True, text=True, env=env,
    )
    if _IS_WINDOWS:
        python_bins = sorted(uv_python_dir.glob("cpython-3.13*/python.exe"))
        python_bin = python_bins[0] if python_bins else None
    else:
        python_bins = sorted(uv_python_dir.glob("cpython-3.13*/bin/python3*"))
        python_bin = next((p for p in python_bins if not p.name.endswith(("-config", ".1"))), None)

    sync_cmd = [uv, "sync", "--no-cache"]
    if python_bin:
        sync_cmd += ["--python", str(python_bin)]

    r = subprocess.run(sync_cmd, cwd=str(backend_dir), capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"uv sync failed:\n{r.stderr[:500]}")
    _ok("Python dependencies updated")


def _fix_ownership() -> None:
    """Linux: hand the whole install tree back to the trailarr service user.

    The update runs as root; chowning only backend/ would leave
    frontend-build/ (which the app must write for URL_BASE support),
    scripts/ and assets/ owned by root.
    """
    if not _IS_LINUX:
        return
    import pwd

    try:
        pw = pwd.getpwnam("trailarr")
    except KeyError:
        return
    for p in [_INSTALL_DIR, *_INSTALL_DIR.rglob("*")]:
        try:
            os.chown(p, pw.pw_uid, pw.pw_gid)
        except OSError:
            pass


def _version() -> None:
    installed = load_env(_DATA_DIR / ".env").get("APP_VERSION", "unknown")
    _info(f"Installed version: {installed}")
    try:
        latest = _fetch_release(None).get("tag_name", "unknown")
    except Exception as exc:
        _warn(f"Could not check the latest release: {exc}")
        return
    _info(f"Latest release:    {latest}")
    if installed.lstrip("v") == latest.lstrip("v"):
        _ok("Trailarr is up to date")
    elif _IS_WINDOWS:
        _warn("Update available — run 'trailarr update' as Administrator")
    else:
        _warn("Update available — run: sudo trailarr update")


def _update(target: str | None = None, force: bool = False) -> None:
    _info("Fetching release information...")
    try:
        release = _fetch_release(target)
    except Exception as exc:
        _err(f"Failed to fetch release info: {exc}")
        if target:
            _info(f"Check that '{target}' exists: https://github.com/{_GITHUB_REPO}/releases")
        sys.exit(1)

    tag = release.get("tag_name", "unknown")
    env_path = _DATA_DIR / ".env"
    current = load_env(env_path).get("APP_VERSION", "")
    if not force and current and current.lstrip("v") == tag.lstrip("v"):
        _ok(f"Already up to date ({current})")
        _info("Use 'trailarr update --force' to reinstall anyway.")
        return

    assets = release.get("assets", [])
    asset = next((a for a in assets if a["name"].endswith("-release.tar.gz")), None)
    if not asset:
        _err(f"No release asset found for version {tag}. Cannot update.")
        sys.exit(1)
    # Checksum asset exists for newer releases only; skip quietly when absent
    sha_asset = next((a for a in assets if a["name"] == asset["name"] + ".sha256"), None)

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

    # Replaced application dirs are renamed aside (not deleted) so any
    # failure below can roll the install back to the previous version.
    replaced: dict[str, Path] = {}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive = tmp_path / "release.tar.gz"
            _info(f"Downloading {asset['browser_download_url']}...")
            urllib.request.urlretrieve(asset["browser_download_url"], archive)  # noqa: S310

            if sha_asset:
                _verify_checksum(archive, sha_asset["browser_download_url"])

            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(tmp_path, filter="data")

            extracted = next(tmp_path.glob("trailarr-*/"), None)
            if not extracted:
                raise RuntimeError("Failed to find extracted release directory")

            for name in ("backend", "frontend-build", "assets", "scripts"):
                src = extracted / name
                dst = _INSTALL_DIR / name
                if not src.exists():
                    continue
                if dst.exists():
                    aside = _INSTALL_DIR / f".{name}.old"
                    if aside.exists():
                        shutil.rmtree(aside)
                    dst.rename(aside)
                    replaced[name] = aside
                shutil.copytree(src, dst)

        _sync_python_deps()
        _fix_ownership()

        # Update CLI wrapper to latest version
        _reinstall_cli()

        # Record the new version so the app reports it (installer writes the raw tag)
        update_env_var(env_path, "APP_VERSION", tag)

        for aside in replaced.values():
            shutil.rmtree(aside, ignore_errors=True)

    except Exception as exc:
        _err(f"Update failed: {exc}")
        _warn("Rolling back to the previous version...")
        for name, aside in replaced.items():
            dst = _INSTALL_DIR / name
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            if aside.exists():
                aside.rename(dst)
        _service_start()
        sys.exit(1)

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
        # Re-copy python.exe → trailarr.exe so Task Manager shows "trailarr.exe"
        trailarr_exe = venv_python.parent / "trailarr.exe"
        shutil.copy2(venv_python, trailarr_exe)


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def _uninstall() -> None:
    if console:
        from rich.prompt import Confirm
        confirmed = Confirm.ask(
            "  [bold red]Remove Trailarr (service + application files)?[/bold red]",
            default=False,
            console=console,
        )
    else:
        answer = input("Remove Trailarr (service + application files)? (y/N): ").strip().lower()
        confirmed = answer in ("y", "yes")

    if not confirmed:
        _info("Uninstall cancelled.")
        return

    if console:
        from rich.prompt import Confirm
        remove_data = Confirm.ask(
            f"  [bold yellow]Also delete data directory ({_DATA_DIR})?\n"
            "  This contains your database, backups, and config.[/bold yellow]",
            default=False,
            console=console,
        )
    else:
        answer = input(f"Also delete data directory {_DATA_DIR}? (database, backups, config) (y/N): ").strip().lower()
        remove_data = answer in ("y", "yes")

    _service_stop()

    if _IS_LINUX:
        _run("systemctl", "disable", _SERVICE_NAME)
        service_file = Path(f"/etc/systemd/system/{_SERVICE_NAME}.service")
        service_file.unlink(missing_ok=True)
        _run("systemctl", "daemon-reload")
        _run("userdel", "-r", "trailarr")
        wrapper = Path("/usr/local/bin/trailarr")
        wrapper.unlink(missing_ok=True)
        shutil.rmtree(Path("/var/log/trailarr"), ignore_errors=True)
    elif _IS_MACOS:
        uid = _macos_uid()
        _run("launchctl", "bootout", f"gui/{uid}", str(_PLIST_PATH))
        _run("launchctl", "unload", "-w", str(_PLIST_PATH))
        _PLIST_PATH.unlink(missing_ok=True)
        Path("/usr/local/bin/trailarr").unlink(missing_ok=True)
        shutil.rmtree(_LOG_DIR, ignore_errors=True)
    elif _IS_WINDOWS:
        _run("powershell", "-NonInteractive", "-Command",
             f"Stop-ScheduledTask -TaskName '{_TASK_NAME}' -ErrorAction SilentlyContinue; "
             f"Unregister-ScheduledTask -TaskName '{_TASK_NAME}' -Confirm:$false -ErrorAction SilentlyContinue")

    if _INSTALL_DIR.exists():
        shutil.rmtree(_INSTALL_DIR, ignore_errors=True)

    if remove_data and _DATA_DIR.exists():
        shutil.rmtree(_DATA_DIR, ignore_errors=True)
    elif _DATA_DIR.exists():
        _info(f"Data folder at '{_DATA_DIR}' has been kept")
    _ok("Trailarr successfully uninstalled")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _usage() -> None:
    if console:
        from rich.panel import Panel
        if _IS_WINDOWS:
            elevation_hint = "run, stop, restart, update, uninstall require Run as Administrator"
        else:
            elevation_hint = "run, stop, restart, update, uninstall require sudo"
        console.print(
            Panel(
                "  [bold]trailarr run[/bold]         — Start the service\n"
                "  [bold]trailarr stop[/bold]        — Stop the service\n"
                "  [bold]trailarr restart[/bold]     — Restart the service\n"
                "  [bold]trailarr status[/bold]      — Show service status\n"
                "  [bold]trailarr logs [N][/bold]    — Show last N lines (default 50)\n"
                "  [bold]trailarr version[/bold]     — Show installed and latest versions\n"
                "  [bold]trailarr update[/bold]      — Update to latest version\n"
                "                        [dim]trailarr update vX.Y.Z — specific version;"
                " --force — reinstall[/dim]\n"
                "  [bold]trailarr uninstall[/bold]   — Remove Trailarr\n\n"
                f"  [dim italic]{elevation_hint}[/dim italic]",
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
            rest = args[1:]
            force = "--force" in rest
            target = next((a for a in rest if not a.startswith("-")), None)
            _update(target, force)
        case "version" | "--version" | "-v":
            _version()
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
