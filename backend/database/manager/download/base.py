"""Shared helpers for reading and writing a trailer download."""

from typing import Sequence

from sqlmodel import Session, col, select

from database.models.download import (
    Download,
    DownloadRead,
)
from exceptions import ItemNotFoundError


def convert_to_read_item(
    db_download: Download,
) -> DownloadRead:
    """
    Convert a Download database object to a DownloadRead object.
    Args:
        db_download (Download): Download database object
    Returns:
        DownloadRead: DownloadRead object
    """
    download_read = DownloadRead.model_validate(db_download)
    return download_read


def convert_to_read_list(
    db_download_list: Sequence[Download],
) -> list[DownloadRead]:
    """
    Convert a list of Download database objects to a list of \
        DownloadRead objects.
    Args:
        db_download_list (list[Download]): List of Download\
            database objects
    Returns:
        list[DownloadRead]: List of DownloadRead objects
    """
    if not db_download_list or len(db_download_list) == 0:
        return []
    download_read_list: list[DownloadRead] = []
    for db_download in db_download_list:
        download_read = DownloadRead.model_validate(db_download)
        download_read_list.append(download_read)
    return download_read_list


def _get_db_item(download_id: int, session: Session) -> Download:
    """
    Get a Download database object from a list by ID.
    Args:
        download_id (int): ID of the Download to get
        session (Session): SQLModel Session
    Returns:
        Download: Download database object
    Raises:
        ItemNotFoundError: If the Download with the given ID is not found.
    """
    db_download = session.get(Download, download_id)
    if db_download is None:
        raise ItemNotFoundError(model_name="Download", id=download_id)
    return db_download


def _has_active_download_at(path: str, session: Session) -> bool:
    """True when an active download has the path.

    Two active downloads for one file are a duplicate. A caller runs this
    in its write session, so that no other write can come between the
    check and its own write. `ix_download_path` makes it a short lookup.
    Args:
        path (str): The path of the file.
        session (Session): SQLModel Session
    Returns:
        bool: True when an active download has the path.
    """
    active_copy = session.exec(
        select(Download.id)
        .where(Download.path == path)
        .where(col(Download.file_exists).is_(True))
        .limit(1)
    ).first()
    return active_copy is not None
