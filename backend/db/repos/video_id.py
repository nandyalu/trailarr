from datetime import datetime, timezone

from sqlmodel import Session, col, select

from db.engine import read_session, write_session
from db.models.videoid import VideoId, VideoIdRead, VideoIdSourceEnum
from exceptions import ItemNotFoundError


def _to_read(obj: VideoId) -> VideoIdRead:
    return VideoIdRead.model_validate(obj)


@read_session
def get_for_media(media_id: int, *, _session: Session = None) -> list[VideoIdRead]:  # type: ignore
    """Return all VideoId records for a media item."""
    rows = _session.exec(
        select(VideoId)
        .where(VideoId.media_id == media_id)
        .order_by(col(VideoId.source), col(VideoId.video_type))
    ).all()
    return [_to_read(r) for r in rows]


@read_session
def get_best_for_download(
    media_id: int,
    video_type: str,
    language: str = "",
    season: int = 0,
    *,
    _session: Session = None,  # type: ignore
) -> str | None:
    """Return the best YouTube ID for download, in priority order: user → arr → tmdb.

    For tmdb records, prefers an exact language match over an empty-language record.
    Returns None if no matching record exists.
    """
    rows = _session.exec(
        select(VideoId).where(
            VideoId.media_id == media_id,
            VideoId.video_type == video_type,
            col(VideoId.season) == season,
        )
    ).all()

    if not rows:
        return None

    source_priority = {VideoIdSourceEnum.USER: 0, VideoIdSourceEnum.ARR: 1, VideoIdSourceEnum.TMDB: 2}

    def sort_key(r: VideoId):
        # Primary: source priority; secondary: exact language match over empty
        lang_match = 0 if (r.language == language or r.language == "") else 99
        lang_exact = 0 if r.language == language else 1
        return (source_priority.get(r.source, 99), lang_match, lang_exact)

    rows_sorted = sorted(rows, key=sort_key)
    return rows_sorted[0].youtube_id if rows_sorted else None


@write_session
def upsert_arr(media_id: int, youtube_id: str, *, _session: Session = None) -> VideoId:  # type: ignore
    """Create or update the Arr-sourced trailer YouTube ID for a media item."""
    existing = _session.exec(
        select(VideoId).where(
            VideoId.media_id == media_id,
            VideoId.source == VideoIdSourceEnum.ARR,
            VideoId.video_type == "trailer",
        )
    ).first()
    now = datetime.now(timezone.utc)
    if existing:
        existing.youtube_id = youtube_id
        existing.updated_at = now
        _session.add(existing)
        _session.commit()
        _session.refresh(existing)
        return existing
    row = VideoId(
        media_id=media_id,
        youtube_id=youtube_id,
        video_type="trailer",
        source=VideoIdSourceEnum.ARR,
        language="",
        season=0,
        created_at=now,
        updated_at=now,
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row


@write_session
def upsert_tmdb(
    media_id: int,
    video_type: str,
    language: str,
    season: int,
    youtube_id: str | None,
    *,
    _session: Session = None,  # type: ignore
) -> VideoId | None:
    """Create or update a TMDB-sourced YouTube ID. Skips if youtube_id is None."""
    if not youtube_id:
        return None
    existing = _session.exec(
        select(VideoId).where(
            VideoId.media_id == media_id,
            VideoId.source == VideoIdSourceEnum.TMDB,
            VideoId.video_type == video_type,
            VideoId.language == language,
            col(VideoId.season) == season,
        )
    ).first()
    now = datetime.now(timezone.utc)
    if existing:
        if existing.youtube_id == youtube_id:
            return existing
        existing.youtube_id = youtube_id
        existing.updated_at = now
        _session.add(existing)
        _session.commit()
        _session.refresh(existing)
        return existing
    row = VideoId(
        media_id=media_id,
        youtube_id=youtube_id,
        video_type=video_type,
        source=VideoIdSourceEnum.TMDB,
        language=language,
        season=season,
        created_at=now,
        updated_at=now,
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row


@write_session
def create_user(
    media_id: int,
    video_type: str,
    language: str,
    youtube_id: str,
    *,
    _session: Session = None,  # type: ignore
) -> VideoIdRead:
    """Create a user-provided YouTube ID record."""
    now = datetime.now(timezone.utc)
    row = VideoId(
        media_id=media_id,
        youtube_id=youtube_id,
        video_type=video_type,
        source=VideoIdSourceEnum.USER,
        language=language,
        season=0,
        created_at=now,
        updated_at=now,
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return _to_read(row)


@write_session
def delete(video_id_id: int, media_id: int, *, _session: Session = None) -> bool:  # type: ignore
    """Delete a user-provided VideoId record. Returns False if not found or not user-sourced."""
    row = _session.exec(
        select(VideoId).where(
            col(VideoId.id) == video_id_id,
            VideoId.media_id == media_id,
            VideoId.source == VideoIdSourceEnum.USER,
        )
    ).first()
    if row is None:
        return False
    _session.delete(row)
    _session.commit()
    return True


@read_session
def get(video_id_id: int, *, _session: Session = None) -> VideoIdRead | None:  # type: ignore
    row = _session.get(VideoId, video_id_id)
    if row is None:
        return None
    return _to_read(row)
