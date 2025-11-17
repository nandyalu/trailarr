from datetime import datetime, timezone
from typing import Sequence
from sqlmodel import Session

from . import base
from core.base.database.models.helpers import MediaUpdateDC
from core.base.database.models.media import (
    MediaUpdate,
    MonitorStatus,
)
from core.base.database.utils.engine import manage_session


@manage_session
def _update(
    media_update: MediaUpdate,
    *,
    _commit: bool = True,
    _session: Session = None,  # type: ignore
) -> None:
    """Update an existing media item in the database by id.\n
    Args:
        media_update (MediaUpdate): The media data to update.
        _commit (bool, Optional): Flag to `commit` the changes. Default is `True`.
        _session (Session, Optional): A session to use for the database connection. \
            Default is None, in which case a new session will be created. \n
    Returns:
        None
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = base._get_db_item(media_update.id, _session)
    media_update_data = media_update.model_dump(
        exclude_unset=True,
        # exclude_defaults=True,
        exclude_none=True,
        exclude={"youtube_trailer_id", "downloaded_at"},
    )
    db_media.sqlmodel_update(media_update_data)
    if _session.is_modified(db_media):
        db_media.updated_at = datetime.now(timezone.utc)
    _session.add(db_media)
    if _commit:
        _session.commit()
    return


@manage_session
def update_bulk(
    media_updates: list[MediaUpdate],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update multiple media items in the database at once.\n
    Args:
        media_updates (list[MediaUpdate]): List of media update objects.
        _session (Session, Optional=None): A session to use for the database connection.
            - Default is `None`, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    for media_update in media_updates:
        _update(media_update, _session=_session, _commit=False)
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
    if media_update.trailer_exists is not None:
        db_media.trailer_exists = media_update.trailer_exists
    # If trailer exists, disable monitoring
    if db_media.trailer_exists:
        db_media.monitor = False
    else:
        db_media.monitor = media_update.monitor
    # Update status based on monitor status and trailer existence if not downloading
    if media_update.status not in (
        MonitorStatus.DOWNLOADING,
        MonitorStatus.MISSING,
    ):
        if db_media.trailer_exists:
            _status = MonitorStatus.DOWNLOADED
        else:
            if db_media.monitor:
                _status = MonitorStatus.MONITORED
            else:
                _status = MonitorStatus.MISSING
    else:  # If not downloading/missing, set received status
        _status = media_update.status
    db_media.status = _status
    if media_update.downloaded_at:
        db_media.downloaded_at = media_update.downloaded_at
    if media_update.yt_id:
        db_media.youtube_trailer_id = media_update.yt_id
    if _session.is_modified(db_media):
        db_media.updated_at = datetime.now(timezone.utc)
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
        db_media.monitor = monitor
        db_media.status = MonitorStatus.MONITORED
        db_media.updated_at = datetime.now(timezone.utc)
        _session.add(db_media)
        if _commit:
            _session.commit()
        msg = f"Media '{db_media.title}' [{db_media.id}] is now monitored"
        return msg, True
    # Monitor = False
    # If trailer exists, set status to downloaded, else set to missing
    db_media.monitor = monitor
    if db_media.trailer_exists:
        db_media.status = MonitorStatus.DOWNLOADED
    else:
        db_media.status = MonitorStatus.MISSING
    db_media.updated_at = datetime.now(timezone.utc)
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
    db_media.trailer_exists = trailer_exists
    db_media.updated_at = datetime.now(timezone.utc)
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
def update_trailer_exists_bulk(
    media_updates: list[tuple[int, bool]],
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Update the trailer_exists status of multiple media items in the database at once.\n
    Args:
        media_updates (list[tuple[int, bool]]): List of tuples with media id and \
            trailer_exists status.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.
    Returns:
        None
    Raises:
        ItemNotFoundError: If any of the media items with provided id's don't exist.
    """
    for media_id, trailer_exists in media_updates:
        update_trailer_exists(
            media_id, trailer_exists, _session=_session, _commit=False
        )
    _session.commit()
    return


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
    db_media.updated_at = datetime.now(timezone.utc)
    _session.add(db_media)
    if _commit:
        _session.commit()
    return
