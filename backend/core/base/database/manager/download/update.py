from sqlmodel import Session

from app_logger import ModuleLogger
from core.base.database.manager.download.base import (
    convert_to_read_item,
)
from core.base.database.models.download import (
    Download,
    DownloadCreate,
    DownloadRead,
)
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError

logger = ModuleLogger("DownloadManager")


@manage_session
def update(
    download_id: int,
    download_create: DownloadCreate,
    *,
    _session: Session = None,  # type: ignore
) -> DownloadRead:
    """
    Update a download in the database.
    Args:
        download_id (int): The ID of the download to update.
        download_create (DownloadCreate): The new data for the download.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Returns:
        DownloadRead: The updated download.
    Raises:
        ItemNotFoundError: If the download with the given ID is not found.
        ValueError: If the download is invalid.
    """
    # Get the existing download from the database
    download_db = _session.get(Download, download_id)
    if download_db is None:
        raise ItemNotFoundError(model_name="Download", id=download_id)

    # Update the fields of the existing download
    _update_data = download_create.model_dump(exclude_unset=True)
    download_db.sqlmodel_update(_update_data)

    # Validate the updated download
    Download.model_validate(download_db)

    # Commit the changes to the database
    # _session.add(download_db)
    _session.commit()
    _session.refresh(download_db)
    logger.info(f"Updated download: {download_db.path}")
    return convert_to_read_item(download_db)


@manage_session
def mark_as_deleted(
    download_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """
    Mark a download as deleted in the database.
    Args:
        download_id (int): The ID of the download to mark as deleted.
        _session (Session, optional): A session to use for the database connection. Defaults to None.
    Raises:
        ItemNotFoundError: If the download with the given ID is not found.
    """
    # Get the existing download from the database
    download_db = _session.get(Download, download_id)
    if download_db is None:
        raise ItemNotFoundError(model_name="Download", id=download_id)

    # Mark the download as deleted
    download_db.is_deleted = True

    # Commit the changes to the database
    _session.add(download_db)
    _session.commit()
    logger.info(f"Marked download as deleted: {download_db.path}")
