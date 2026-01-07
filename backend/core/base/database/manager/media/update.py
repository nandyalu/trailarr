from datetime import datetime, timezone
from typing import Sequence
from sqlmodel import Session

from . import base
from core.base.database.models.helpers import MediaImage, MediaUpdateDC
from core.base.database.models.media import (
    MediaUpdate,
    MonitorStatus,
)
from core.base.database.utils.engine import manage_session


@manage_session
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


@manage_session
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


@manage_session
def update_media_status_bulk(
    media_update_list: Sequence[MediaUpdateDC],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the monitoring status of multiple media items in the database at once.\n
    Args:
        media_update_list (Sequence[MediaUpdateProtocol]): Sequence of media update objects.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    for media_update in media_update_list:
        update_media_status(media_update, _session=_session, _commit=False)
    _session.commit()
    return


@manage_session
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


@manage_session
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


@manage_session
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
    # Update status based on monitor status
    if db_media.monitor:
        db_media.status = MonitorStatus.MONITORED
    else:
        db_media.status = MonitorStatus.MISSING
    _session.add(db_media)
    _session.commit()
    return None


# TODO: Split this up into separate simpler methods
@manage_session
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
    # If trailer exists, disable monitoring
    if trailer_exists:
        db_media.monitor = False
        db_media.status = MonitorStatus.DOWNLOADED
    else:
        if db_media.monitor:
            db_media.status = MonitorStatus.MONITORED
        else:
            db_media.status = MonitorStatus.MISSING
    _session.add(db_media)
    if _commit:
        _session.commit()
    return None


@manage_session
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
    return
