"""Interactive configuration wizard for Trailarr installation."""

import platform
from pathlib import Path

from rich.prompt import IntPrompt

from common.display import console, print_section, print_success
from common.env_file import update_env_var


def ask_port(default: int = 7889) -> int:
    print_section("Configuration")
    port = IntPrompt.ask(
        "  Web interface port",
        default=default,
        console=console,
    )
    while not (1024 <= port <= 65535):
        console.print("[error]  Port must be between 1024 and 65535[/error]")
        port = IntPrompt.ask(
            "  Web interface port", default=default, console=console
        )
    return port


def write_initial_config(
    env_path: Path,
    *,
    version: str,
    install_dir: Path,
    data_dir: Path,
    port: int,
    ffmpeg_path: Path,
    ffprobe_path: Path,
    ytdlp_path: Path,
    python_executable: Path,
) -> None:
    """Write the initial .env configuration file."""
    tz = _detect_timezone()

    vars_to_write = {
        "APP_VERSION": version,
        "APP_DATA_DIR": str(data_dir),
        "APP_PORT": str(port),
        "APP_MODE": _app_mode(),
        "TZ": tz,
        "FFMPEG_PATH": str(ffmpeg_path),
        "FFPROBE_PATH": str(ffprobe_path),
        "YTDLP_PATH": str(ytdlp_path),
        "PYTHON_EXECUTABLE": str(python_executable),
        "PYTHONPATH": str(install_dir / "backend"),
        "MONITOR_INTERVAL": str(60),
        "WAIT_FOR_MEDIA": str("true"),
        "UPDATE_YTDLP": str("false"),
        "LOG_LEVEL": str("INFO"),
    }

    env_path.parent.mkdir(parents=True, exist_ok=True)
    if not env_path.exists():
        env_path.write_text("# Trailarr Configuration\n", encoding="utf-8")

    for key, value in vars_to_write.items():
        update_env_var(env_path, key, value)

    print_success(f"Configuration written to {env_path}")


def _detect_timezone() -> str:
    try:
        from tzlocal import get_localzone
        return str(get_localzone())
    except Exception:
        pass
    return "UTC"


def _app_mode() -> str:
    modes = {
        "Linux": "Direct Linux",
        "Darwin": "Direct macOS",
        "Windows": "Direct Windows",
    }
    return modes.get(platform.system(), "Direct")
