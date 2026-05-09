from datetime import datetime, timezone
from typing import Sequence
from sqlmodel import Session, col, select

from . import base
from core.base.database.models.helpers import MediaImage, MediaUpdateDC
from core.base.database.models.media import (
    Media,
    MediaUpdate,
    MonitorStatus,
)
from core.base.database.utils.engine import write_session


@write_session
def update_media_image(
    media_image: MediaImage,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the image path of a media item in the database by id.\n
    Args:
        media_image (MediaImage): The media image data to update.
        _session (Session, Optional): A session to use for the database connection. \
            Default is None, in which case a new session will be created. \n
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_image.id, _session)
    _updated = False
    if media_image.is_poster:
        _updated = db_media.poster_path != media_image.image_path
        db_media.poster_path = media_image.image_path
    else:
        _updated = db_media.fanart_path != media_image.image_path
        db_media.fanart_path = media_image.image_path
    if _updated:
        _session.add(db_media)
        _session.commit()
    return


@write_session
def update_monitor_and_trailer_exists(
    media_id: int,
    monitor: bool,
    trailer_exists: bool,
    *,
    _commit: bool = True,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the monitoring and trailer_exists status of a media item in the database by id.\n
    Args:
        media_id (int): The id of the media to update.
        monitor (bool): The monitoring status to set.
        trailer_exists (bool): The trailer_exists status to set.
        _commit (bool, Optional): Flag to `commit` the changes. Default is `True`.
        _session (Session, Optional): A session to use for the database connection. \
            Default is `None`, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_id, _session)
    _updated = False
    if db_media.monitor != monitor:
        db_media.monitor = monitor
        _updated = True
    if db_media.trailer_exists != trailer_exists:
        db_media.trailer_exists = trailer_exists
        _updated = True
    if _updated:
        db_media.updated_at = datetime.now(timezone.utc)
        # Update status based on monitor status and trailer existence
        db_media.status = base.get_status(
            db_media.monitor, db_media.trailer_exists, db_media.status
        )
        _session.add(db_media)
        if _commit:
            _session.commit()
    return


