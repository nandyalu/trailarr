"""Startup checks for the external binaries Trailarr runs (yt-dlp, ffmpeg, ffprobe).

The configured paths default to Docker locations (/usr/local/bin/...). On a
direct install those paths can be wrong or missing from the .env file. This
module checks each configured path at startup, falls back to the system PATH
when possible, and logs a clear error when the tool is not found at all.
"""

import os
import shutil
from pathlib import Path

from app_logger import ModuleLogger
from config.settings import app_settings

logger = ModuleLogger("BinaryPaths")


def validate_binary_paths() -> None:
    """Check the configured yt-dlp, ffmpeg, and ffprobe paths at startup.

    For each tool: if the configured path does not point to an executable,
    search the system PATH. If found there, use that copy for this run
    (process environment only — the .env file is not changed). If not found,
    log an error that names the environment variable to set.
    """
    _resolve_binary("yt-dlp", "YTDLP_PATH", app_settings.ytdlp_path)
    _resolve_binary("ffmpeg", "FFMPEG_PATH", app_settings.ffmpeg_path)
    _resolve_binary("ffprobe", "FFPROBE_PATH", app_settings.ffprobe_path)
    _ensure_js_runtime()


def _resolve_binary(tool: str, env_key: str, configured: str) -> None:
    # shutil.which accepts absolute paths and bare names. On Windows it
    # also tries PATHEXT, so 'yt-dlp' resolves to 'yt-dlp.exe'.
    if shutil.which(configured):
        return
    fallback = shutil.which(tool)
    if fallback:
        os.environ[env_key] = fallback
        logger.warning(
            f"{env_key} is set to '{configured}', but no executable exists"
            f" there. Trailarr uses '{fallback}' from the system PATH for"
            " this session."
        )
        return
    logger.error(
        f"Trailarr cannot find {tool} at '{configured}' or on the system"
        f" PATH. Set {env_key} in the .env file in APP_DATA_DIR to the full"
        f" path of the {tool} executable. Downloads and scans fail until"
        " you correct this."
    )


def _ensure_js_runtime() -> None:
    """Make sure yt-dlp can find a JavaScript runtime (Deno).

    yt-dlp needs a JavaScript runtime to solve YouTube's challenges.
    Without one, YouTube provides only image formats and every download
    fails with 'Requested format is not available'. yt-dlp discovers
    Deno through the PATH environment variable, so when only DENO_PATH
    is set, this adds the binary's directory to PATH for this process
    and its subprocesses.
    """
    if shutil.which("deno"):
        return
    configured = app_settings.deno_path
    resolved = shutil.which(configured) if configured else None
    if resolved:
        deno_dir = str(Path(resolved).parent)
        os.environ["PATH"] = (
            deno_dir + os.pathsep + os.environ.get("PATH", "")
        )
        logger.info(
            f"Added '{deno_dir}' to PATH so yt-dlp can find the Deno"
            " JavaScript runtime."
        )
        return
    logger.warning(
        "No JavaScript runtime found. yt-dlp needs one (Deno) to solve"
        " YouTube's challenges — without it, YouTube downloads fail with"
        " 'Requested format is not available'. Install Deno, or set"
        " DENO_PATH in the .env file in APP_DATA_DIR to the full path of"
        " the Deno executable."
    )
