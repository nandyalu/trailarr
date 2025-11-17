from pydantic import BaseModel
from sqlmodel import Session, col, select

from core.base.database.models.media import Media
from core.base.database.utils.engine import manage_session


class ServerStats(BaseModel):
    trailers_downloaded: int
    trailers_detected: int
    movies_count: int
    movies_monitored: int
    series_count: int
    series_monitored: int


@manage_session
def get_stats(
    *,
    _session: Session = None,  # type: ignore
) -> ServerStats:
    # Downloaded trailers count
    statement = select(Media.id).where(col(Media.downloaded_at).is_not(None))
    _downloaded = len(_session.exec(statement).all())

    # Detected trailers count
    statement = select(Media.id).where(col(Media.trailer_exists).is_(True))
    _detected = len(_session.exec(statement).all())

    # Movies Total
    movies_statement = select(Media.id).where(col(Media.is_movie).is_(True))
    _movies_count = len(_session.exec(movies_statement).all())

    # Movies Monitored
    statement = movies_statement.where(col(Media.monitor).is_(True))
    _movies_monitored_count = len(_session.exec(statement).all())

    # Series Total
    series_statement = select(Media.id).where(col(Media.is_movie).is_(False))
    _series_count = len(_session.exec(series_statement).all())

    # Series Monitored
    statement = series_statement.where(col(Media.monitor).is_(True))
    _series_monitored_count = len(_session.exec(statement).all())

    return ServerStats(
        trailers_downloaded=_downloaded,
        trailers_detected=_detected,
        movies_count=_movies_count,
        movies_monitored=_movies_monitored_count,
        series_count=_series_count,
        series_monitored=_series_monitored_count,
    )
