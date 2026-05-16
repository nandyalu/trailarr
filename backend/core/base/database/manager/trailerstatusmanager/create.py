from datetime import datetime, timezone

from sqlmodel import Session, col, select

from core.base.database.models.mediatrailerstatus import (
    MediaTrailerStatus,
    TrailerSourceEnum,
    TrailerStatusEnum,
)
from core.base.database.utils.engine import write_session


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
    from app_logger import ModuleLogger

    logger = ModuleLogger("TrailerStatusManager")
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
