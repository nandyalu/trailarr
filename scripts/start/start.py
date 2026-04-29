"""
Trailarr cross-platform startup script.

Used as the entry point for systemd (Linux), launchd (macOS), and NSSM (Windows) services.
Runs as the service user (trailarr on Linux, current user on macOS/Windows).

Flow:
  1. Display startup banner
  2. Ensure data directories exist
  3. Detect GPUs → update .env
  4. Check / update yt-dlp if UPDATE_YTDLP=true
  5. Backup database
  6. Run Alembic migrations
  7. exec uvicorn (replaces this process)
"""

import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).parent.resolve()
_INSTALL_DIR = (
    _SCRIPT_DIR.parent.parent
)  # scripts/start/ → scripts/ → install root

# Allow override via environment (set by the service unit file)
_DATA_DIR = Path(
    os.environ.get("APP_DATA_DIR", str(_INSTALL_DIR.parent / "data"))
)
_BACKEND_DIR = _INSTALL_DIR / "backend"
_VENV_DIR = _BACKEND_DIR / ".venv"
_BIN_DIR = _INSTALL_DIR / "bin"

_IS_WINDOWS = platform.system() == "Windows"
_VENV_BIN = _VENV_DIR / "Scripts" if _IS_WINDOWS else _VENV_DIR / "bin"
_PYTHON = _VENV_BIN / ("python.exe" if _IS_WINDOWS else "python")


# ---------------------------------------------------------------------------
# Rich console (available after uv sync installed rich into the venv)
# ---------------------------------------------------------------------------


def _get_console():
    try:
        from rich.console import Console

        return Console()
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _load_env(env_path: Path) -> dict[str, str]:
    # Use dotenv's own parser so it correctly handles whatever quoting set_key writes.
    from dotenv import dotenv_values

    result: dict[str, str] = {
        k: v for k, v in dotenv_values(env_path).items() if v is not None
    }
    # Merge into os.environ so subprocess calls inherit them
    os.environ.update(result)
    return result


def _update_env_var(env_path: Path, key: str, value: str) -> None:
    if not env_path.exists():
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _log(msg: str, console=None) -> None:
    if console:
        console.print(msg)
    else:
        print(msg, flush=True)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def _print_banner(env: dict[str, str], console) -> None:
    version = env.get("APP_VERSION", "unknown")
    port = env.get("APP_PORT", "7889")
    mode = env.get("APP_MODE", "Direct")
    data_dir = env.get("APP_DATA_DIR", str(_DATA_DIR))

    if console:
        from rich.panel import Panel
        from rich.text import Text

        console.print(
            Panel(
                Text.assemble(
                    ("Trailarr\n", "bold cyan"),
                    (f"  Version:  {version}\n", "white"),
                    (f"  Mode:     {mode}\n", "white"),
                    (f"  Data dir: {data_dir}\n", "white"),
                    (f"  Port:     {port}", "white"),
                ),
                border_style="blue",
            )
        )
    else:
        print(
            f"\n=== Trailarr {version} | {mode} | port {port} ===\n",
            flush=True,
        )


