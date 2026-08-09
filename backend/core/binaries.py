"""Startup checks for the external binaries Trailarr runs (yt-dlp, ffmpeg, ffprobe).

The configured paths default to Docker locations (/usr/local/bin/...). On a
direct install those paths can be wrong or missing from the .env file. This
module checks each configured path at startup, falls back to the system PATH
when possible, and logs a clear error when the tool is not found at all.
"""

import os
import shutil

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
