"""Add a trailer download to the database."""

from sqlmodel import Session

from . import base
from database.models.download import (
    Download,
    DownloadCreate,
    DownloadRead,
)
from database.engine import write_session


@write_session
def create(
    download_create: DownloadCreate,
    *,
    _session: Session = None,  # type: ignore
) -> DownloadRead:
    """
    Create a new download.
    Args:
        download_create (DownloadCreate): DownloadCreate model
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        DownloadRead: DownloadRead object
    Raises:
        ValidationError: If the input data is not valid.
    """
    # Create a db Download object
    db_download = Download.model_validate(download_create)
    # Save to database
    _session.add(db_download)
    _session.commit()
    _session.refresh(db_download)
    return base.convert_to_read_item(db_download)


@write_session
def create_if_path_untracked(
    download_create: DownloadCreate,
    *,
    _session: Session = None,  # type: ignore
) -> DownloadRead | None:
    """
    Create a new download, unless an active download has its path.
    The disk scan records a file that no download had when the scan read
    the media item. The Cleanup Task or the download task can restore a
    deleted download of the same file in the meantime. This checks again,
    under the write lock, as `mark_as_restored` does. So one file never
    gets two active downloads.
    Args:
        download_create (DownloadCreate): DownloadCreate model
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        DownloadRead | None: The new download. None when an active download
            has the path.
    Raises:
        ValidationError: If the input data is not valid.
    """
    if base._has_active_download_at(download_create.path, _session):
        return None
    db_download = Download.model_validate(download_create)
    _session.add(db_download)
    _session.commit()
    _session.refresh(db_download)
    return base.convert_to_read_item(db_download)
