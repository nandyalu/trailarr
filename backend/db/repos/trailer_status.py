from datetime import datetime, timezone

from sqlmodel import Session, col, select, text

from db.engine import read_session, write_session
from db.models.customfilter import CustomFilter
from db.models.mediatrailerstatus import (
    MediaTrailerStatus,
    MediaTrailerStatusRead,
    TrailerSourceEnum,
    TrailerStatusEnum,
)
from db.models.trailerprofile import TrailerProfile
from exceptions import ItemNotFoundError


def _get_or_404(row_id: int, session: Session) -> MediaTrailerStatus:
    row = session.get(MediaTrailerStatus, row_id)
    if row is None:
        raise ItemNotFoundError("MediaTrailerStatus", row_id)
    return row


def _to_read(row: MediaTrailerStatus, session: Session) -> MediaTrailerStatusRead:
    read = MediaTrailerStatusRead.model_validate(row)
    if row.profile_id is not None:
        profile = session.get(TrailerProfile, row.profile_id)
        if profile is not None:
            read.video_type = profile.video_type
            cf = session.get(CustomFilter, profile.customfilter_id)
            if cf is not None:
                read.profile_name = cf.filter_name
    return read


@read_session
def read(row_id: int, *, _session: Session = None) -> MediaTrailerStatusRead | None:  # type: ignore
    row = _session.get(MediaTrailerStatus, row_id)
    if row is None:
        return None
    return MediaTrailerStatusRead.model_validate(row)


@read_session
def get_rows_for_media(media_id: int, *, _session: Session = None) -> list[MediaTrailerStatusRead]:  # type: ignore
    rows = _session.exec(
        select(MediaTrailerStatus).where(MediaTrailerStatus.media_id == media_id)
    ).all()
    return [_to_read(row, _session) for row in rows]


@read_session
def get_rows_for_media_and_profiles(
    media_id: int,
    profile_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> dict[tuple[int, int, int], MediaTrailerStatus]:
    """Return existing rows for one media item keyed by (profile_id, season, sequence)."""
    if not profile_ids:
        return {}
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            MediaTrailerStatus.media_id == media_id,
            col(MediaTrailerStatus.profile_id).in_(profile_ids),
        )
    ).all()
    return {(r.profile_id, r.season, r.sequence): r for r in rows}


@read_session
def get_all_rows(*, _session: Session = None) -> list[dict]:  # type: ignore
    """Return all rows as raw dicts with joined profile_name and video_type."""
    query = text(
        """
        SELECT
            mts.id, mts.media_id, mts.profile_id, mts.season, mts.sequence,
            mts.status, mts.source, mts.linked_download_id, mts.youtube_id,
            mts.created_at, mts.updated_at,
            tp.video_type,
            cf.filter_name AS profile_name
        FROM mediatrailerstatus mts
        LEFT JOIN trailerprofile tp ON mts.profile_id = tp.id
        LEFT JOIN customfilter cf ON tp.customfilter_id = cf.id
        """
    )
    return [dict(row) for row in _session.execute(query).mappings()]


@read_session
def get_first_row_for_profile(
    media_id: int,
    profile_id: int,
    season: int = 0,
    *,
    _session: Session = None,  # type: ignore
) -> MediaTrailerStatus | None:
    """Return the lowest-sequence row (any status) for (media_id, profile_id, season).

    Used by the scan service to find an existing slot to link a discovered file to.
    """
    return _session.exec(
        select(MediaTrailerStatus)
        .where(
            MediaTrailerStatus.media_id == media_id,
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.season) == season,
        )
        .order_by(col(MediaTrailerStatus.sequence))
        .limit(1)
    ).first()


@write_session
def update_row_status(
    row_id: int,
    status: TrailerStatusEnum,
    download_id: int | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Update status (and optionally link a download) on a single row. Used by the API."""
    row = _session.get(MediaTrailerStatus, row_id)
    if row is None:
        return False
    row.status = status
    if download_id is not None:
        row.linked_download_id = download_id
    row.updated_at = datetime.now(timezone.utc)
    _session.add(row)
    _session.commit()
    return True


@write_session
def upsert_slot_status(
    media_id: int,
    profile_id: int,
    season: int,
    sequence: int,
    status: TrailerStatusEnum,
    download_id: int | None = None,
    *,
    increment_attempt: bool = False,
    _session: Session = None,  # type: ignore
) -> MediaTrailerStatus:
    """Create or update status for a specific (media, profile, season, sequence) slot.

    Creates a new row if none exists. `increment_attempt=True` bumps attempt_count
    (used when marking a slot as FAILED after exhausting retries).
    """
    row = _session.exec(
        select(MediaTrailerStatus).where(
            MediaTrailerStatus.media_id == media_id,
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.season) == season,
            col(MediaTrailerStatus.sequence) == sequence,
        )
    ).first()
    now = datetime.now(timezone.utc)
    if row is None:
        row = MediaTrailerStatus(
            media_id=media_id,
            profile_id=profile_id,
            season=season,
            sequence=sequence,
            status=status,
            source=TrailerSourceEnum.APP,
            created_at=now,
            updated_at=now,
        )
    else:
        row.status = status
        row.updated_at = now
        if increment_attempt:
            row.attempt_count = (row.attempt_count or 0) + 1
    if download_id is not None:
        row.linked_download_id = download_id
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row


@write_session
def on_file_deleted(download_id: int, *, _session: Session = None) -> int:  # type: ignore
    """Reset rows back to PENDING when the file is deleted (Download record survives).

    Resetting to PENDING makes the slot eligible for re-download on the next pipeline run.
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
