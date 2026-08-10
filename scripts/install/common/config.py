"""Interactive configuration wizard for Trailarr installation."""

import platform
import socket
from pathlib import Path

from common.display import print_info, print_section, print_success
from common.env_file import load_env, update_env_var


def ask_port(default: int = 7889) -> int:
    print_section("Configuration")
    port = default
    while port <= 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                break
            except OSError:
                port += 1
    if port > 65535:
        raise RuntimeError(f"No free TCP port found between {default} and 65535")
    print_info(f"Web interface port: {port}" + (" (default)" if port == default else f" (port {default} in use)"))
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
    deno_path: Path | None,
    python_executable: Path,
) -> None:
    """Write the .env configuration file.

    Install-managed values (version, paths, port) are always written.
    User-tunable values are only seeded when missing, so re-running the
    installer over an existing install preserves the user's settings.
    """
    always_write = {
        "APP_VERSION": version,
        "APP_DATA_DIR": str(data_dir),
        "APP_PORT": str(port),
        "APP_MODE": _app_mode(),
        "FFMPEG_PATH": str(ffmpeg_path),
        "FFPROBE_PATH": str(ffprobe_path),
        "YTDLP_PATH": str(ytdlp_path),
        "PYTHON_EXECUTABLE": str(python_executable),
        "PYTHONPATH": str(install_dir / "backend"),
    }
    # Keep an existing DENO_PATH when this install could not provide Deno
    if deno_path:
        always_write["DENO_PATH"] = str(deno_path)
    defaults_if_missing = {
        "TZ": _detect_timezone(),
        "WAIT_FOR_MEDIA": str("true"),
        "UPDATE_YTDLP": str("false"),
        "LOG_LEVEL": str("INFO"),
    }

    env_path.parent.mkdir(parents=True, exist_ok=True)
    if not env_path.exists():
        env_path.write_text("# Trailarr Configuration\n", encoding="utf-8")

    existing = load_env(env_path)
    for key, value in always_write.items():
        update_env_var(env_path, key, value)
    for key, value in defaults_if_missing.items():
        if key not in existing:
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