@write_session
def update_monitor_and_trailer_exists_bulk(
    media_update_list: Sequence[tuple[int, bool, bool]],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the monitoring and trailer_exists status of multiple media items in the database at once.\n
    Args:
        media_update_list (Sequence[tuple[int, bool, bool]]): Sequence of tuples containing \
            media id, monitor status and trailer_exists status.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    for media_id, monitor, trailer_exists in media_update_list:
        update_monitor_and_trailer_exists(
            media_id,
            monitor,
            trailer_exists,
            _session=_session,
            _commit=False,
        )
    _session.commit()
    return


@write_session
def update_media_status(
    media_update: MediaUpdateDC,
    *,
    _commit: bool = True,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the monitoring status of a media item in the database by id.\n
    Args:
        media_update (MediaUpdateProtocol): The media update object satisfying the protocol.
        _commit (bool, Optional): Flag to `commit` the changes. Default is `True`.
        _session (Session, Optional): A session to use for the database connection. \
            Default is `None`, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_update.id, _session)
    _update = MediaUpdate(**media_update.model_dump())
    if base.has_updated(db_media, _update):
        db_media.updated_at = datetime.now(timezone.utc)
    if media_update.trailer_exists is not None:
        db_media.trailer_exists = media_update.trailer_exists
    # If trailer exists, disable monitoring
    if db_media.trailer_exists:
        db_media.monitor = False
    else:
        db_media.monitor = media_update.monitor
    # Update status based on monitor status and trailer existence if not downloading
    db_media.status = base.get_status(
        db_media.monitor, db_media.trailer_exists, media_update.status
    )
    if media_update.downloaded_at:
        db_media.downloaded_at = media_update.downloaded_at
    if media_update.yt_id:
        db_media.youtube_trailer_id = media_update.yt_id
    _session.add(db_media)
    if _commit:
        _session.commit()
    return


@write_session
def update_monitoring(
    media_id: int,
    monitor: bool,
    *,
    _commit: bool = True,
    _session: Session = None,  # type: ignore
) -> tuple[str, bool]:
    """Update the monitoring status of a media item in the database by id.\n
    Also updates the status based on the monitor status and trailer existence.\n
    Args:
        media_id (int): The id of the media to update.
        monitor (bool): The monitoring status to set.
        _commit (bool, Optional): Flag to `commit` the changes. Default is `True`.
        _session (Session, Optional): A session to use for the database connection. \
            Default is `None`, in which case a new session will be created.
    Returns:
        tuple(msg, bool): Message indicating the status of the operation, \
            and a flag indicating success.
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_id, _session)
    if db_media.monitor != monitor:
        db_media.updated_at = datetime.now(timezone.utc)
    # Check if the monitor status is already set to the same value
    if db_media.monitor == monitor:
        msg = f"Media '{db_media.title}' [{db_media.id}] is already"
        msg += " monitored!" if monitor else " not monitored!"
        return msg, False
    # Monitor = True
    if monitor:
        # If trailer exists, change nothing!
        if db_media.trailer_exists:
            msg = (
                f"Media '{db_media.title}' [{db_media.id}] already has a"
                " trailer!"
            )
            return msg, False
        # Trailer doesn't exist, set monitor status
        db_media.monitor = True
        db_media.status = MonitorStatus.MONITORED
        _session.add(db_media)
        if _commit:
            _session.commit()
        msg = f"Media '{db_media.title}' [{db_media.id}] is now monitored"
        return msg, True
    # Monitor = False
    # If trailer exists, set status to downloaded, else set to missing
    db_media.monitor = False
    db_media.status = base.get_status(
        db_media.monitor, db_media.trailer_exists, db_media.status
    )
    msg = f"Media '{db_media.title}' [{db_media.id}] is no longer monitored"
    _session.add(db_media)
    if _commit:
        _session.commit()
    return msg, True


@write_session
def update_monitoring_bulk(
    media_ids: list,
    monitor: bool,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the monitoring status of multiple media items in the database at once.\n
    Args:
        media_ids (list[int]): List of media id's to update.
        monitor (bool): The monitoring status to set.
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    for media_id in media_ids:
        update_monitoring(media_id, monitor, _session=_session, _commit=False)
    _session.commit()
    return


@write_session
def update_no_trailers_exist(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update a media item in the database to set trailer_exists to False.\n
    Does not change the monitor status, but updates the status accordingly.\n
    Args:
        media_id (int): The id of the media to update.
        _session (Session, Optional): A session to use for the database connection. \
            Default is None, in which case a new session will be created.
    Returns:
        None
    """
    db_media = base._get_db_item(media_id, _session)
    if db_media.trailer_exists is True:
        db_media.updated_at = datetime.now(timezone.utc)
    db_media.trailer_exists = False
    # Update status based on monitor status, but don't interrupt an active download
    db_media.status = base.get_status(db_media.monitor, False, db_media.status)
    _session.add(db_media)
    _session.commit()
    return None


# TODO: Split this up into separate simpler methods
@write_session
def update_trailer_exists(
    media_id: int,
    trailer_exists: bool,
    *,
    _commit: bool = True,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the trailer_exists status of a media item in the database by id.\n
    Args:
        media_id (int): The id of the media to update.
        trailer_exists (bool): The trailer_exists status to set.
        _commit (bool, Optional): Flag to `commit` the changes. Default is `True`.
        _session (Session, Optional): A session to use for the database connection. \
            Default is `None`, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_id, _session)
    if db_media.trailer_exists != trailer_exists:
        db_media.updated_at = datetime.now(timezone.utc)
    db_media.trailer_exists = trailer_exists
    # If trailer exists, disable monitoring and mark downloaded
    if trailer_exists:
        db_media.monitor = False
        db_media.status = MonitorStatus.DOWNLOADED
    else:
        # Don't interrupt an active download
        db_media.status = base.get_status(
            db_media.monitor, trailer_exists, db_media.status
        )
    _session.add(db_media)
    if _commit:
        _session.commit()
    return None


@write_session
def update_media_exists(
    media_id: int,
    media_exists: bool,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the media_exists flag of a media item in the database by id.\n
    Args:
        media_id (int): The id of the media to update.
        media_exists (bool): Whether the media file exists on disk.
        _session (Session, Optional): A session to use for the database connection. \
            Default is `None`, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_id, _session)
    if db_media.media_exists != media_exists:
        db_media.media_exists = media_exists
        db_media.updated_at = datetime.now(timezone.utc)
        _session.add(db_media)
        _session.commit()
    return None


@write_session
def update_ytid(
    media_id: int,
    yt_id: str,
    *,
    _commit: bool = True,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the youtube trailer id of a media item in the database by id.\n
    Args:
        media_id (int): The id of the media to update.
        yt_id (str): The youtube trailer id to set.
        _commit (bool, Optional): Flag to `commit` the changes. Default is `True`.
        _session (Session, Optional): A session to use for the database connection. \
            Default is `None`, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_id, _session)
    db_media.youtube_trailer_id = yt_id
    _session.add(db_media)
    if _commit:
        _session.commit()
    return None


@write_session
def update_plex_fields(
    media_id: int,
    plex_rating_key: str | None,
    plex_section_key: str | None,
    plex_connection_id: int | None,
    media_filename: str | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Update only the Plex-specific fields on a media item.\n
    Used during Plex connection refresh to layer Plex metadata onto an
    existing Arr-sourced media row without overwriting Arr fields.\n
    Args:
        media_id (int): The id of the media to update.
        plex_rating_key (str | None): The Plex ratingKey for targeted refreshes.
        plex_section_key (str | None): The Plex library section key.
        plex_connection_id (int | None): FK to the Plex Connection row.
        media_filename (str | None): When provided, update the media_filename field.
            Only pass this for Plex-only items (arr_id=0); leave None for Arr-linked rows.
        _session (Session, Optional): A session to use for the database connection.
    Returns:
        bool: True if any field was changed and the DB was updated, False if no-op.
    """
    db_media = base._get_db_item(media_id, _session)
    changed = (
        db_media.plex_rating_key != plex_rating_key
        or db_media.plex_section_key != plex_section_key
        or db_media.plex_connection_id != plex_connection_id
        or (
            media_filename is not None
            and db_media.media_filename != media_filename
        )
    )
    if not changed:
        return False
    db_media.plex_rating_key = plex_rating_key
    db_media.plex_section_key = plex_section_key
    db_media.plex_connection_id = plex_connection_id
    if media_filename is not None:
        db_media.media_filename = media_filename
    db_media.updated_at = datetime.now(timezone.utc)
    _session.add(db_media)
    _session.commit()
    return True


@write_session
def update_plex_trailer(
    media_id: int,
    plex_trailer: bool | None,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the plex_trailer flag on a media item.

    Args:
        media_id (int): The id of the media to update.
        plex_trailer (bool | None): True if Plex has a trailer, False if not, None if unknown.
        _session (Session, Optional): A session to use for the database connection.
    """
    db_media = base._get_db_item(media_id, _session)
    db_media.plex_trailer = plex_trailer
    db_media.updated_at = datetime.now(timezone.utc)
    _session.add(db_media)
    _session.commit()


@write_session
def update_plex_trailer_bulk(
    updates: list[tuple[int, bool | None]],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update plex_trailer flags for multiple media items in a single transaction.

    Args:
        updates: List of (media_id, plex_trailer) pairs to apply.
        _session (Session, Optional): A session to use for the database connection.
    """
    now = datetime.now(timezone.utc)
    for media_id, plex_trailer in updates:
        db_media = _session.get(Media, media_id)
        if db_media is None:
            continue
        db_media.plex_trailer = plex_trailer
        db_media.updated_at = now
        _session.add(db_media)
    _session.commit()
    return None


@write_session
def demote_arr_items_with_plex_to_plex_only(
    connection_id: int,
    keep_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> list[int]:
    """Demote Arr-sourced rows being removed from Arr that still have a Plex link.

    Instead of deleting them, sets connection_id = plex_connection_id and arr_id = 0
    so the Plex connection continues tracking the item. Only affects rows that have
    plex_connection_id set (i.e. previously linked to both Arr and Plex).

    Args:
        connection_id (int): The Arr connection id to scope the query.
        keep_ids (list[int]): Media ids that are still present in Arr (not to demote).

    Returns:
        list[int]: IDs of demoted media items so the caller can fire ARR_UNLINKED events.
    """
    statement = (
        select(Media)
        .where(Media.connection_id == connection_id)
        .where(~col(Media.id).in_(keep_ids))
        .where(col(Media.plex_connection_id).is_not(None))
    )
    rows = _session.exec(statement).all()
    demoted_ids: list[int] = []
    for db_media in rows:
        db_media.connection_id = db_media.plex_connection_id  # type: ignore
        db_media.arr_id = 0
        db_media.updated_at = datetime.now(timezone.utc)
        _session.add(db_media)
        demoted_ids.append(db_media.id)  # type: ignore
    _session.commit()
    return demoted_ids
