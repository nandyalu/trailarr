from sqlmodel import Session, select, text
from . import base
from core.base.database.models.download import (
    Download,
    DownloadRead,
)
from core.base.database.utils.engine import manage_session


@manage_session
def read(
    download_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> DownloadRead:
    """
    Get a download by ID.
    Args:
        download_id (int): The ID of the download to retrieve.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        DownloadRead: The download (read-only).
    Raises:
        ItemNotFoundError: If the download with the given ID is not found.
    """
    db_download = base._get_db_item(download_id, _session)
    return base.convert_to_read_item(db_download)


@manage_session
def read_all_raw(
    *,
    _session: Session = None,  # type: ignore
) -> list[dict]:
    """Get all downloads in raw dictionary format.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[dict]: List of all downloads as dictionaries.
    """
    query = text("SELECT * FROM download")
    result = _session.execute(query)
    rows = []
    for row in result.mappings():
        item = dict(row)
        rows.append(item)
    return rows


@manage_session
def read_all(
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadRead]:
    """
    Get all downloads.
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[DownloadRead]: List of downloads (read-only).
    """
    statement = select(Download)
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)


@manage_session
def read_by_media_id(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadRead]:
    """
    Get all downloads for a specific media ID.
    Args:
        media_id (int): The media ID to filter downloads by.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[DownloadRead]: List of downloads (read-only).
    """
    statement = select(Download).where(Download.media_id == media_id)
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)


@manage_session
def read_by_profile_id(
    profile_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadRead]:
    """
    Get all downloads for a specific profile ID.
    Args:
        profile_id (int): The profile ID to filter downloads by.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[DownloadRead]: List of downloads (read-only).
    """
    statement = select(Download).where(Download.profile_id == profile_id)
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)
