from pydantic import BaseModel
from sqlmodel import Session, col, select

from db.models.media import Media
from db.engine import read_session


class ServerStats(BaseModel):
    trailers_downloaded: int
    trailers_detected: int
    movies_count: int
    movies_monitored: int
    series_count: int
    series_monitored: int


@read_session
def get_stats(
    *,
    _session: Session = None,  # type: ignore
) -> ServerStats:
    downloaded = len(
        _session.exec(select(Media.id).where(col(Media.downloaded_at).is_not(None))).all()
    )
    movies_count = len(
        _session.exec(select(Media.id).where(col(Media.is_movie).is_(True))).all()
    )
    movies_monitored = len(
        _session.exec(
            select(Media.id).where(col(Media.is_movie).is_(True), col(Media.monitor).is_(True))
        ).all()
    )
    series_count = len(
        _session.exec(select(Media.id).where(col(Media.is_movie).is_(False))).all()
    )
    series_monitored = len(
        _session.exec(
            select(Media.id).where(col(Media.is_movie).is_(False), col(Media.monitor).is_(True))
        ).all()
    )
    return ServerStats(
        trailers_downloaded=downloaded,
        trailers_detected=downloaded,
        movies_count=movies_count,
        movies_monitored=movies_monitored,
        series_count=series_count,
        series_monitored=series_monitored,
    )
