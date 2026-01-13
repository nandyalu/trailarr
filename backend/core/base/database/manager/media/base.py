from typing import Sequence
from sqlmodel import Session

from core.base.database.models.media import (
    Media,
    MediaCreate,
    MediaRead,
    MediaUpdate,
    MonitorStatus,
)
from exceptions import ItemNotFoundError


def _convert_to_read_list(db_media_list: Sequence[Media]) -> list[MediaRead]:
    """🚨This is a private method🚨 \n
    Convert a list of Media objects to a list of MediaRead objects.\n"""
    if not db_media_list or len(db_media_list) == 0:
        return []
    media_read_list: list[MediaRead] = []
    for db_media in db_media_list:
        media_read = MediaRead.model_validate(db_media)
        media_read_list.append(media_read)
    return media_read_list


def _get_db_item(media_id: int, session: Session) -> Media:
    """🚨This is a private method🚨 \n
    Get a media item from the database by id.\n
    Args:
        media_id (int): The id of the media item to get.
        session (Session): A session to use for the database connection.\n
    Returns:
        Media: The media object if it exists.
    Raises:
        ItemNotFoundError: If the media item with provided id doesn't exist.
    """
    db_media = session.get(Media, media_id)
    if not db_media:
        raise ItemNotFoundError("Media", media_id)
    return db_media


def has_updated(
    db_media: Media,
    update: MediaCreate | MediaRead | MediaUpdate,
    *,
    ignore_attrs: set[str] | None = None,
) -> bool:
    """🚨This is a private method🚨 \n
    Check if certain fields in the media update differ from the existing media object.\n
    Field that will be compared:
        - title
        - year
        - media_exists
        - media_filename
        - folder_path
        - trailer_exists
        - monitor
        - arr_monitored
    Args:
        db_media (Media): The existing media object from the database.
        update (MediaCreate | MediaRead | MediaUpdate): The media update object to compare.\n
    Returns:
        bool: True if any fields have changed, False otherwise.
    """
    _checked_fields = {
        "title",
        "year",
        "media_exists",
        "media_filename",
        "folder_path",
        "trailer_exists",
        "monitor",
        "arr_monitored",
    }
    # Remove ignored attributes from the checked fields
    if ignore_attrs:
        _checked_fields = _checked_fields.difference(ignore_attrs)
    # Compare the fields
    db_data = db_media.model_dump()
    update_data = update.model_dump()
    for field in _checked_fields:
        if update_data.get(field) is not None:
            if db_data.get(field) != update_data.get(field):
                print(
                    f"{field} changed, {db_data.get(field)} ->"
                    f" {update_data.get(field)}"
                )
                return True
    return False
    # if update.title is not None:
    #     if db_media.title != update.title:
    #         print(f"title changed, {db_media.title} -> {update.title}")
    #         return True
    # if update.year is not None:
    #     if db_media.year != update.year:
    #         print(f"year changed, {db_media.year} -> {update.year}")
    #         return True
    # if update.media_exists is not None:
    #     if db_media.media_exists != update.media_exists:
    #         print(
    #             f"media_exists changed, {db_media.media_exists} ->"
    #             f" {update.media_exists}"
    #         )
    #         return True
    # if update.media_filename is not None:
    #     if db_media.media_filename != update.media_filename:
    #         print(
    #             f"media_filename changed, {db_media.media_filename} ->"
    #             f" {update.media_filename}"
    #         )
    #         return True
    # if update.folder_path is not None:
    #     if db_media.folder_path != update.folder_path:
    #         print(
    #             f"folder_path changed, {db_media.folder_path} ->"
    #             f" {update.folder_path}"
    #         )
    #         return True
    # if update.trailer_exists is not None:
    #     if db_media.trailer_exists != update.trailer_exists:
    #         print(
    #             f"trailer_exists changed, {db_media.trailer_exists} ->"
    #             f" {update.trailer_exists}"
    #         )
    #         return True
    # if update.monitor is not None:
    #     if db_media.monitor != update.monitor:
    #         print(f"monitor changed, {db_media.monitor} -> {update.monitor}")
    #         return True
    # if update.arr_monitored is not None:
    #     if db_media.arr_monitored != update.arr_monitored:
    #         print(
    #             f"arr_monitored changed, {db_media.arr_monitored} ->"
    #             f" {update.arr_monitored}"
    #         )
    #         return True
    # return False


def get_status(
    monitor: bool, trailer_exists: bool, status: MonitorStatus
) -> MonitorStatus:
    """🚨This is a private method🚨 \n
    Get the monitor status string based on monitor and trailer_exists flags.\n
    Args:
        monitor (bool): Whether monitoring is enabled for the media.
        trailer_exists (bool): Whether the trailer already exists for the media.
        status (MonitorStatus): Current monitor status of the media.\n
    Returns:
        MonitorStatus: The monitor status.
    """
    if status in (
        MonitorStatus.DOWNLOADING,
        MonitorStatus.MISSING,
    ):
        return status
    if trailer_exists:
        return MonitorStatus.DOWNLOADED
    if monitor:
        return MonitorStatus.MONITORED
    return MonitorStatus.MISSING
