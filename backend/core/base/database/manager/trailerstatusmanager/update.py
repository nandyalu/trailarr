from datetime import datetime, timezone

from sqlmodel import Session, col, select

from core.base.database.models.mediatrailerstatus import (
    MediaTrailerStatus,
    TrailerStatusEnum,
)
from core.base.database.utils.engine import write_session


@write_session
def update_row_status(
    row_id: int,
    status: TrailerStatusEnum,
    download_id: int | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Update status (and optionally link a download) on a single row.

    Returns True if the row was found and updated.
    """
    from app_logger import ModuleLogger

    logger = ModuleLogger("TrailerStatusManager")
    row = _session.get(MediaTrailerStatus, row_id)
    if row is None:
        logger.warning(f"MediaTrailerStatus row {row_id} not found")
        return False
    row.status = status
    if download_id is not None:
        row.linked_download_id = download_id
    row.updated_at = datetime.now(timezone.utc)
    _session.add(row)
    _session.commit()
    return True


@write_session
def set_pending_rows_skipped_for_media(
    media_id: int,
    exclude_row_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Mark all PENDING rows for *media_id* as SKIPPED, except *exclude_row_id*.

    Called after a successful download when stop_monitoring=True so that
    lower-priority profiles are not attempted for this media item.
    Returns the count of rows updated.
    """
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            col(MediaTrailerStatus.media_id) == media_id,
            MediaTrailerStatus.status == TrailerStatusEnum.PENDING,
            col(MediaTrailerStatus.id) != exclude_row_id,
        )
    ).all()
    now = datetime.now(timezone.utc)
    count = 0
    for row in rows:
        row.status = TrailerStatusEnum.SKIPPED
        row.updated_at = now
        _session.add(row)
        count += 1
    _session.commit()
    return count


@write_session
def on_download_deleted(
    download_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Called when a Download record is deleted via the app (intentional).

    Resets all DOWNLOADED rows that reference *download_id* back to PENDING
    so the download loop will re-attempt them.
    UNMONITORED rows are left unchanged.
    No Issue is created — this is an intentional action.
    Returns count of rows reset.
    """
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            col(MediaTrailerStatus.linked_download_id) == download_id,
            MediaTrailerStatus.status != TrailerStatusEnum.UNMONITORED,
        )
    ).all()
    now = datetime.now(timezone.utc)
    count = 0
    for row in rows:
        row.status = TrailerStatusEnum.PENDING
        row.linked_download_id = None
        row.updated_at = now
        _session.add(row)
        count += 1
    _session.commit()
    return count


@write_session
def on_file_deleted(
    download_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Called when just the file is deleted via the app UI (Download record survives).

    Same reset as on_download_deleted but leaves linked_download_id intact so the
    Download record still points to the (now missing) path.
    No Issue is created — intentional action.
    Returns count of rows reset.
    """
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            col(MediaTrailerStatus.linked_download_id) == download_id,
            MediaTrailerStatus.status != TrailerStatusEnum.UNMONITORED,
        )
    ).all()
    now = datetime.now(timezone.utc)
    count = 0
    for row in rows:
        row.status = TrailerStatusEnum.PENDING
        row.updated_at = now
        _session.add(row)
        count += 1
    _session.commit()
    return count
