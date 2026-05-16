from sqlmodel import Session, col, select, text

from . import base
from core.base.database.models.media import Media
from core.base.database.models.mediatrailerstatus import (
    MediaTrailerStatus,
    MediaTrailerStatusRead,
    TrailerStatusEnum,
)
from core.base.database.models.trailerprofile import TrailerProfile
from core.base.database.utils.engine import read_session


@read_session
def get_pending_rows(
    limit: int = 100,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaTrailerStatus]:
    """Return up to *limit* PENDING rows where the media is monitored.

    Ordered by profile priority ASC, then media_id, then sequence ASC.
    Profile rows with NULL profile_id (manual/unattributed) are excluded.
    """
    stmt = (
        select(MediaTrailerStatus)
        .join(Media, Media.id == MediaTrailerStatus.media_id)  # type: ignore[arg-type]
        .join(TrailerProfile, TrailerProfile.id == MediaTrailerStatus.profile_id)  # type: ignore[arg-type]
        .where(
            MediaTrailerStatus.status == TrailerStatusEnum.PENDING,
            MediaTrailerStatus.profile_id.isnot(None),  # type: ignore[union-attr]
            col(Media.monitor).is_(True),
        )
        .order_by(
            col(TrailerProfile.priority).desc(),
            col(MediaTrailerStatus.media_id),
            col(MediaTrailerStatus.sequence),
        )
        .limit(limit)
    )
    return list(_session.exec(stmt).all())


@read_session
def get_rows_for_media(
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[MediaTrailerStatusRead]:
    """Return all MediaTrailerStatus rows for a given media_id, with profile fields joined."""
    stmt = select(MediaTrailerStatus).where(
        MediaTrailerStatus.media_id == media_id
    )
    rows = list(_session.exec(stmt).all())
    return [base._to_read(row, _session) for row in rows]


@read_session
def get_all_rows(
    *,
    _session: Session = None,  # type: ignore
) -> list[dict]:
    """Return all MediaTrailerStatus rows as raw dicts with joined profile_name and video_type.

    Uses a raw SQL query to avoid loading thousands of ORM objects into memory.
    """
    query = text(
        """
        SELECT
            mts.id,
            mts.media_id,
            mts.profile_id,
            mts.season,
            mts.sequence,
            mts.status,
            mts.source,
            mts.linked_download_id,
            mts.created_at,
            mts.updated_at,
            tp.video_type,
            cf.filter_name AS profile_name
        FROM mediatrailerstatus mts
        LEFT JOIN trailerprofile tp ON mts.profile_id = tp.id
        LEFT JOIN customfilter cf ON tp.customfilter_id = cf.id
        """
    )
    result = _session.execute(query)
    return [dict(row) for row in result.mappings()]


@read_session
def read(
    row_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> MediaTrailerStatusRead | None:
    """Return a single MediaTrailerStatusRead by id, or None if not found."""
    row = _session.get(MediaTrailerStatus, row_id)
    if row is None:
        return None
    return MediaTrailerStatusRead.model_validate(row)