def _ensure_dirs(data_dir: Path, console) -> None:
    for sub in ("logs", "backups", "web/images", "tmp"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    _log("  Directories ready", console)


def _detect_gpus_and_update_env(env_path: Path, console) -> None:
    """Detect available GPU hardware and write results to .env."""
    _log("  Detecting GPU hardware...", console)
    try:
        # Add scripts/install to path so gpu module is importable
        install_pkg = str(_INSTALL_DIR / "scripts" / "install")
        if install_pkg not in sys.path:
            sys.path.insert(0, install_pkg)

        from common.gpu import detect_gpus  # type: ignore

        gpus = detect_gpus()
        nvidia = any(g.vendor == "nvidia" for g in gpus)
        intel = any(g.vendor == "intel" for g in gpus)
        amd = any(g.vendor == "amd" for g in gpus)

        _update_env_var(env_path, "GPU_AVAILABLE_NVIDIA", str(nvidia).lower())
        _update_env_var(env_path, "GPU_AVAILABLE_INTEL", str(intel).lower())
        _update_env_var(env_path, "GPU_AVAILABLE_AMD", str(amd).lower())

        for gpu in gpus:
            if gpu.device_path:
                key = f"GPU_DEVICE_{gpu.vendor.upper()}"
                _update_env_var(env_path, key, gpu.device_path)

        if gpus:
            names = ", ".join(g.name for g in gpus)
            _log(f"  GPU(s) detected: {names}", console)
        else:
            _log(
                "  No GPU hardware detected; CPU encoding will be used",
                console,
            )
    except Exception as exc:
        _log(f"  GPU detection skipped: {exc}", console)


def _update_ytdlp(env: dict[str, str], console) -> None:
    val = env.get("UPDATE_YTDLP", "false").lower()
    if val not in ("true", "1", "yes"):
        return

    _log("  UPDATE_YTDLP=true — updating yt-dlp...", console)
    uv = shutil.which("uv") or str(_INSTALL_DIR / ".local" / "bin" / "uv")
    result = subprocess.run(
        [uv, "sync", "--no-cache-dir"],
        cwd=str(_BACKEND_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        _log("  yt-dlp updated", console)
    else:
        _log(f"  yt-dlp update failed: {result.stderr[:200]}", console)


def _backup_database(data_dir: Path, console) -> None:
    db = data_dir / "trailarr.db"
    if not db.exists():
        return

    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = backups_dir / f"trailarr_{stamp}.db"
    shutil.copy2(db, dest)
    _log(f"  Database backed up: {dest.name}", console)

    # Keep only the most recent 30 backups
    backups = sorted(
        backups_dir.glob("trailarr_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in backups[30:]:
        old.unlink(missing_ok=True)


def _run_migrations(console) -> None:
    _log("  Running database migrations...", console)
    alembic = _VENV_BIN / ("alembic.exe" if _IS_WINDOWS else "alembic")
    if not alembic.exists():
        alembic_cmd = [str(_PYTHON), "-m", "alembic"]
    else:
        alembic_cmd = [str(alembic)]

    result = subprocess.run(
        alembic_cmd + ["upgrade", "head"],
        cwd=str(_BACKEND_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic migrations failed:\n{result.stderr}")
    _log("  Migrations complete", console)


def _start_uvicorn(env: dict[str, str], console) -> None:
    port = env.get("APP_PORT", "7889")
    url_base = env.get("URL_BASE", "").strip("/")

    cmd = [
        f'"{str(_PYTHON)}"',
        "-m",
        "uvicorn",
        "main:trailarr_api",
        "--host",
        "0.0.0.0",
        "--port",
        port,
    ]
    if url_base:
        cmd += ["--root-path", f"/{url_base}"]

    _log(f"\n  Starting uvicorn on port {port}...", console)
    os.chdir(str(_BACKEND_DIR))

    # exec replaces this process with Python running uvicorn
    os.execv(str(_PYTHON), cmd)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    console = _get_console()
    env_path = _DATA_DIR / ".env"

    try:
        env = _load_env(env_path)

        _print_banner(env, console)

        if console:
            from rich.rule import Rule

            console.rule("[bold]Starting Trailarr[/bold]")
        else:
            print("=" * 60, flush=True)

        _log("", console)
        _ensure_dirs(_DATA_DIR, console)
        _detect_gpus_and_update_env(env_path, console)

        # Reload env after GPU detection updated it
        env = _load_env(env_path)

        _update_ytdlp(env, console)
        _backup_database(_DATA_DIR, console)
        _run_migrations(console)
        _start_uvicorn(env, console)

    except Exception as exc:
        if console:
            console.print(f"[bold red]✗ Startup failed:[/bold red] {exc}")
            console.print_exception()
        else:
            print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
