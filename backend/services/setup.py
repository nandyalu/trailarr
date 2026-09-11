"""The state of the first-run setup guide.

A fresh installation has nothing in it, and the guide walks the user
through the few things Trailarr needs: a connection, the optional TMDB
key, and a look at what the first run would download before it downloads
anything.

An installation that already has a connection or any media is not fresh,
and must never see the guide. That is decided once, by a startup pass, and
recorded in a setting — not by counting rows every time the page loads.
Counting every time would show the guide to someone who deleted their last
connection, which is the opposite of helpful.
"""

from app_logger import ModuleLogger
import database.manager.connection as connection_manager
import database.manager.media as media_manager
from config.settings import app_settings
from database.models.setup import SetupStatus

logger = ModuleLogger("Setup")


def counts() -> tuple[int, int]:
    """How many connections and media items exist.

    Returns:
        tuple[int, int]: The connection count and the media count.
    """
    try:
        connections = len(connection_manager.read_all())
    except Exception:
        connections = 0
    try:
        media = media_manager.count_all()
    except Exception:
        media = 0
    return connections, media


def status() -> SetupStatus:
    """What the frontend needs to decide whether to show the guide.

    An installation that is already in use is recorded as set up here, and
    not only by the startup pass. The pass runs a minute after start, and
    for that minute an upgraded installation would have been told it needs
    the guide — which is the one thing wargame C1 forbids. Asking at the
    moment someone asks closes that window. Both paths call the same
    function, and it does nothing once the decision is recorded.
    """
    if not app_settings.setup_completed:
        mark_existing_installation()
    connections, media = counts()
    return SetupStatus(
        needed=not app_settings.setup_completed,
        completed=app_settings.setup_completed,
        connections=connections,
        media=media,
        downloads_enabled=app_settings.downloads_enabled,
        tmdb_key_set=bool(app_settings.tmdb_api_key),
    )


def complete() -> SetupStatus:
    """Record that the setup guide is behind this installation.

    Called when the user finishes the guide and when they skip it. Both
    mean the same thing: do not show it again.
    """
    app_settings.setup_completed = True
    logger.info("Trailarr recorded that the setup guide is complete.")
    return status()


def mark_existing_installation() -> bool:
    """Put an installation that is already in use past the guide.

    Returns:
        bool: True when this installation was marked as set up.
    """
    if app_settings.setup_completed:
        return False
    connections, media = counts()
    if connections == 0 and media == 0:
        return False
    app_settings.setup_completed = True
    logger.info(
        "Trailarr found an installation that is already in use"
        f" ({connections} connection(s), {media} media item(s)), so it does"
        " not show the setup guide."
    )
    return True
