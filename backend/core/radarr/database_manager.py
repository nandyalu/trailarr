from sqlmodel import select
from backend.core.base.database.manager.base import DatabaseHandler
from backend.core.radarr.models import Movie, MovieCreate, MovieRead, MovieUpdate


class MovieDatabaseHandler(DatabaseHandler[Movie, MovieCreate, MovieRead, MovieUpdate]):
    """CRUD operations for movie database table."""

    def __init__(self):
        super().__init__(db_model=Movie, read_model=MovieRead)

    def _get_txdb_statement(self, txdb_id: str):
        return select(Movie).where(Movie.tmdb_id == txdb_id)

    def _get_read_by_id_statement(self, connection_id: int, media_id: int):
        return (
            select(Movie)
            .where(Movie.connection_id == connection_id)
            .where(Movie.radarr_id == media_id)
        )
