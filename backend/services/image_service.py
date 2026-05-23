"""Image service — refresh poster and fanart images for all media.

Reads media from the DB, resolves Plex auth tokens, and delegates
the actual HTTP download to download.image.refresh_media_images.
"""
import threading

import db.repos.connection as connection_repo
import db.repos.media as media_repo
from db.models.helpers import MediaImage
from download.image import refresh_media_images
from app_logger import ModuleLogger

logger = ModuleLogger("ImageService")


async def refresh_images(recent_only: bool = False, _stop_event: threading.Event | None = None) -> None:
    """Refresh poster and fanart for all movies and series."""
    logger.info("Refreshing images in the system")
    await _refresh_for_type(is_movie=True, recent_only=recent_only, _stop_event=_stop_event)
    await _refresh_for_type(is_movie=False, recent_only=recent_only, _stop_event=_stop_event)
    logger.info("Image refresh complete!")


async def _refresh_for_type(
    is_movie: bool,
    recent_only: bool = False,
    _stop_event: threading.Event | None = None,
) -> None:
    if recent_only:
        db_media_list = media_repo.read_recent(movies_only=is_movie)
    else:
        db_media_list = media_repo.read_all_generator(movies_only=is_movie)

    media_image_list: list[MediaImage] = []
    logger.debug(f"Refreshing images for {'movies' if is_movie else 'series'}")
    plex_tokens: dict[int, str] = {}

    for db_media in db_media_list:
        if _stop_event and _stop_event.is_set():
            logger.info("Image refresh stopped due to stop event.")
            return
        plex_headers: dict | None = None
        if db_media.plex_connection_id:
            conn_id = db_media.plex_connection_id
            if conn_id not in plex_tokens:
                try:
                    conn = connection_repo.read(conn_id)
                    plex_tokens[conn_id] = conn.api_key or ""
                except Exception:
                    plex_tokens[conn_id] = ""
            token = plex_tokens[conn_id]
            if token:
                plex_headers = {"X-Plex-Token": token}
        media_image_list.append(MediaImage(
            id=db_media.id,
            is_poster=True,
            image_url=db_media.poster_url,
            image_path=db_media.poster_path,
            headers=plex_headers,
        ))
        media_image_list.append(MediaImage(
            id=db_media.id,
            is_poster=False,
            image_url=db_media.fanart_url,
            image_path=db_media.fanart_path,
            headers=plex_headers,
        ))

    await refresh_media_images(is_movie, media_image_list, _stop_event)
    if _stop_event and _stop_event.is_set():
        logger.info("Image refresh stopped due to stop event.")
        return
    logger.debug(f"Finished refreshing images for {'movies' if is_movie else 'series'}")
