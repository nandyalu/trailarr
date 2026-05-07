import threading

import core.base.database.manager.connection as connection_manager
import core.base.database.manager.media as media_manager
from app_logger import ModuleLogger
from core.base.database.models.connection import ArrType

logger = ModuleLogger("PlexTrailerRefreshTask")


async def refresh_plex_trailer_flags(
    _stop_event: threading.Event | None = None,
) -> None:
    """Refresh the plex_trailer flag for all Plex-linked media items.

    Calls the Plex API once per item to check whether Plex already has a
    remote trailer. The result is cached on the media row so the download
    task can skip the API call on subsequent runs.
    """
    connections = connection_manager.read_all()
    plex_connections = {c.id: c for c in connections if c.arr_type == ArrType.PLEX}

    if not plex_connections:
        logger.warning("No Plex connections found, skipping Plex trailer refresh")
        return

    logger.info(
        f"Refreshing Plex trailer flags for {len(plex_connections)} Plex connection(s)"
    )

    from core.plex.api_manager import PlexAPI

    updated = 0
    errors = 0

    for media in media_manager.read_all_generator(plex_linked_only=True):
        if _stop_event and _stop_event.is_set():
            logger.info("Stop event set, terminating Plex trailer flag refresh.")
            return

        conn = plex_connections.get(media.plex_connection_id)
        if not conn:
            continue

        try:
            api = PlexAPI(
                server_url=conn.url,
                token=conn.api_key,
                identifier=f"trailarr_{conn.id}",
            )
            extras = await api.get_library_item_extras(media.plex_rating_key)
            has_trailer = any(
                e.subtype == "trailer" and not e.guid.startswith("file://")
                for e in extras
            )
            media_manager.update_plex_trailer(media.id, has_trailer)
            updated += 1
        except Exception as e:
            logger.warning(
                f"Failed to refresh plex_trailer for '{media.title}'"
                f" [{media.id}]: {e}"
            )
            errors += 1

    logger.info(
        f"Plex trailer flag refresh complete."
        f" Updated: {updated}, Errors: {errors}"
    )
