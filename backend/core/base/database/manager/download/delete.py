from sqlmodel import Session, select

from app_logger import ModuleLogger
from core.base.database.models.download import Download
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError

logger = ModuleLogger("DownloadManager")


@manage_session
def delete(id: int, *, _session: Session = None) -> bool:  # type: ignore
    """
    Delete a download by id.
    Args:
        id (int): The id of the download to delete.
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        bool: True if the download was deleted successfully.
    Raises:
        ItemNotFoundError: If the download with the given id does not exist.
    """
    db_download = _session.get(Download, id)
    if not db_download:
        raise ItemNotFoundError("Download", id)

    # Delete the download
    _session.delete(db_download)
    _session.commit()
    logger.info(f"Deleted download record: {db_download.file_name}")
    return True


@manage_session
def delete_all_for_media(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete all downloads for a specific media item.\n
    Args:
        media_id (int): The ID of the media whose downloads to delete.\n
        _session (Session, Optional): A session to use for the database connection.\n
    Returns:
        int: Number of downloads deleted.
    """
    statement = select(Download).where(Download.media_id == media_id)
    downloads = _session.exec(statement).all()
    count = len(downloads)

    for download in downloads:
        _session.delete(download)

    _session.commit()
    return count
