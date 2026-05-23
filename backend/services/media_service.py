"""Media service — business logic for interactive media writes.

Each write method:
1. Calls the repo to mutate the DB row.
2. Fires the relevant event(s) via event_service.
3. Returns the updated model so the API layer can push it via ws_manager.push().
"""
from db.models.event import EventSource
from db.models.media import MediaRead
import db.repos.media as media_repo
import db.repos.event as event_repo
from services import event_service


def toggle_monitor(media_id: int, monitor: bool) -> tuple[str, bool, MediaRead | None]:
    """Toggle monitoring for a single media item.

    Returns (message, changed, MediaRead | None).
    MediaRead is None when nothing changed.
    """
    msg, changed = media_repo.update_monitoring(media_id, monitor)
    if not changed:
        return msg, False, None
    event_service.track_monitor_changed(
        media_id=media_id,
        old_monitor=not monitor,
        new_monitor=monitor,
        source=EventSource.USER,
        source_detail="API",
    )
    updated = media_repo.read(media_id)
    return msg, True, updated


def batch_toggle_monitor(media_ids: list[int], monitor: bool) -> None:
    """Bulk-toggle monitoring for multiple media items."""
    for media_id in media_ids:
        msg, changed = media_repo.update_monitoring(media_id, monitor)
        if changed:
            event_service.track_monitor_changed(
                media_id=media_id,
                old_monitor=not monitor,
                new_monitor=monitor,
                source=EventSource.USER,
                source_detail="BatchAPI",
            )


def update_yt_id(media_id: int, yt_id: str) -> tuple[str, MediaRead]:
    """Update the YouTube trailer ID for a media item."""
    media = media_repo.read(media_id)
    old_yt_id = media.youtube_trailer_id
    media_repo.update_ytid(media_id, yt_id)
    event_service.track_youtube_id_changed(
        media_id=media_id,
        old_yt_id=old_yt_id,
        new_yt_id=yt_id,
        source=EventSource.USER,
        source_detail="API",
    )
    updated = media_repo.read(media_id)
    return f"YouTube ID updated for '{media.title}'", updated
