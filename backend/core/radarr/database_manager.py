from backend.core.base.database.manager.base import DatabaseHandler
from backend.core.radarr.models import Movie, MovieCreate, MovieRead, MovieUpdate


class MovieDatabaseHandler(DatabaseHandler[Movie, MovieCreate, MovieRead, MovieUpdate]):
    """CRUD operations for movie database table."""

    def __init__(self):
        super().__init__(db_model=Movie, read_model=MovieRead)
