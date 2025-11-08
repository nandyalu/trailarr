from sqlmodel import Session

from app_logger import ModuleLogger
from core.base.database.manager.download.base import convert_to_read_item

from core.base.database.models.download import (
    Download,
    DownloadCreate,
    DownloadRead,
)
from core.base.database.utils.engine import manage_session

logger = ModuleLogger("DownloadManager")


@manage_session
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
    logger.info(f"Created download: {db_download.file_name}")
    return convert_to_read_item(db_download)
