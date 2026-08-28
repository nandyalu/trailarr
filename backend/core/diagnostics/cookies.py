"""Manage the YouTube cookies file from the UI (Milestone B).

Builds on the existing mechanism: downloads already pass
``app_settings.yt_cookies_path`` to yt-dlp. This module only gives that
setting a first-class UI path: upload/paste content, store it under
APP_DATA_DIR with mode 600, and report status.

Security (wargame B2): cookie values are credentials. They are never
logged, never returned by any endpoint (write-only), and the file is
excluded from the diagnostics bundle (Milestone D).
"""

import os
import time

from app_logger import ModuleLogger
from config.settings import app_settings
from core.diagnostics.models import CookiesStatus

logger = ModuleLogger("Cookies")

_MANAGED_FILENAME = "cookies.txt"


def _managed_path() -> str:
    return os.path.join(app_settings.app_data_dir, _MANAGED_FILENAME)


def _file_stats(path: str) -> tuple[int, int]:
    """(youtube cookie count, expired youtube cookie count)."""
    youtube = 0
    expired = 0
    now = time.time()
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < 7:
                continue
            if "youtube.com" not in fields[0]:
                continue
            youtube += 1
            try:
                expiry = float(fields[4])
            except ValueError:
                continue
            if expiry and expiry < now:
                expired += 1
    return youtube, expired


def get_status() -> CookiesStatus:
    """Status of the configured cookies file — never its content."""
    path = app_settings.yt_cookies_path
    if not path:
        return CookiesStatus(
            detail=(
                "No cookies file is set up. Cookies are needed only when"
                " YouTube asks for a sign-in or rate-limits downloads."
            )
        )
    if not os.path.isfile(path):
        return CookiesStatus(
            configured=True,
            path=path,
            exists=False,
            detail=f"The configured cookies file '{path}' does not exist.",
        )
    youtube, expired = _file_stats(path)
    if youtube == 0:
        detail = "The file contains no youtube.com cookies."
    elif expired:
        detail = f"{expired} of {youtube} youtube.com cookies are expired."
    else:
        detail = f"{youtube} youtube.com cookies, none expired."
    return CookiesStatus(
        configured=True,
        path=path,
        exists=True,
        youtube_cookies=youtube,
        expired=expired > 0 and expired >= youtube,
        detail=detail,
    )


def save(content: str) -> CookiesStatus:
    """Store uploaded cookies content and point yt-dlp at it.

    Args:
        content: The cookies file text (Netscape format).

    Raises:
        ValueError: If the content does not look like a cookies file.
    """
    if not _looks_like_cookies(content):
        raise ValueError(
            "This does not look like a cookies file. Export cookies in"
            " the Netscape format (the browser extensions do this) and"
            " try again."
        )
    path = _managed_path()
    # Write with restrictive permissions from the start
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    os.chmod(path, 0o600)
    app_settings.yt_cookies_path = path
    logger.info(f"Cookies file saved to '{path}' (values not logged).")
    return get_status()


def delete() -> CookiesStatus:
    """Clear the cookies setting; delete the file only if Trailarr owns it."""
    path = app_settings.yt_cookies_path
    managed = _managed_path()
    if path and os.path.abspath(path) == os.path.abspath(managed):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    app_settings.yt_cookies_path = ""
    logger.info("Cookies file removed from the configuration.")
    return get_status()


def _looks_like_cookies(content: str) -> bool:
    """True when at least one line parses as a Netscape cookie row."""
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if len(line.split("\t")) >= 7:
            return True
    return False
