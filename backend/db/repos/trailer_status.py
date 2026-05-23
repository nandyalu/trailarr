from dataclasses import dataclass
from datetime import datetime, timezone

from sqlmodel import Session, col, select, text

from db.engine import read_session, write_session
from db.models.customfilter import CustomFilter
from db.models.media import Media
from db.models.mediatrailerstatus import (
    MediaTrailerStatus,
    MediaTrailerStatusRead,
    TrailerSourceEnum,
    TrailerStatusEnum,
)
from db.models.trailerprofile import TrailerProfile
from exceptions import ItemNotFoundError


@dataclass
class TmdbPendingRow:
    row_id: int
    media_id: int
    profile_id: int
    season: int
    video_type: str
    status: TrailerStatusEnum
    tmdb_language: str
    youtube_id: str | None


@read_session
def get_pending_for_tmdb_refresh(*, _session: Session = None) -> list[TmdbPendingRow]:  # type: ignore
    """Return PENDING/NOT_AVAILABLE rows for monitored media, with joined video_type and tmdb_language."""
    stmt = (
        select(
            MediaTrailerStatus.id,
            MediaTrailerStatus.media_id,
            MediaTrailerStatus.profile_id,
            MediaTrailerStatus.season,
            MediaTrailerStatus.status,
            MediaTrailerStatus.youtube_id,
            TrailerProfile.video_type,
            TrailerProfile.tmdb_language,
        )
        .join(TrailerProfile, TrailerProfile.id == MediaTrailerStatus.profile_id)
        .join(Media, Media.id == MediaTrailerStatus.media_id)
        .where(
            MediaTrailerStatus.status.in_(  # type: ignore[union-attr]
                [TrailerStatusEnum.PENDING, TrailerStatusEnum.NOT_AVAILABLE]
            ),
            MediaTrailerStatus.profile_id.isnot(None),  # type: ignore[union-attr]
            col(Media.monitor).is_(True),
        )
    )
    rows = _session.exec(stmt).all()
    return [
        TmdbPendingRow(
            row_id=r.id,
            media_id=r.media_id,
            profile_id=r.profile_id,
            season=r.season,
            video_type=str(r.video_type),
            status=r.status,
            tmdb_language=str(r.tmdb_language) if r.tmdb_language else "",
            youtube_id=r.youtube_id,
        )
        for r in rows
    ]


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
    """Insert a new row. Returns None if an identical row already exists."""
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
    media_list: list,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Batch-insert PENDING rows for all matching media × seasons × sequences.

    Skips rows that already exist. Returns count of rows inserted.
    """
    now = datetime.now(timezone.utc)
    inserted = 0
    for media in media_list:
        if media.is_movie != for_movies:
            continue
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
                    continue
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
    return inserted


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
def get_pending_rows(limit: int = 100, *, _session: Session = None) -> list[MediaTrailerStatus]:  # type: ignore
    """Return PENDING rows for monitored media, ordered by profile priority DESC."""
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


@write_session
def update_row_youtube_id(
    row_id: int,
    youtube_id: str | None,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Cache a TMDB-sourced YouTube key on a status row (never writes to media.youtube_trailer_id)."""
    row = _session.get(MediaTrailerStatus, row_id)
    if row is None:
        return False
    row.youtube_id = youtube_id
    row.updated_at = datetime.now(timezone.utc)
    _session.add(row)
    _session.commit()
    return True


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


@write_session
def update_row_status(
    row_id: int,
    status: TrailerStatusEnum,
    download_id: int | None = None,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Update status (and optionally link a download) on a single row."""
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
def set_pending_rows_skipped_for_media(
    media_id: int,
    exclude_row_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Mark all PENDING rows for media_id as SKIPPED, except exclude_row_id."""
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
def on_download_deleted(download_id: int, *, _session: Session = None) -> int:  # type: ignore
    """Reset DOWNLOADED rows referencing download_id back to PENDING (intentional delete)."""
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
def on_file_deleted(download_id: int, *, _session: Session = None) -> int:  # type: ignore
    """Reset rows back to PENDING when just the file is deleted (Download record survives)."""
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


@read_session
def get_first_pending_row_for_profile(
    media_id: int,
    profile_id: int,
    season: int = 0,
    *,
    _session: Session = None,  # type: ignore
) -> MediaTrailerStatus | None:
    """Return the lowest-sequence PENDING row for (media_id, profile_id, season)."""
    return _session.exec(
        select(MediaTrailerStatus)
        .where(
            MediaTrailerStatus.media_id == media_id,
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.season) == season,
            MediaTrailerStatus.status == TrailerStatusEnum.PENDING,
        )
        .order_by(col(MediaTrailerStatus.sequence))
        .limit(1)
    ).first()


@write_session
def delete_undownloaded_rows_for_profile(
    profile_id: int,
    media_ids: list[int],
    *,
    _session: Session = None,  # type: ignore
) -> int:
    """Delete rows for profile_id/media_ids where no file was ever downloaded."""
    rows = _session.exec(
        select(MediaTrailerStatus).where(
            MediaTrailerStatus.profile_id == profile_id,
            col(MediaTrailerStatus.media_id).in_(media_ids),
            MediaTrailerStatus.linked_download_id == None,  # noqa: E711
            MediaTrailerStatus.status != TrailerStatusEnum.UNMONITORED,
        )
    ).all()
    count = len(rows)
    for row in rows:
        _session.delete(row)
    _session.commit()
    return count
