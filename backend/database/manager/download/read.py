from sqlmodel import Session, col, desc, select, text
from . import base
from database.models.download import (
    Download,
    DownloadRead,
)
from database.engine import read_session


@read_session
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


@read_session
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
    query = text("SELECT * FROM download ORDER BY added_at DESC")
    result = _session.execute(query)
    rows = []
    for row in result.mappings():
        item = dict(row)
        rows.append(item)
    return rows


@read_session
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
    statement = select(Download).order_by(desc(Download.added_at))
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)


@read_session
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
    statement = statement.order_by(desc(Download.added_at))
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)


@read_session
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
    statement = statement.order_by(desc(Download.added_at))
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)


@read_session
def read_unattributed(
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadRead]:
    """
    Get all active downloads not attributed to any profile.
    Active means the file still exists on disk (file_exists=True);
    unattributed means profile_id=0 (e.g. trailers found on disk by the
    files scan that could not be linked to a profile at the time).
    Args:
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        list[DownloadRead]: List of downloads (read-only), ordered by
            media_id, then oldest first.
    """
    statement = (
        select(Download)
        .where(Download.profile_id == 0)
        .where(col(Download.file_exists).is_(True))
        .order_by(col(Download.media_id), col(Download.added_at))
    )
    db_downloads = _session.exec(statement).all()
    return base.convert_to_read_list(db_downloads)
