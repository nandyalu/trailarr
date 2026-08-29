"""Ask Plex which media items already have a trailer.

Plex can hold a trailer that Trailarr did not download. The flag this task
writes lets a trailer profile skip a media item that Plex already covers.
"""

import threading

import database.manager.connection as connection_manager
import database.manager.media as media_manager
from app_logger import ModuleLogger
from database.models.connection import ArrType, ConnectionRead
from services.connections.plex.api_manager import PlexAPI

logger = ModuleLogger("PlexTrailerRefreshTask")

_CHUNK_SIZE = 50


def _build_api_cache(connections: list[ConnectionRead]) -> dict[int, PlexAPI]:
    """Create a PlexAPI instance for each Plex connection and return them keyed by connection id."""
    return {
        c.id: PlexAPI(
            server_url=c.url,
            token=c.api_key,
            identifier=f"trailarr_{c.id}",
        )
        for c in connections
        if c.arr_type == ArrType.PLEX
    }


async def _refresh_media_item(
    media,
    api: PlexAPI,
) -> tuple[bool, bool]:
    """Call the Plex API for one item and return (has_trailer, had_error)."""
    try:
        extras = await api.get_library_item_extras(media.plex_rating_key)
        has_trailer = any(
            e.subtype == "trailer" and not e.guid.startswith("file://")
            for e in extras
        )
        return has_trailer, False
    except Exception as e:
        logger.warning(
            f"Trailarr could not refresh the Plex trailer flag for"
            f" '{media.title}': {e}",
            **logger.media(media.id),
        )
        return False, True


async def refresh_plex_trailer_flags(
    _stop_event: threading.Event | None = None,
) -> None:
    """Refresh the plex_trailer flag for all Plex-linked media items.

    Calls the Plex API once per item to check whether Plex already has a
    remote trailer. The result is cached on the media row so the download
    task can skip the API call on subsequent runs.
    """
    api_cache = _build_api_cache(connection_manager.read_all())

    if not api_cache:
        logger.warning(
            "There are no Plex connections. Trailarr skips the refresh of"
            " the Plex trailer flags."
        )
        return

    logger.info(
        f"Trailarr refreshes the Plex trailer flags for {len(api_cache)}"
        " Plex connections."
    )

    seen_ids: set[int] = set()
    pending_updates: list[tuple[int, bool | None]] = []
    total_updated = 0
    errors = 0

    for media in media_manager.read_all_generator(plex_linked_only=True):
        if _stop_event and _stop_event.is_set():
            logger.info(
                "Trailarr stopped the refresh of the Plex trailer flags."
                " A stop was requested."
            )
            break
        if media.id in seen_ids:
            continue
        seen_ids.add(media.id)

        if not media.plex_connection_id or not media.plex_rating_key:
            continue

        api = api_cache.get(media.plex_connection_id)
        if api is None:
            # Connection added since task started — refresh cache from DB.
            api_cache = _build_api_cache(connection_manager.read_all())
            api = api_cache.get(media.plex_connection_id)
            if api is None:
                continue

        has_trailer, had_error = await _refresh_media_item(media, api)
        if had_error:
            errors += 1
        else:
            pending_updates.append((media.id, has_trailer))

        if len(pending_updates) >= _CHUNK_SIZE:
            media_manager.update_plex_trailer_bulk(pending_updates)
            total_updated += len(pending_updates)
            pending_updates = []

    if pending_updates:
        media_manager.update_plex_trailer_bulk(pending_updates)
        total_updated += len(pending_updates)

    logger.info(
        f"Trailarr refreshed the Plex trailer flags. It changed"
        f" {total_updated} media items. {errors} failed."
    )
