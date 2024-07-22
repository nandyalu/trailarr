from pydantic import BaseModel
from sqlmodel import Session, col, select

from core.base.database.utils.engine import manage_session
from core.radarr.models import Movie
from core.sonarr.models import Series


class ServerStats(BaseModel):
    trailers_downloaded: int
    movies_count: int
    series_count: int
    monitored_count: int


class GeneralDatabaseManager:

    @manage_session
    def get_stats(
        self,
        *,
        _session: Session = None,  # type: ignore
    ) -> ServerStats:
        # Downloaded trailers count
        statement = select(Movie.id).where(col(Movie.downloaded_at).is_not(None))
        _downloaded = len(_session.exec(statement).all())
        statement = select(Series.id).where(col(Series.downloaded_at).is_not(None))
        _downloaded += len(_session.exec(statement).all())

        # Movies count
        statement = select(Movie.id)
        _movies_count = len(_session.exec(statement).all())

        # Series count
        statement = select(Series.id)
        _series_count = len(_session.exec(statement).all())

        # Monitored count
        statement = select(Movie.id).where(col(Movie.monitor).is_(True))
        _monitored_count = len(_session.exec(statement).all())
        statement = select(Series.id).where(col(Series.monitor).is_(True))
        _monitored_count += len(_session.exec(statement).all())

        return ServerStats(
            trailers_downloaded=_downloaded,
            movies_count=_movies_count,
            series_count=_series_count,
            monitored_count=_monitored_count,
        )
