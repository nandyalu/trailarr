# backend/core/base/database/manager/trailerstatusmanager.py
"""Database manager for MediaTrailerStatus records."""

from datetime import datetime, timezone

from sqlmodel import Session, col, select

from app_logger import ModuleLogger
from core.base.database.models.mediatrailerstatus import (
    MediaTrailerStatus,
    MediaTrailerStatusRead,
    TrailerStatusEnum,
    TrailerSourceEnum,
)
from core.base.database.utils.engine import write_session

logger = ModuleLogger("TrailerStatusManager")

_SKIP_STATUSES = {
    TrailerStatusEnum.UNMONITORED,
    TrailerStatusEnum.NOT_AVAILABLE,
    TrailerStatusEnum.SKIPPED,
    TrailerStatusEnum.DOWNLOADED,
}


@write_session
def get_pending_rows(
    limit: int = 100,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaTrailerStatus]:
    """Return up to *limit* PENDING rows where the media is monitored.

    Ordered by profile priority ASC, then media_id, then sequence ASC.
    Profile rows with NULL profile_id (manual/unattributed) are excluded.
    """
    from core.base.database.models.media import Media

    stmt = (
        select(MediaTrailerStatus)
        .join(Media, Media.id == MediaTrailerStatus.media_id)  # type: ignore[arg-type]
        .where(
            MediaTrailerStatus.status == TrailerStatusEnum.PENDING,
            MediaTrailerStatus.profile_id.isnot(None),  # type: ignore[union-attr]
            col(Media.monitor).is_(True),
        )
        .order_by(
            col(MediaTrailerStatus.profile_id),
            col(MediaTrailerStatus.media_id),
            col(MediaTrailerStatus.sequence),
        )
        .limit(limit)
    )
    return list(_session.exec(stmt).all())


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
def create_row(
    media_id: int,
    profile_id: int | None,
    season: int = 0,
    sequence: int = 1,
    status: TrailerStatusEnum = TrailerStatusEnum.PENDING,
    source: TrailerSourceEnum = TrailerSourceEnum.APP,
    *,
    _session: Session = None,  # type: ignore
) -> MediaTrailerStatus | None:
    """Insert a new MediaTrailerStatus row.

    Returns None if a row with the same (media_id, profile_id, season, sequence)
    already exists (unique constraint).
    """
    existing = _session.exec(
        select(MediaTrailerStatus).where(
            MediaTrailerStatus.media_id == media_id,
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.season) == season,
            col(MediaTrailerStatus.sequence) == sequence,
        )
    ).first()
    if existing:
        return None
    row = MediaTrailerStatus(
        media_id=media_id,
        profile_id=profile_id,
        season=season,
        sequence=sequence,
        status=status,
        source=source,
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row


@write_session
def create_rows_for_profile(
    profile_id: int,
    for_movies: bool,
    max_count: int,
    download_season_videos: bool,
    media_list: list,  # list of Media-like objects with .id, .is_movie, .season_count, .monitor
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Batch-insert PENDING rows for all matching media × seasons × sequences.

    Skips rows that already exist or whose existing row is UNMONITORED.
    Returns count of rows actually inserted.
    """
    now = datetime.now(timezone.utc)
    inserted = 0
    for media in media_list:
        if media.is_movie != for_movies:
            continue
        # Build the set of (season, sequence) pairs to create
        seasons: list[int] = [0]
        if not for_movies and download_season_videos:
            seasons = list(range(0, (media.season_count or 0) + 1))
        for season in seasons:
            for seq in range(1, max_count + 1):
                existing = _session.exec(
                    select(MediaTrailerStatus).where(
                        MediaTrailerStatus.media_id == media.id,
                        MediaTrailerStatus.profile_id == profile_id,
                        col(MediaTrailerStatus.season) == season,
                        col(MediaTrailerStatus.sequence) == seq,
                    )
                ).first()
                if existing:
                    continue  # Never overwrite UNMONITORED or any existing row
                row = MediaTrailerStatus(
                    media_id=media.id,
                    profile_id=profile_id,
                    season=season,
                    sequence=seq,
                    status=TrailerStatusEnum.PENDING,
                    source=TrailerSourceEnum.APP,
                    created_at=now,
                    updated_at=now,
                )
                _session.add(row)
                inserted += 1
    _session.commit()
    logger.info(f"create_rows_for_profile: inserted {inserted} rows for profile {profile_id}")
    return inserted


@write_session
def get_rows_for_media(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaTrailerStatus]:
    """Return all MediaTrailerStatus rows for a given media_id."""
    stmt = select(MediaTrailerStatus).where(
        MediaTrailerStatus.media_id == media_id
    )
    return list(_session.exec(stmt).all())


@write_session
def get_all_rows(
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaTrailerStatus]:
    """Return all MediaTrailerStatus rows (for the bulk raw endpoint)."""
    return list(_session.exec(select(MediaTrailerStatus)).all())


@write_session
def delete_undownloaded_rows_for_profile(
    profile_id: int,
    media_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete rows for *profile_id* / *media_ids* where no file was ever downloaded.

    Rows with a linked_download_id (file exists) are left untouched.
    Returns the number of rows deleted.
    """
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.media_id).in_(media_ids),
            MediaTrailerStatus.linked_download_id == None,  # noqa: E711
        )
    ).all()
    count = len(rows)
    for row in rows:
        _session.delete(row)
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


def read(row_id: int) -> MediaTrailerStatusRead | None:
    """Return a single MediaTrailerStatusRead by id, or None if not found."""
    from core.base.database.utils.engine import read_session as _read_session

    with _read_session() as session:
        row = session.get(MediaTrailerStatus, row_id)
        if row is None:
            return None
        return MediaTrailerStatusRead.model_validate(row)
